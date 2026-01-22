"""
Unit tests for AWS Gateway integration utilities.

Tests all utility classes and functions for AWS API Gateway integration.
"""

import pytest
import json
from src.aws_gateway_integration import (
    APIGatewayEvent,
    APIGatewayResponse,
    CORSHelper,
    AuthenticationHelper,
    RequestLogger
)


class TestAPIGatewayEvent:
    """Test suite for APIGatewayEvent class"""
    
    def test_init_rest_api_format(self, sample_rest_api_event):
        """
        Test: Initialize with REST API event
        Expected: is_rest_api is True, is_http_api is False
        """
        event = APIGatewayEvent(sample_rest_api_event)
        
        assert event.is_rest_api is True
        assert event.is_http_api is False
    
    def test_init_http_api_format(self, sample_http_api_event):
        """
        Test: Initialize with HTTP API event
        Expected: is_http_api is True, is_rest_api is False
        """
        event = APIGatewayEvent(sample_http_api_event)
        
        assert event.is_http_api is True
        assert event.is_rest_api is False
    
    def test_method_rest_api(self, sample_rest_api_event):
        """
        Test: Get HTTP method from REST API event
        Expected: Returns correct method
        """
        event = APIGatewayEvent(sample_rest_api_event)
        
        assert event.method == "GET"
    
    def test_method_http_api(self, sample_http_api_event):
        """
        Test: Get HTTP method from HTTP API event
        Expected: Returns correct method
        """
        event = APIGatewayEvent(sample_http_api_event)
        
        assert event.method == "GET"
    
    def test_method_post(self):
        """
        Test: Get POST method from event
        Expected: Returns "POST"
        """
        event_data = {
            "httpMethod": "POST",
            "requestContext": {"requestId": "123"}
        }
        event = APIGatewayEvent(event_data)
        
        assert event.method == "POST"
    
    def test_path_rest_api(self, sample_rest_api_event):
        """
        Test: Get path from REST API event
        Expected: Returns correct path
        """
        event = APIGatewayEvent(sample_rest_api_event)
        
        assert event.path == "/api/items"
    
    def test_path_http_api(self, sample_http_api_event):
        """
        Test: Get path from HTTP API event
        Expected: Returns correct path
        """
        event = APIGatewayEvent(sample_http_api_event)
        
        assert event.path == "/api/items"
    
    def test_headers_rest_api(self, sample_rest_api_event):
        """
        Test: Get headers from REST API event
        Expected: Returns headers dictionary
        """
        event = APIGatewayEvent(sample_rest_api_event)
        headers = event.headers
        
        assert "Host" in headers
        assert headers["Host"] == "api.example.com"
        assert "Authorization" in headers
    
    def test_headers_empty(self):
        """
        Test: Get headers when none provided
        Expected: Returns empty dictionary
        """
        event_data = {
            "httpMethod": "GET",
            "requestContext": {"requestId": "123"}
        }
        event = APIGatewayEvent(event_data)
        
        assert event.headers == {}
    
    def test_query_params_rest_api(self, sample_rest_api_event):
        """
        Test: Get query parameters from REST API event
        Expected: Returns query parameters dictionary
        """
        event = APIGatewayEvent(sample_rest_api_event)
        params = event.query_params
        
        assert params["page"] == "1"
        assert params["limit"] == "10"
    
    def test_query_params_http_api(self, sample_http_api_event):
        """
        Test: Get query parameters from HTTP API event
        Expected: Parses rawQueryString
        """
        event = APIGatewayEvent(sample_http_api_event)
        params = event.query_params
        
        assert params["page"] == "1"
        assert params["limit"] == "10"
    
    def test_query_params_none(self):
        """
        Test: Get query parameters when none provided
        Expected: Returns empty dictionary
        """
        event_data = {
            "httpMethod": "GET",
            "queryStringParameters": None,
            "requestContext": {"requestId": "123"}
        }
        event = APIGatewayEvent(event_data)
        
        assert event.query_params == {}
    
    def test_body_plain_text(self):
        """
        Test: Get body as plain text
        Expected: Returns body string
        """
        body_content = '{"key": "value"}'
        event_data = {
            "httpMethod": "POST",
            "body": body_content,
            "isBase64Encoded": False,
            "requestContext": {"requestId": "123"}
        }
        event = APIGatewayEvent(event_data)
        
        assert event.body == body_content
    
    def test_body_base64_encoded(self):
        """
        Test: Get body when base64 encoded
        Expected: Decodes body
        """
        import base64
        original = '{"key": "value"}'
        encoded = base64.b64encode(original.encode()).decode()
        
        event_data = {
            "httpMethod": "POST",
            "body": encoded,
            "isBase64Encoded": True,
            "requestContext": {"requestId": "123"}
        }
        event = APIGatewayEvent(event_data)
        
        assert event.body == original
    
    def test_body_none(self):
        """
        Test: Get body when not provided
        Expected: Returns None
        """
        event_data = {
            "httpMethod": "GET",
            "body": None,
            "requestContext": {"requestId": "123"}
        }
        event = APIGatewayEvent(event_data)
        
        assert event.body is None
    
    def test_source_ip_rest_api(self, sample_rest_api_event):
        """
        Test: Get source IP from REST API event
        Expected: Returns correct IP address
        """
        event = APIGatewayEvent(sample_rest_api_event)
        
        assert event.source_ip == "192.168.1.100"
    
    def test_source_ip_http_api(self, sample_http_api_event):
        """
        Test: Get source IP from HTTP API event
        Expected: Returns correct IP address
        """
        event = APIGatewayEvent(sample_http_api_event)
        
        assert event.source_ip == "192.168.1.100"
    
    def test_source_ip_default(self):
        """
        Test: Get source IP when not provided
        Expected: Returns default "0.0.0.0"
        """
        event_data = {
            "httpMethod": "GET",
            "requestContext": {"requestId": "123"}
        }
        event = APIGatewayEvent(event_data)
        
        assert event.source_ip == "0.0.0.0"
    
    def test_request_id_rest_api(self, sample_rest_api_event):
        """
        Test: Get request ID from REST API event
        Expected: Returns correct request ID
        """
        event = APIGatewayEvent(sample_rest_api_event)
        
        assert event.request_id == "c6af9ac6-7b61-11e6-9a41-93e8deadbeef"
    
    def test_request_id_http_api(self, sample_http_api_event):
        """
        Test: Get request ID from HTTP API event
        Expected: Returns correct request ID
        """
        event = APIGatewayEvent(sample_http_api_event)
        
        assert event.request_id == "id="
    
    def test_request_id_default(self):
        """
        Test: Get request ID when not provided
        Expected: Returns default "unknown"
        """
        event_data = {
            "httpMethod": "GET",
            "requestContext": {}
        }
        event = APIGatewayEvent(event_data)
        
        assert event.request_id == "unknown"


class TestAPIGatewayResponse:
    """Test suite for APIGatewayResponse class"""
    
    def test_success_basic(self):
        """
        Test: Create basic success response
        Expected: Returns properly formatted response
        """
        response = APIGatewayResponse.success()
        
        assert response["statusCode"] == 200
        assert "headers" in response
        assert "body" not in response or response["body"] is None
        assert response["isBase64Encoded"] is False
    
    def test_success_with_status_code(self):
        """
        Test: Create success response with custom status code
        Expected: Uses provided status code
        """
        response = APIGatewayResponse.success(status_code=201)
        
        assert response["statusCode"] == 201
    
    def test_success_with_body(self):
        """
        Test: Create success response with body
        Expected: Body is JSON serialized
        """
        body = {"message": "success", "data": [1, 2, 3]}
        response = APIGatewayResponse.success(body=body)
        
        assert response["statusCode"] == 200
        assert json.loads(response["body"]) == body
    
    def test_success_with_headers(self):
        """
        Test: Create success response with custom headers
        Expected: Headers are included
        """
        headers = {"X-Custom-Header": "value"}
        response = APIGatewayResponse.success(headers=headers)
        
        assert response["headers"]["X-Custom-Header"] == "value"
    
    def test_success_content_type_default(self):
        """
        Test: Success response includes default Content-Type
        Expected: Content-Type is application/json
        """
        response = APIGatewayResponse.success()
        
        assert response["headers"]["Content-Type"] == "application/json"
    
    def test_success_204_no_content(self):
        """
        Test: Create 204 No Content response
        Expected: Status code is 204, no body
        """
        response = APIGatewayResponse.success(status_code=204)
        
        assert response["statusCode"] == 204
    
    def test_error_basic(self):
        """
        Test: Create basic error response
        Expected: Returns properly formatted error
        """
        response = APIGatewayResponse.error()
        
        assert response["statusCode"] == 500
        assert "body" in response
        body = json.loads(response["body"])
        assert body["error"] == "Internal Server Error"
    
    def test_error_with_status_code(self):
        """
        Test: Create error response with custom status code
        Expected: Uses provided status code
        """
        response = APIGatewayResponse.error(status_code=404)
        
        assert response["statusCode"] == 404
    
    def test_error_with_message(self):
        """
        Test: Create error response with custom message
        Expected: Message is in response body
        """
        response = APIGatewayResponse.error(message="Custom error")
        
        body = json.loads(response["body"])
        assert body["error"] == "Custom error"
    
    def test_error_with_error_code(self):
        """
        Test: Create error response with error code
        Expected: error_code is in response body
        """
        response = APIGatewayResponse.error(
            status_code=404,
            message="Not found",
            error_code="NOT_FOUND"
        )
        
        body = json.loads(response["body"])
        assert body["error_code"] == "NOT_FOUND"
    
    def test_error_with_details(self):
        """
        Test: Create error response with details
        Expected: Details are logged (not in response)
        """
        details = {"field": "email", "reason": "invalid"}
        response = APIGatewayResponse.error(
            message="Validation error",
            details=details
        )
        
        assert response["statusCode"] == 500
        # Details should not be in the response body (for security)
        body = json.loads(response["body"])
        assert "details" not in body
    
    def test_error_has_timestamp(self):
        """
        Test: Error response includes timestamp
        Expected: timestamp field present in body
        """
        response = APIGatewayResponse.error()
        
        body = json.loads(response["body"])
        assert "timestamp" in body


class TestCORSHelper:
    """Test suite for CORSHelper class"""
    
    def test_cors_headers_default(self):
        """
        Test: Get CORS headers with defaults
        Expected: Returns default CORS configuration
        """
        headers = CORSHelper.get_cors_headers()
        
        assert headers["Access-Control-Allow-Origin"] == "*"
        assert "GET" in headers["Access-Control-Allow-Methods"]
        assert "POST" in headers["Access-Control-Allow-Methods"]
        assert headers["Access-Control-Allow-Credentials"] == "true"
    
    def test_cors_headers_specific_origins(self):
        """
        Test: Get CORS headers with specific origins
        Expected: Origins are specified
        """
        origins = ["https://example.com", "https://app.example.com"]
        headers = CORSHelper.get_cors_headers(allow_origins=origins)
        
        assert "https://example.com" in headers["Access-Control-Allow-Origin"]
        assert "https://app.example.com" in headers["Access-Control-Allow-Origin"]
    
    def test_cors_headers_custom_methods(self):
        """
        Test: Get CORS headers with custom methods
        Expected: Methods are specified
        """
        methods = ["GET", "POST", "PUT"]
        headers = CORSHelper.get_cors_headers(allow_methods=methods)
        
        assert headers["Access-Control-Allow-Methods"] == "GET, POST, PUT"
    
    def test_cors_headers_custom_headers(self):
        """
        Test: Get CORS headers with custom allowed headers
        Expected: Headers are specified
        """
        allowed_headers = ["Content-Type", "Authorization", "X-API-Key"]
        headers = CORSHelper.get_cors_headers(allow_headers=allowed_headers)
        
        assert "Access-Control-Allow-Headers" in headers
        assert "Content-Type" in headers["Access-Control-Allow-Headers"]
        assert "Authorization" in headers["Access-Control-Allow-Headers"]
    
    def test_cors_headers_no_credentials(self):
        """
        Test: Get CORS headers without credentials
        Expected: Credentials not allowed
        """
        headers = CORSHelper.get_cors_headers(allow_credentials=False)
        
        # If credentials false, header might not be present or be false
        if "Access-Control-Allow-Credentials" in headers:
            assert headers["Access-Control-Allow-Credentials"] == "false"
    
    def test_cors_headers_custom_max_age(self):
        """
        Test: Get CORS headers with custom max age
        Expected: Max age is specified
        """
        headers = CORSHelper.get_cors_headers(max_age=86400)
        
        assert headers["Access-Control-Max-Age"] == "86400"


class TestAuthenticationHelper:
    """Test suite for AuthenticationHelper class"""
    
    def test_get_token_valid(self, api_key_header):
        """
        Test: Extract token from valid header
        Expected: Returns token without "Bearer " prefix
        """
        token = AuthenticationHelper.get_authorization_token(api_key_header)
        
        assert token == "secret-api-key-123"
    
    def test_get_token_missing(self):
        """
        Test: Extract token when header missing
        Expected: Returns None
        """
        headers = {"Content-Type": "application/json"}
        token = AuthenticationHelper.get_authorization_token(headers)
        
        assert token is None
    
    def test_get_token_case_insensitive(self):
        """
        Test: Extract token with lowercase Authorization header
        Expected: Returns token
        """
        headers = {"authorization": "Bearer token123"}
        token = AuthenticationHelper.get_authorization_token(headers)
        
        assert token == "token123"
    
    def test_get_token_invalid_format(self):
        """
        Test: Extract token with invalid format (no Bearer)
        Expected: Returns None
        """
        headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        token = AuthenticationHelper.get_authorization_token(headers)
        
        assert token is None
    
    def test_is_authorized_with_token_present(self, api_key_header):
        """
        Test: Check authorization when token present
        Expected: Returns True
        """
        is_auth = AuthenticationHelper.is_authorized(api_key_header)
        
        assert is_auth is True
    
    def test_is_authorized_no_token(self):
        """
        Test: Check authorization when no token
        Expected: Returns False
        """
        headers = {}
        is_auth = AuthenticationHelper.is_authorized(headers)
        
        assert is_auth is False
    
    def test_is_authorized_token_matches(self, api_key_header):
        """
        Test: Check authorization when token matches expected
        Expected: Returns True
        """
        is_auth = AuthenticationHelper.is_authorized(
            api_key_header,
            expected_token="secret-api-key-123"
        )
        
        assert is_auth is True
    
    def test_is_authorized_token_mismatch(self, api_key_header):
        """
        Test: Check authorization when token doesn't match
        Expected: Returns False
        """
        is_auth = AuthenticationHelper.is_authorized(
            api_key_header,
            expected_token="wrong-token"
        )
        
        assert is_auth is False


class TestRequestLogger:
    """Test suite for RequestLogger class"""
    
    def test_log_request(self, sample_rest_api_event, caplog):
        """
        Test: Log incoming request
        Expected: Request details are logged
        """
        import logging
        caplog.set_level(logging.INFO)
        
        event = APIGatewayEvent(sample_rest_api_event)
        RequestLogger.log_request(event)
        
        # Check that something was logged
        assert len(caplog.records) > 0
    
    def test_log_response(self, caplog):
        """
        Test: Log response details
        Expected: Response details are logged
        """
        import logging
        caplog.set_level(logging.INFO)
        
        RequestLogger.log_response(
            request_id="req-123",
            status_code=200,
            response_time_ms=45.5
        )
        
        # Check that something was logged
        assert len(caplog.records) > 0


class TestIntegrationScenarios:
    """Test suite for integration scenarios"""
    
    def test_parse_and_format_response(self, sample_rest_api_event):
        """
        Test: Parse event and create response
        Expected: Event parsed and response formatted correctly
        """
        # Parse incoming event
        event = APIGatewayEvent(sample_rest_api_event)
        
        assert event.method == "GET"
        assert event.path == "/api/items"
        
        # Create response
        response = APIGatewayResponse.success(
            body={"items": []}
        )
        
        assert response["statusCode"] == 200
        assert "body" in response
    
    def test_auth_and_cors_handling(self, sample_rest_api_event):
        """
        Test: Check auth and add CORS headers
        Expected: Both operations succeed
        """
        event = APIGatewayEvent(sample_rest_api_event)
        
        # Check authentication
        token = AuthenticationHelper.get_authorization_token(event.headers)
        assert token is not None
        
        # Add CORS headers
        cors_headers = CORSHelper.get_cors_headers(
            allow_origins=["https://example.com"]
        )
        
        # Create response
        response = APIGatewayResponse.success(headers=cors_headers)
        
        assert "Access-Control-Allow-Origin" in response["headers"]
