"""
Pytest configuration and shared fixtures for testing.

This file provides common fixtures and configuration used across all tests.
"""

import pytest
import json
from typing import Generator
from fastapi.testclient import TestClient
from src.fast_api import app, Item, ItemResponse, HealthResponse
from src.aws_gateway_integration import APIGatewayEvent


@pytest.fixture
def client() -> TestClient:
    """
    Fixture providing a FastAPI test client.
    
    Returns:
        TestClient: FastAPI test client for making requests
    """
    return TestClient(app)


@pytest.fixture
def valid_item_data() -> dict:
    """
    Fixture providing valid item data for creating items.
    
    Returns:
        dict: Valid item creation payload
    """
    return {
        "name": "Test Item",
        "description": "This is a test item",
        "status": "active"
    }


@pytest.fixture
def invalid_item_data() -> dict:
    """
    Fixture providing invalid item data for validation testing.
    
    Returns:
        dict: Invalid item creation payload (empty name)
    """
    return {
        "name": "",  # Empty name - should fail validation
        "description": "Test item"
    }


@pytest.fixture
def sample_rest_api_event() -> dict:
    """
    Fixture providing a sample REST API Gateway event.
    
    Returns:
        dict: Sample API Gateway REST API event
    """
    return {
        "resource": "/api/items",
        "path": "/api/items",
        "httpMethod": "GET",
        "headers": {
            "Host": "api.example.com",
            "User-Agent": "curl/7.64.1",
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Authorization": "Bearer token123"
        },
        "queryStringParameters": {
            "page": "1",
            "limit": "10"
        },
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {
            "resourceId": "123456",
            "resourcePath": "/api/items",
            "httpMethod": "GET",
            "extendedRequestId": "request-id-123",
            "requestTime": "09/Apr/2015:12:34:56 +0000",
            "path": "/api/items",
            "accountId": "123456789012",
            "protocol": "HTTP/1.1",
            "stage": "prod",
            "domainPrefix": "api",
            "requestTimeEpoch": 1428582896000,
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "identity": {
                "cognitoIdentityPoolId": None,
                "accountId": None,
                "cognitoIdentityId": None,
                "caller": None,
                "sourceIp": "192.168.1.100",
                "principalOrgId": None,
                "accessKey": None,
                "cognitoAuthenticationType": None,
                "cognitoAuthenticationProvider": None,
                "userArn": None,
                "userAgent": "curl/7.64.1",
                "user": None
            },
            "domainName": "api.execute-api.us-east-1.amazonaws.com",
            "apiId": "1234567890"
        },
        "body": None,
        "isBase64Encoded": False
    }


@pytest.fixture
def sample_http_api_event() -> dict:
    """
    Fixture providing a sample HTTP API Gateway event.
    
    Returns:
        dict: Sample API Gateway HTTP API event
    """
    return {
        "version": "2.0",
        "routeKey": "GET /api/items",
        "rawPath": "/api/items",
        "rawQueryString": "page=1&limit=10",
        "headers": {
            "host": "api.example.com",
            "user-agent": "curl/7.64.1",
            "accept": "*/*",
            "content-type": "application/json",
            "authorization": "Bearer token123"
        },
        "queryStringParameters": "page=1&limit=10",
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "api-id",
            "domainName": "api.execute-api.us-east-1.amazonaws.com",
            "domainPrefix": "api",
            "http": {
                "method": "GET",
                "path": "/api/items",
                "protocol": "HTTP/1.1",
                "sourceIp": "192.168.1.100",
                "userAgent": "curl/7.64.1"
            },
            "requestId": "id=",
            "routeKey": "GET /api/items",
            "stage": "$default",
            "time": "12/Mar/2020:19:03:58 +0000",
            "timeEpoch": 1583348638390
        },
        "isBase64Encoded": False
    }


@pytest.fixture
def item_with_long_name() -> dict:
    """
    Fixture providing item data with a name exceeding max length.
    
    Returns:
        dict: Item with name > 100 characters
    """
    return {
        "name": "a" * 101,  # 101 characters - exceeds max
        "description": "Test item"
    }


@pytest.fixture
def item_with_long_description() -> dict:
    """
    Fixture providing item data with a description exceeding max length.
    
    Returns:
        dict: Item with description > 500 characters
    """
    return {
        "name": "Test Item",
        "description": "a" * 501  # 501 characters - exceeds max
    }


@pytest.fixture
def api_key_header() -> dict:
    """
    Fixture providing headers with API key authentication.
    
    Returns:
        dict: Headers with Bearer token
    """
    return {"Authorization": "Bearer secret-api-key-123"}


@pytest.fixture
def cors_headers() -> dict:
    """
    Fixture providing CORS headers.
    
    Returns:
        dict: CORS response headers
    """
    return {
        "Access-Control-Allow-Origin": "https://example.com",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }


@pytest.fixture
def mock_lambda_context():
    """
    Fixture providing a mock Lambda context object.
    
    Returns:
        MockLambdaContext: Mock context with Lambda attributes
    """
    class MockLambdaContext:
        def __init__(self):
            self.function_name = "test-function"
            self.function_version = "$LATEST"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
            self.memory_limit_in_mb = 512
            self.aws_request_id = "test-request-id"
            self.log_group_name = "/aws/lambda/test-function"
            self.log_stream_name = "2024/01/01/[$LATEST]abcdefgh"
    
    return MockLambdaContext()
