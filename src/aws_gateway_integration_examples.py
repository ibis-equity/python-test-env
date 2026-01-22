"""
AWS API Gateway and Lambda Integration Examples

This file contains practical examples for using FastAPI with AWS Lambda
and API Gateway integration utilities.
"""

# Example 1: Basic API Gateway Event Handling
# ============================================

from aws_gateway_integration import APIGatewayEvent, APIGatewayResponse
import json


def example_1_parse_event():
    """Example: Parse API Gateway event and extract information."""
    
    # Mock API Gateway event
    event = {
        "resource": "/api/items/{id}",
        "path": "/api/items/42",
        "httpMethod": "GET",
        "headers": {
            "Host": "example.com",
            "Authorization": "Bearer token123",
            "Content-Type": "application/json"
        },
        "queryStringParameters": {
            "limit": "10",
            "offset": "0"
        },
        "body": None,
        "requestContext": {
            "httpMethod": "GET",
            "path": "/api/items/42",
            "identity": {
                "sourceIp": "203.0.113.1"
            },
            "requestId": "req-abc123"
        }
    }
    
    # Parse the event
    parsed = APIGatewayEvent(event)
    
    print("Method:", parsed.method)  # GET
    print("Path:", parsed.path)  # /api/items/42
    print("Headers:", parsed.headers)
    print("Query params:", parsed.query_params)
    print("Source IP:", parsed.source_ip)
    print("Request ID:", parsed.request_id)


# Example 2: Create Response with Proper Format
# ============================================

def example_2_format_response():
    """Example: Create response in API Gateway format."""
    
    # Success response
    response = APIGatewayResponse.success(
        status_code=200,
        body={
            "id": 42,
            "name": "Item 42",
            "description": "Example item",
            "status": "active"
        }
    )
    
    print("Response structure:")
    print(json.dumps(response, indent=2))
    
    # Error response
    error_response = APIGatewayResponse.error(
        status_code=404,
        message="Item not found",
        error_code="ITEM_NOT_FOUND",
        details={"item_id": 42}
    )
    
    print("\nError response:")
    print(json.dumps(error_response, indent=2))


# Example 3: CORS Configuration
# ============================

def example_3_cors():
    """Example: Configure CORS for API Gateway."""
    
    from aws_gateway_integration import CORSHelper
    
    # Configure CORS for specific origins
    cors_headers = CORSHelper.get_cors_headers(
        allow_origins=[
            "https://app.example.com",
            "https://admin.example.com"
        ],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-API-Key"
        ],
        allow_credentials=True,
        max_age=86400  # 1 day
    )
    
    # Use in response
    response = APIGatewayResponse.success(
        body={"message": "CORS enabled"},
        headers=cors_headers
    )
    
    print("Response with CORS headers:")
    print(json.dumps(response, indent=2))


# Example 4: Authentication
# =========================

def example_4_authentication():
    """Example: Validate authentication tokens."""
    
    from aws_gateway_integration import AuthenticationHelper
    
    # Example 1: Extract token
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    
    token = AuthenticationHelper.get_authorization_token(headers)
    print("Extracted token:", token)
    
    # Example 2: Validate token
    api_key = "secret-api-key-123"
    
    request_headers = {
        "Authorization": "Bearer secret-api-key-123"
    }
    
    is_valid = AuthenticationHelper.is_authorized(
        request_headers,
        expected_token=api_key
    )
    
    print("Token is valid:", is_valid)
    
    # Use in Lambda handler
    if not is_valid:
        return APIGatewayResponse.error(
            status_code=401,
            message="Unauthorized",
            error_code="INVALID_TOKEN"
        )


# Example 5: Custom Lambda Handler
# ================================

def example_5_custom_handler():
    """Example: Custom Lambda handler using API Gateway utilities."""
    
    async def my_handler(event, context):
        """Custom handler that uses AWS Gateway integration utilities."""
        
        # Parse event
        parsed_event = APIGatewayEvent(event)
        
        # Log request
        print(f"Request: {parsed_event.method} {parsed_event.path}")
        print(f"From: {parsed_event.source_ip}")
        
        # Check authentication
        token = AuthenticationHelper.get_authorization_token(parsed_event.headers)
        if not token:
            return APIGatewayResponse.error(
                status_code=401,
                message="Missing authentication token"
            )
        
        # Process request
        if parsed_event.path == "/api/items" and parsed_event.method == "GET":
            items = [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"}
            ]
            return APIGatewayResponse.success(
                body={"items": items},
                headers=CORSHelper.get_cors_headers()
            )
        
        # Default 404
        return APIGatewayResponse.error(
            status_code=404,
            message="Endpoint not found"
        )


# Example 6: Structured Logging
# =============================

def example_6_logging():
    """Example: Use RequestLogger for CloudWatch."""
    
    from aws_gateway_integration import RequestLogger
    import time
    
    # Mock event
    event = {
        "path": "/api/items",
        "httpMethod": "POST",
        "headers": {"Host": "api.example.com"},
        "requestContext": {
            "requestId": "req-123",
            "identity": {"sourceIp": "192.168.1.1"}
        }
    }
    
    parsed_event = APIGatewayEvent(event)
    
    # Log incoming request
    RequestLogger.log_request(parsed_event)
    
    # Simulate processing
    start_time = time.time()
    # ... do work ...
    response_time = (time.time() - start_time) * 1000
    
    # Log response
    RequestLogger.log_response(
        request_id=parsed_event.request_id,
        status_code=200,
        response_time_ms=response_time
    )


# Example 7: REST API Patterns
# ============================

def example_7_rest_patterns():
    """Example: Common REST API patterns with FastAPI + Lambda."""
    
    # Example event for different HTTP methods
    
    # GET - Retrieve resource
    get_event = {
        "path": "/api/items/42",
        "httpMethod": "GET",
        "queryStringParameters": {"expand": "true"},
        "requestContext": {"requestId": "req-1"}
    }
    
    # POST - Create resource
    post_event = {
        "path": "/api/items",
        "httpMethod": "POST",
        "body": '{"name": "New Item", "description": "..."}',
        "headers": {"Content-Type": "application/json"},
        "requestContext": {"requestId": "req-2"}
    }
    
    # PUT - Update resource
    put_event = {
        "path": "/api/items/42",
        "httpMethod": "PUT",
        "body": '{"name": "Updated Name"}',
        "requestContext": {"requestId": "req-3"}
    }
    
    # DELETE - Remove resource
    delete_event = {
        "path": "/api/items/42",
        "httpMethod": "DELETE",
        "requestContext": {"requestId": "req-4"}
    }
    
    # Handler routing
    def handle_request(event):
        parsed = APIGatewayEvent(event)
        
        if parsed.method == "GET":
            return APIGatewayResponse.success(
                body={"id": 42, "name": "Item 42"}
            )
        elif parsed.method == "POST":
            body = json.loads(parsed.body) if parsed.body else {}
            return APIGatewayResponse.success(
                status_code=201,
                body={"id": 43, **body}
            )
        elif parsed.method == "PUT":
            return APIGatewayResponse.success(
                body={"id": 42, "name": "Updated"}
            )
        elif parsed.method == "DELETE":
            return APIGatewayResponse.success(
                status_code=204,
                body={}
            )


# Example 8: Error Handling
# ==========================

def example_8_error_handling():
    """Example: Comprehensive error handling patterns."""
    
    # Example handler with error handling
    def safe_handler(event, context):
        try:
            parsed_event = APIGatewayEvent(event)
            
            # Simulate processing
            if not parsed_event.path:
                raise ValueError("Invalid path")
            
            # Success
            return APIGatewayResponse.success(
                body={"status": "success"}
            )
        
        except ValueError as e:
            # Validation error (400)
            return APIGatewayResponse.error(
                status_code=400,
                message="Invalid request",
                error_code="VALIDATION_ERROR",
                details={"error": str(e)}
            )
        
        except KeyError as e:
            # Not found error (404)
            return APIGatewayResponse.error(
                status_code=404,
                message="Resource not found",
                error_code="NOT_FOUND"
            )
        
        except PermissionError as e:
            # Authorization error (403)
            return APIGatewayResponse.error(
                status_code=403,
                message="Forbidden",
                error_code="FORBIDDEN"
            )
        
        except Exception as e:
            # Generic server error (500)
            print(f"Unhandled exception: {e}")
            return APIGatewayResponse.error(
                status_code=500,
                message="Internal server error",
                error_code="INTERNAL_ERROR",
                details={"exception": str(e)}
            )


# Example 9: HTTP API vs REST API
# =============================

def example_9_api_formats():
    """Example: Handle both REST API and HTTP API formats."""
    
    # REST API format (older)
    rest_api_event = {
        "resource": "/items/{id}",
        "path": "/items/42",
        "httpMethod": "GET",
        "headers": {"Host": "example.com"},
        "requestContext": {
            "httpMethod": "GET",
            "identity": {"sourceIp": "192.168.1.1"}
        }
    }
    
    # HTTP API format (newer)
    http_api_event = {
        "routeKey": "GET /items/{id}",
        "rawPath": "/items/42",
        "headers": {"host": "example.com"},
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/items/42",
                "sourceIp": "192.168.1.1"
            }
        }
    }
    
    # APIGatewayEvent handles both automatically
    rest_parsed = APIGatewayEvent(rest_api_event)
    http_parsed = APIGatewayEvent(http_api_event)
    
    print(f"REST API - Method: {rest_parsed.method}, Path: {rest_parsed.path}")
    print(f"HTTP API - Method: {http_parsed.method}, Path: {http_parsed.path}")


# Example 10: Complete Middleware Pattern
# =======================================

def example_10_middleware():
    """Example: Middleware-like pattern for cross-cutting concerns."""
    
    def with_cors(handler):
        """Decorator to add CORS headers to response."""
        def wrapper(event, context):
            response = handler(event, context)
            cors_headers = CORSHelper.get_cors_headers()
            response["headers"].update(cors_headers)
            return response
        return wrapper
    
    def with_auth(handler):
        """Decorator to validate authentication."""
        def wrapper(event, context):
            parsed_event = APIGatewayEvent(event)
            
            if not AuthenticationHelper.get_authorization_token(parsed_event.headers):
                return APIGatewayResponse.error(
                    status_code=401,
                    message="Unauthorized"
                )
            
            return handler(event, context)
        return wrapper
    
    def with_logging(handler):
        """Decorator to log requests and responses."""
        def wrapper(event, context):
            parsed_event = APIGatewayEvent(event)
            RequestLogger.log_request(parsed_event)
            
            import time
            start = time.time()
            response = handler(event, context)
            elapsed = (time.time() - start) * 1000
            
            RequestLogger.log_response(
                parsed_event.request_id,
                response.get("statusCode", 200),
                elapsed
            )
            
            return response
        return wrapper
    
    # Stack decorators
    @with_cors
    @with_auth
    @with_logging
    def my_handler(event, context):
        return APIGatewayResponse.success(
            body={"message": "Fully decorated handler"}
        )


if __name__ == "__main__":
    print("AWS API Gateway Integration Examples")
    print("=" * 50)
    
    print("\nExample 1: Parse API Gateway Event")
    print("-" * 50)
    example_1_parse_event()
    
    print("\n\nExample 2: Format Response")
    print("-" * 50)
    example_2_format_response()
    
    print("\n\nExample 3: CORS Configuration")
    print("-" * 50)
    example_3_cors()
    
    print("\n\nExample 4: Authentication")
    print("-" * 50)
    example_4_authentication()
    
    print("\n\nRun this file with: python aws_gateway_integration_examples.py")
