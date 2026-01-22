"""
AWS API Gateway Integration Module

This module provides utilities for integrating FastAPI with AWS API Gateway and Lambda.
Supports both REST API and HTTP API gateway types.

Features:
- Event transformation utilities
- Response formatting for API Gateway
- Custom error handling
- CORS configuration helpers
- Authentication utilities
"""

import json
import logging
from typing import Dict, Any, Optional, Callable, Coroutine
from datetime import datetime

logger = logging.getLogger(__name__)


class APIGatewayEvent:
    """Parse and validate AWS API Gateway event."""
    
    def __init__(self, event: Dict[str, Any]):
        """
        Initialize with API Gateway event.
        
        Args:
            event: Raw API Gateway event from Lambda
        """
        self.event = event
        self.is_http_api = "requestContext" in event and "http" in event["requestContext"]
        self.is_rest_api = "requestContext" in event and "httpMethod" in event
    
    @property
    def method(self) -> str:
        """Get HTTP method."""
        if self.is_http_api:
            return self.event["requestContext"]["http"]["method"]
        return self.event.get("httpMethod", "GET")
    
    @property
    def path(self) -> str:
        """Get request path."""
        if self.is_http_api:
            return self.event["requestContext"]["http"]["path"]
        return self.event.get("path", "/")
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers."""
        return self.event.get("headers", {})
    
    @property
    def query_params(self) -> Dict[str, str]:
        """Get query parameters."""
        if self.is_http_api:
            raw_qs = self.event.get("rawQueryString", "")
            if not raw_qs:
                return {}
            return {k: v for k, v in [param.split("=") for param in raw_qs.split("&") if "=" in param]}
        return self.event.get("queryStringParameters") or {}
    
    @property
    def body(self) -> Optional[str]:
        """Get request body."""
        body = self.event.get("body")
        if self.event.get("isBase64Encoded"):
            import base64
            return base64.b64decode(body).decode("utf-8") if body else None
        return body
    
    @property
    def source_ip(self) -> str:
        """Get client IP address."""
        if self.is_http_api:
            return self.event["requestContext"]["http"].get("sourceIp", "0.0.0.0")
        return self.event.get("requestContext", {}).get("identity", {}).get("sourceIp", "0.0.0.0")
    
    @property
    def request_id(self) -> str:
        """Get unique request ID."""
        if self.is_http_api:
            return self.event["requestContext"].get("requestId", "unknown")
        return self.event.get("requestContext", {}).get("requestId", "unknown")


class APIGatewayResponse:
    """Format response for API Gateway."""
    
    @staticmethod
    def success(
        status_code: int = 200,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        is_base64_encoded: bool = False
    ) -> Dict[str, Any]:
        """
        Create successful API Gateway response.
        
        Args:
            status_code: HTTP status code (default 200)
            body: Response body as dict (will be JSON serialized)
            headers: HTTP response headers
            is_base64_encoded: Whether body is base64 encoded
        
        Returns:
            API Gateway formatted response
        """
        default_headers = {"Content-Type": "application/json"}
        if headers:
            default_headers.update(headers)
        
        response = {
            "statusCode": status_code,
            "headers": default_headers,
            "isBase64Encoded": is_base64_encoded,
        }
        
        if body is not None:
            response["body"] = json.dumps(body) if isinstance(body, dict) else str(body)
        
        return response
    
    @staticmethod
    def error(
        status_code: int = 500,
        message: str = "Internal Server Error",
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create error API Gateway response.
        
        Args:
            status_code: HTTP status code
            message: Error message
            error_code: Optional error code for client
            details: Optional error details (logged server-side)
            headers: HTTP response headers
        
        Returns:
            API Gateway formatted error response
        """
        error_body = {
            "error": message,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if error_code:
            error_body["error_code"] = error_code
        
        if details and isinstance(details, dict):
            logger.error(f"Request error details: {details}")
        
        return APIGatewayResponse.success(
            status_code=status_code,
            body=error_body,
            headers=headers or {}
        )


class CORSHelper:
    """Helper for configuring CORS for API Gateway."""
    
    @staticmethod
    def get_cors_headers(
        allow_origins: Optional[list] = None,
        allow_methods: Optional[list] = None,
        allow_headers: Optional[list] = None,
        allow_credentials: bool = True,
        max_age: int = 3600
    ) -> Dict[str, str]:
        """
        Get CORS headers for API Gateway response.
        
        Args:
            allow_origins: List of allowed origins (default: *)
            allow_methods: List of allowed methods (default: GET, POST, PUT, DELETE, OPTIONS)
            allow_headers: List of allowed headers
            allow_credentials: Whether to allow credentials
            max_age: Cache duration in seconds
        
        Returns:
            Dictionary of CORS headers
        """
        headers = {
            "Access-Control-Allow-Origin": ", ".join(allow_origins) if allow_origins else "*",
            "Access-Control-Allow-Methods": ", ".join(allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]),
            "Access-Control-Max-Age": str(max_age),
        }
        
        if allow_headers:
            headers["Access-Control-Allow-Headers"] = ", ".join(allow_headers)
        
        if allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        
        return headers


class AuthenticationHelper:
    """Helper for API Gateway authentication."""
    
    @staticmethod
    def get_authorization_token(headers: Dict[str, str]) -> Optional[str]:
        """
        Extract authorization token from headers.
        
        Args:
            headers: Request headers
        
        Returns:
            Bearer token or None
        """
        auth_header = headers.get("Authorization") or headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None
    
    @staticmethod
    def is_authorized(headers: Dict[str, str], expected_token: Optional[str] = None) -> bool:
        """
        Check if request is authorized.
        
        Args:
            headers: Request headers
            expected_token: Token to validate against (if provided)
        
        Returns:
            True if authorized, False otherwise
        """
        token = AuthenticationHelper.get_authorization_token(headers)
        if expected_token:
            return token == expected_token
        return token is not None


class RequestLogger:
    """Log API Gateway requests and responses."""
    
    @staticmethod
    def log_request(event: APIGatewayEvent):
        """Log incoming API Gateway request."""
        logger.info(
            f"Incoming request",
            extra={
                "method": event.method,
                "path": event.path,
                "source_ip": event.source_ip,
                "request_id": event.request_id,
                "headers": dict(event.headers),
            }
        )
    
    @staticmethod
    def log_response(request_id: str, status_code: int, response_time_ms: float):
        """Log outgoing API Gateway response."""
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
            }
        )


# Middleware-like decorator for API Gateway events
def api_gateway_handler(func: Callable) -> Callable:
    """
    Decorator for Lambda handlers that work with API Gateway events.
    
    Provides automatic event parsing, CORS handling, and error handling.
    
    Example:
        @api_gateway_handler
        async def my_handler(event, context):
            parsed_event = APIGatewayEvent(event)
            # ... process request
            return APIGatewayResponse.success(body={"result": "success"})
    """
    async def wrapper(event: Dict[str, Any], context: Any):
        try:
            start_time = datetime.utcnow()
            
            # Parse API Gateway event
            parsed_event = APIGatewayEvent(event)
            RequestLogger.log_request(parsed_event)
            
            # Call handler function
            response = await func(event, context)
            
            # Log response
            elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000
            RequestLogger.log_response(parsed_event.request_id, response.get("statusCode", 200), elapsed)
            
            return response
        except Exception as e:
            logger.exception("Unhandled exception in handler")
            return APIGatewayResponse.error(
                status_code=500,
                message="Internal server error",
                error_code="INTERNAL_ERROR",
                details={"exception": str(e)}
            )
    
    return wrapper


if __name__ == "__main__":
    # Example usage
    sample_event = {
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/api/test",
                "sourceIp": "192.168.1.1"
            },
            "requestId": "abc-123"
        },
        "headers": {"Authorization": "Bearer token123"},
        "rawQueryString": "page=1&limit=10"
    }
    
    parsed = APIGatewayEvent(sample_event)
    print(f"Method: {parsed.method}")
    print(f"Path: {parsed.path}")
    print(f"Query: {parsed.query_params}")
    print(f"Token: {AuthenticationHelper.get_authorization_token(parsed.headers)}")
    
    response = APIGatewayResponse.success(body={"message": "Hello from Lambda!"})
    print(f"Response: {json.dumps(response, indent=2)}")
