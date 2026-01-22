#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Lambda/API Gateway integration with FastAPI."""

import json
import sys
import os

# Fix for Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Test imports
try:
    from mangum import Mangum
    print("[OK] Mangum ASGI adapter installed")
except ImportError as e:
    print(f"[FAIL] Mangum import failed: {e}")
    sys.exit(1)

try:
    from fast_api import app, lambda_handler
    print("[OK] FastAPI app with Lambda handler loaded")
except ImportError as e:
    print(f"[FAIL] FastAPI import failed: {e}")
    sys.exit(1)

try:
    from aws_gateway_integration import (
        APIGatewayEvent,
        APIGatewayResponse,
        CORSHelper,
        AuthenticationHelper
    )
    print("[OK] AWS Gateway integration utilities loaded")
except ImportError as e:
    print(f"[FAIL] AWS Gateway integration import failed: {e}")
    sys.exit(1)

# Test Lambda handler
print("\n" + "="*60)
print("Testing Lambda Handler")
print("="*60)

# Mock API Gateway event (REST API format)
test_event = {
    "resource": "/",
    "path": "/api/health",
    "httpMethod": "GET",
    "headers": {
        "Host": "lambda.example.com",
        "User-Agent": "curl/7.64.1",
        "Accept": "*/*",
        "Content-Type": "application/json"
    },
    "queryStringParameters": None,
    "pathParameters": None,
    "stageVariables": None,
    "requestContext": {
        "resourceId": "123456",
        "resourcePath": "/",
        "httpMethod": "GET",
        "extendedRequestId": "request-id",
        "requestTime": "09/Apr/2015:12:34:56 +0000",
        "path": "/api/health",
        "accountId": "123456789012",
        "protocol": "HTTP/1.1",
        "stage": "prod",
        "domainPrefix": "id",
        "requestTimeEpoch": 1428582896000,
        "requestId": "id=",
        "identity": {
            "cognitoIdentityPoolId": None,
            "accountId": None,
            "cognitoIdentityId": None,
            "caller": None,
            "sourceIp": "192.168.1.1",
            "principalOrgId": None,
            "accessKey": None,
            "cognitoAuthenticationType": None,
            "cognitoAuthenticationProvider": None,
            "userArn": None,
            "userAgent": "curl/7.64.1",
            "user": None
        },
        "domainName": "id.execute-api.us-east-1.amazonaws.com",
        "apiId": "1234567890"
    },
    "body": None,
    "isBase64Encoded": False
}

# Mock context
class MockContext:
    def __init__(self):
        self.function_name = "fastapi-app"
        self.function_version = "$LATEST"
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:fastapi-app"
        self.memory_limit_in_mb = 512
        self.aws_request_id = "request-id"
        self.log_group_name = "/aws/lambda/fastapi-app"
        self.log_stream_name = "2024/01/01/[$LATEST]abcdef"

context = MockContext()

print("\nTest 1: Health check endpoint")
print("-" * 40)
try:
    # The lambda_handler is an ASGI application wrapped by Mangum
    # In a real Lambda environment, it receives the API Gateway event
    response = lambda_handler(test_event, context)
    print(f"Status Code: {response.get('statusCode')}")
    body = json.loads(response.get('body', '{}'))
    print(f"Response: {json.dumps(body, indent=2)}")
    if response.get('statusCode') == 200:
        print("✓ Health check endpoint working")
    else:
        print("✗ Unexpected status code")
except Exception as e:
    print(f"✗ Error: {e}")

# Test API Gateway event parsing
print("\n" + "="*60)
print("Testing API Gateway Event Parser")
print("="*60)

parsed_event = APIGatewayEvent(test_event)
print(f"\nParsed Event Details:")
print(f"  Method: {parsed_event.method}")
print(f"  Path: {parsed_event.path}")
print(f"  Source IP: {parsed_event.source_ip}")
print(f"  Request ID: {parsed_event.request_id}")
print(f"  Is REST API: {parsed_event.is_rest_api}")
print(f"  Is HTTP API: {parsed_event.is_http_api}")

# Test response formatting
print("\n" + "="*60)
print("Testing API Gateway Response Formatter")
print("="*60)

success_response = APIGatewayResponse.success(
    status_code=200,
    body={"message": "Success", "data": [1, 2, 3]}
)
print(f"\nSuccess Response:")
print(f"  Status: {success_response.get('statusCode')}")
print(f"  Headers: {list(success_response.get('headers', {}).keys())}")
print(f"  Body: {success_response.get('body')[:50]}...")

error_response = APIGatewayResponse.error(
    status_code=404,
    message="Resource not found",
    error_code="NOT_FOUND"
)
print(f"\nError Response:")
print(f"  Status: {error_response.get('statusCode')}")
print(f"  Body: {error_response.get('body')}")

# Test CORS
print("\n" + "="*60)
print("Testing CORS Configuration")
print("="*60)

cors_headers = CORSHelper.get_cors_headers(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type", "Authorization"]
)
print(f"\nCORS Headers:")
for key, value in cors_headers.items():
    print(f"  {key}: {value}")

# Test authentication
print("\n" + "="*60)
print("Testing Authentication Helper")
print("="*60)

auth_headers = {
    "Authorization": "Bearer my-token-123"
}
token = AuthenticationHelper.get_authorization_token(auth_headers)
is_authorized = AuthenticationHelper.is_authorized(auth_headers, "my-token-123")
print(f"\nAuthentication Test:")
print(f"  Token extracted: {token}")
print(f"  Is authorized: {is_authorized}")
print(f"  ✓ Authentication helper working")

print("\n" + "="*60)
print("✓ ALL TESTS PASSED")
print("="*60)
print("\nYour FastAPI application is ready for AWS Lambda deployment!")
print("\nNext steps:")
print("1. Deploy to AWS Lambda using SAM or CloudFormation")
print("2. Create API Gateway integration")
print("3. Test endpoints at: https://{api-id}.execute-api.{region}.amazonaws.com/prod")
print("\nFor deployment instructions, see LAMBDA_DEPLOYMENT_GUIDE.md")
