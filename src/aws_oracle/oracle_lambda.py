"""
AWS Lambda handler for FastAPI + Oracle integration.

Wraps the FastAPI application with Mangum for AWS Lambda/API Gateway integration.
Handles cold starts, environment configuration, and CloudWatch logging.

Usage in AWS Lambda:
  Handler: src.oracle_lambda.handler
  Runtime: Python 3.11
  Timeout: 60 seconds
  Memory: 512 MB (minimum)

Environment variables:
  - ORACLE_HOST: Oracle database host
  - ORACLE_PORT: Oracle database port (default: 1521)
  - ORACLE_SERVICE_NAME: Oracle service name
  - ORACLE_USER: Oracle username
  - ORACLE_PASSWORD: Oracle password
  - ORACLE_POOL_MIN: Min connection pool size (default: 2)
  - ORACLE_POOL_MAX: Max connection pool size (default: 10)
"""

import logging
import json
import sys
from typing import Any, Dict
from functools import lru_cache

# Third-party imports
from mangum import Mangum
import structlog

# Local imports
from .oracle_fastapi import app
from .oracle_integration import get_pool, close_pool, OracleException


# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging() -> None:
    """Configure structured logging for Lambda environment."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO
    )


# Initialize logging once on module load
setup_logging()
logger = structlog.get_logger(__name__)


# ============================================================================
# Lambda Lifecycle Management
# ============================================================================

@lru_cache(maxsize=1)
def get_database_pool():
    """
    Get or initialize the Oracle connection pool.
    
    Cached to reuse across Lambda invocations (warm starts).
    Cold start initializes pool on first invocation.
    
    Returns:
        OracleConnectionPool: Shared connection pool
    """
    logger.info("initializing_oracle_pool")
    pool = get_pool()
    
    # Verify pool is healthy
    health = pool.health_check()
    logger.info("pool_health_check", health=health)
    
    if health['status'] != 'healthy':
        logger.warning("pool_unhealthy", health=health)
    
    return pool


def cleanup_resources() -> None:
    """
    Clean up database connections on Lambda shutdown.
    
    Called when Lambda container is being recycled.
    Safe to call even if pool not initialized.
    """
    try:
        logger.info("closing_oracle_pool")
        close_pool()
        logger.info("oracle_pool_closed")
    except Exception as e:
        logger.error("pool_cleanup_error", error=str(e), exc_info=True)


# ============================================================================
# Lambda Handler
# ============================================================================

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for API Gateway.
    
    Processes HTTP requests from API Gateway and routes to FastAPI.
    
    Args:
        event: API Gateway Lambda proxy integration event
        context: Lambda context object
    
    Returns:
        API Gateway Lambda proxy integration response
    
    Example event structure:
        {
            "resource": "/api/accounts",
            "path": "/api/accounts",
            "httpMethod": "GET",
            "headers": {
                "Host": "api.example.com",
                "User-Agent": "curl/7.68.0",
                "Accept": "*/*",
                "X-User-Id": "john.doe@company.com"
            },
            "multiValueHeaders": {...},
            "queryStringParameters": {"skip": "0", "limit": "50"},
            "body": None,
            "isBase64Encoded": false
        }
    """
    # Log invocation details
    logger.info(
        "lambda_invocation",
        request_id=context.request_id,
        function_name=context.function_name,
        memory_limit_in_mb=context.memory_limit_in_mb,
        remaining_time_in_millis=context.get_remaining_time_in_millis(),
        method=event.get('httpMethod'),
        path=event.get('path'),
        source_ip=event.get('requestContext', {}).get('identity', {}).get('sourceIp')
    )
    
    try:
        # Ensure Oracle pool is initialized
        pool = get_database_pool()
        
        # Verify health on each invocation
        health = pool.health_check()
        logger.info("connection_pool_status", health=health)
        
        # Create Mangum handler with FastAPI app
        asgi_handler = Mangum(app)
        
        # Process request through FastAPI
        response = asgi_handler(event, context)
        
        # Extract status code for logging
        status_code = response.get('statusCode', 500)
        logger.info(
            "lambda_response",
            status_code=status_code,
            request_id=context.request_id
        )
        
        return response
        
    except OracleException as e:
        """Database connection errors."""
        logger.error(
            "oracle_error",
            error=str(e),
            error_type=type(e).__name__,
            request_id=context.request_id,
            exc_info=True
        )
        
        return {
            'statusCode': 503,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Database unavailable',
                'message': 'Oracle connection failed',
                'request_id': context.request_id
            })
        }
    
    except Exception as e:
        """Unexpected errors."""
        logger.error(
            "unexpected_error",
            error=str(e),
            error_type=type(e).__name__,
            request_id=context.request_id,
            exc_info=True
        )
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred',
                'request_id': context.request_id
            })
        }


# ============================================================================
# Mangum Handler Export
# ============================================================================

# Export handler for Lambda
handler = lambda_handler


# ============================================================================
# Cold Start Optimization
# ============================================================================

def initialize_on_import() -> None:
    """
    Perform initialization when module is imported (Lambda container startup).
    
    This runs once when the Lambda function first starts, before any invocations.
    Helps with cold start performance.
    """
    logger.info("lambda_module_loading")
    
    try:
        # Pre-warm the pool if desired
        # Uncomment to initialize pool on container startup
        # get_database_pool()
        
        logger.info("lambda_ready")
    except Exception as e:
        logger.error(
            "initialization_failed",
            error=str(e),
            exc_info=True
        )


# Run initialization on module import
initialize_on_import()


# ============================================================================
# Local Testing
# ============================================================================

if __name__ == '__main__':
    """Local testing without Lambda environment."""
    import os
    
    # Set test environment variables
    os.environ['ORACLE_HOST'] = 'localhost'
    os.environ['ORACLE_PORT'] = '1521'
    os.environ['ORACLE_SERVICE_NAME'] = 'XE'
    os.environ['ORACLE_USER'] = 'test_user'
    os.environ['ORACLE_PASSWORD'] = 'test_password'
    
    # Mock Lambda context
    class MockLambdaContext:
        request_id = "local-test-123"
        function_name = "oracle-api-dev"
        memory_limit_in_mb = 512
        
        def get_remaining_time_in_millis(self) -> int:
            return 60000  # 60 seconds
    
    # Test simple GET request
    test_event = {
        'httpMethod': 'GET',
        'path': '/health',
        'headers': {
            'Host': 'localhost:8000',
            'User-Agent': 'curl/7.68.0'
        },
        'queryStringParameters': None,
        'body': None,
        'isBase64Encoded': False,
        'requestContext': {
            'identity': {'sourceIp': '127.0.0.1'}
        }
    }
    
    context = MockLambdaContext()
    
    logger.info("testing_lambda_handler_locally")
    response = lambda_handler(test_event, context)
    
    print("\n=== Lambda Handler Response ===")
    print(json.dumps(response, indent=2, default=str))
    
    # Cleanup
    cleanup_resources()
