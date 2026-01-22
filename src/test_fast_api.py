"""
Unit tests for FastAPI endpoint functions.

Tests all API endpoints including happy path, error cases, and edge cases.
"""

import pytest
import json
from fastapi.testclient import TestClient
from src.fast_api import app, Item, ItemResponse, HealthResponse


class TestRootEndpoint:
    """Test suite for the root endpoint (GET /)"""
    
    def test_read_root_success(self, client):
        """
        Test: Root endpoint returns welcome message
        Expected: 200 OK with message and endpoints
        """
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Welcome to the Python API"
        assert "endpoints" in data
        assert "docs" in data["endpoints"]
        assert "redoc" in data["endpoints"]
    
    def test_read_root_response_format(self, client):
        """
        Test: Root endpoint response has correct format
        Expected: Response contains all required keys
        """
        response = client.get("/")
        data = response.json()
        
        assert isinstance(data, dict)
        assert isinstance(data["endpoints"], dict)
        assert data["endpoints"]["docs"] == "/docs"
        assert data["endpoints"]["redoc"] == "/redoc"
        assert data["endpoints"]["openapi"] == "/api/v1/openapi.json"
    
    def test_read_root_content_type(self, client):
        """
        Test: Root endpoint returns JSON content type
        Expected: Content-Type header is application/json
        """
        response = client.get("/")
        
        assert response.headers["content-type"] == "application/json"
    
    def test_read_root_caching(self, client):
        """
        Test: Root endpoint can be called multiple times
        Expected: Consistent responses on multiple calls
        """
        response1 = client.get("/")
        response2 = client.get("/")
        
        assert response1.json() == response2.json()
        assert response1.status_code == response2.status_code


class TestHealthCheckEndpoint:
    """Test suite for health check endpoint (GET /api/health)"""
    
    def test_health_check_success(self, client):
        """
        Test: Health check endpoint returns healthy status
        Expected: 200 OK with status "healthy" and version
        """
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
    
    def test_health_check_response_model(self, client):
        """
        Test: Health check response matches HealthResponse model
        Expected: Response has correct structure
        """
        response = client.get("/api/health")
        data = response.json()
        
        # Validate structure
        assert "status" in data
        assert "version" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)
    
    def test_health_check_version_format(self, client):
        """
        Test: Version is in correct format
        Expected: Version follows semantic versioning
        """
        response = client.get("/api/health")
        data = response.json()
        
        version = data["version"]
        # Check semantic versioning format: X.Y.Z
        assert len(version.split(".")) == 3
        assert all(part.isdigit() for part in version.split("."))
    
    def test_health_check_is_idempotent(self, client):
        """
        Test: Health check can be called multiple times with same result
        Expected: Consistent responses
        """
        responses = [client.get("/api/health").json() for _ in range(5)]
        
        # All responses should be identical
        assert all(r == responses[0] for r in responses)
    
    def test_health_check_response_time(self, client):
        """
        Test: Health check completes quickly
        Expected: Response time < 100ms
        """
        import time
        start = time.time()
        response = client.get("/api/health")
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert response.status_code == 200
        assert elapsed < 100  # Should be very fast


class TestGetItemEndpoint:
    """Test suite for get item endpoint (GET /api/items/{item_id})"""
    
    def test_get_item_success(self, client):
        """
        Test: Get item by ID returns item details
        Expected: 200 OK with item information
        """
        response = client.get("/api/items/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == 1
        assert data["name"] == "Item 1"
        assert data["description"] == "Description for item 1"
        assert data["status"] == "retrieved"
    
    def test_get_item_with_query_parameter(self, client):
        """
        Test: Get item with query parameter
        Expected: Query parameter included in response
        """
        response = client.get("/api/items/42?q=search_term")
        
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == 42
        assert data["query"] == "search_term"
    
    def test_get_item_multiple_query_params(self, client):
        """
        Test: Get item with multiple query parameters
        Expected: Only first query parameter captured
        """
        response = client.get("/api/items/10?q=test&page=2")
        
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == 10
        assert data["query"] == "test"
    
    def test_get_item_no_query_parameter(self, client):
        """
        Test: Get item without query parameter
        Expected: Query field is None
        """
        response = client.get("/api/items/5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] is None
    
    def test_get_item_invalid_id_zero(self, client):
        """
        Test: Get item with ID = 0 (invalid)
        Expected: 422 Unprocessable Entity
        """
        response = client.get("/api/items/0")
        
        assert response.status_code == 422
    
    def test_get_item_invalid_id_negative(self, client):
        """
        Test: Get item with negative ID
        Expected: 422 Unprocessable Entity
        """
        response = client.get("/api/items/-5")
        
        assert response.status_code == 422
    
    def test_get_item_non_numeric_id(self, client):
        """
        Test: Get item with non-numeric ID
        Expected: 422 Unprocessable Entity
        """
        response = client.get("/api/items/abc")
        
        assert response.status_code == 422
    
    def test_get_item_large_id(self, client):
        """
        Test: Get item with very large ID
        Expected: 200 OK (no upper limit enforced)
        """
        response = client.get("/api/items/999999999")
        
        assert response.status_code == 200
        data = response.json()
        assert data["item_id"] == 999999999
    
    def test_get_item_query_too_long(self, client):
        """
        Test: Get item with query parameter > 50 characters
        Expected: 422 Unprocessable Entity
        """
        long_query = "a" * 51
        response = client.get(f"/api/items/1?q={long_query}")
        
        assert response.status_code == 422
    
    def test_get_item_response_model(self, client):
        """
        Test: Response matches ItemResponse model
        Expected: All required fields present
        """
        response = client.get("/api/items/42")
        data = response.json()
        
        assert "item_id" in data
        assert "name" in data
        assert "description" in data
        assert "status" in data
        assert "query" in data


class TestCreateItemEndpoint:
    """Test suite for create item endpoint (POST /api/items/)"""
    
    def test_create_item_success(self, client, valid_item_data):
        """
        Test: Create item with valid data
        Expected: 201 Created with item information
        """
        response = client.post("/api/items/", json=valid_item_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == valid_item_data["name"]
        assert data["description"] == valid_item_data["description"]
        assert data["status"] == valid_item_data["status"]
    
    def test_create_item_minimal_data(self, client):
        """
        Test: Create item with minimal required data (only name)
        Expected: 201 Created
        """
        response = client.post("/api/items/", json={"name": "Minimal Item"})
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Item"
        assert data["status"] == "created"  # Default status
    
    def test_create_item_no_name(self, client):
        """
        Test: Create item without name field
        Expected: 422 Unprocessable Entity
        """
        response = client.post("/api/items/", json={"description": "No name item"})
        
        assert response.status_code == 422
    
    def test_create_item_empty_name(self, client):
        """
        Test: Create item with empty name
        Expected: 422 Unprocessable Entity (name too short)
        """
        response = client.post("/api/items/", json={"name": ""})
        
        assert response.status_code == 422
    
    def test_create_item_name_too_long(self, client, item_with_long_name):
        """
        Test: Create item with name > 100 characters
        Expected: 422 Unprocessable Entity
        """
        response = client.post("/api/items/", json=item_with_long_name)
        
        assert response.status_code == 422
    
    def test_create_item_description_too_long(self, client, item_with_long_description):
        """
        Test: Create item with description > 500 characters
        Expected: 422 Unprocessable Entity
        """
        response = client.post("/api/items/", json=item_with_long_description)
        
        assert response.status_code == 422
    
    def test_create_item_with_custom_status(self, client):
        """
        Test: Create item with custom status
        Expected: 201 Created with custom status
        """
        item = {
            "name": "Status Item",
            "status": "draft"
        }
        response = client.post("/api/items/", json=item)
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
    
    def test_create_item_invalid_json(self, client):
        """
        Test: Create item with invalid JSON
        Expected: 422 Unprocessable Entity
        """
        response = client.post(
            "/api/items/",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_create_item_missing_body(self, client):
        """
        Test: Create item without body
        Expected: 422 Unprocessable Entity
        """
        response = client.post("/api/items/")
        
        assert response.status_code == 422
    
    def test_create_item_extra_fields_ignored(self, client):
        """
        Test: Create item with extra fields
        Expected: Extra fields are ignored, 201 Created
        """
        item_data = {
            "name": "Test Item",
            "description": "Test",
            "extra_field": "should be ignored"
        }
        response = client.post("/api/items/", json=item_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "extra_field" not in data
    
    def test_create_item_whitespace_in_name(self, client):
        """
        Test: Create item with name containing spaces
        Expected: 201 Created
        """
        item = {"name": "Item With Spaces"}
        response = client.post("/api/items/", json=item)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Item With Spaces"
    
    def test_create_item_special_characters(self, client):
        """
        Test: Create item with special characters in name
        Expected: 201 Created
        """
        item = {"name": "Item-#123!@"}
        response = client.post("/api/items/", json=item)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Item-#123!@"
    
    def test_create_item_unicode_characters(self, client):
        """
        Test: Create item with Unicode characters
        Expected: 201 Created
        """
        item = {"name": "Item 中文 العربية"}
        response = client.post("/api/items/", json=item)
        
        assert response.status_code == 201
        data = response.json()
        assert "中文" in data["name"]
    
    def test_create_item_response_model(self, client, valid_item_data):
        """
        Test: Response matches ItemResponse model
        Expected: All required fields present
        """
        response = client.post("/api/items/", json=valid_item_data)
        data = response.json()
        
        assert "item_id" in data
        assert "name" in data
        assert "description" in data
        assert "status" in data
        assert "query" in data


class TestAwsInfoEndpoint:
    """Test suite for AWS info endpoint (GET /api/aws-info)"""
    
    def test_aws_info_local_environment(self, client):
        """
        Test: AWS info endpoint in local environment
        Expected: 200 OK with local environment info
        """
        response = client.get("/api/aws-info")
        
        assert response.status_code == 200
        data = response.json()
        assert "lambda_function_name" in data
        assert "aws_region" in data
        assert "environment" in data
        assert "lambda_version" in data
    
    def test_aws_info_environment_field(self, client):
        """
        Test: AWS info shows correct environment
        Expected: "environment" is "local" when not in Lambda
        """
        response = client.get("/api/aws-info")
        data = response.json()
        
        # Should be "local" since we're not in Lambda
        assert data["environment"] == "local"
    
    def test_aws_info_function_name_local(self, client):
        """
        Test: AWS info function name in local environment
        Expected: function_name is "local"
        """
        response = client.get("/api/aws-info")
        data = response.json()
        
        assert data["lambda_function_name"] == "local"
    
    def test_aws_info_region_default(self, client):
        """
        Test: AWS info region defaults to us-east-1
        Expected: region is "us-east-1"
        """
        response = client.get("/api/aws-info")
        data = response.json()
        
        assert data["aws_region"] == "us-east-1"
    
    def test_aws_info_response_format(self, client):
        """
        Test: AWS info response has correct format
        Expected: All fields are strings
        """
        response = client.get("/api/aws-info")
        data = response.json()
        
        assert all(isinstance(v, str) for v in data.values())


class TestContentTypes:
    """Test suite for content type handling"""
    
    def test_all_endpoints_return_json(self, client, valid_item_data):
        """
        Test: All endpoints return JSON content type
        Expected: Content-Type is application/json
        """
        endpoints = [
            (client.get, "/"),
            (client.get, "/api/health"),
            (client.get, "/api/items/1"),
            (client.post, "/api/items/", None),
        ]
        
        for method, path, *data in endpoints:
            if method == client.post:
                response = method(path, json=valid_item_data)
            else:
                response = method(path)
            
            assert response.headers["content-type"] == "application/json"


class TestErrorHandling:
    """Test suite for error handling"""
    
    def test_404_not_found(self, client):
        """
        Test: Non-existent endpoint returns 404
        Expected: 404 Not Found
        """
        response = client.get("/nonexistent")
        
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client):
        """
        Test: Wrong HTTP method returns 405
        Expected: 405 Method Not Allowed
        """
        response = client.put("/api/items/1")
        
        assert response.status_code == 405
    
    def test_422_validation_error_format(self, client):
        """
        Test: Validation error response format
        Expected: Response includes detail field with errors
        """
        response = client.post("/api/items/", json={})
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""
    
    def test_item_id_boundary_one(self, client):
        """
        Test: Get item with ID = 1 (minimum valid)
        Expected: 200 OK
        """
        response = client.get("/api/items/1")
        
        assert response.status_code == 200
        assert response.json()["item_id"] == 1
    
    def test_query_parameter_exactly_max_length(self, client):
        """
        Test: Query parameter exactly 50 characters
        Expected: 200 OK
        """
        query = "a" * 50
        response = client.get(f"/api/items/1?q={query}")
        
        assert response.status_code == 200
    
    def test_name_exactly_max_length(self, client):
        """
        Test: Item name exactly 100 characters
        Expected: 201 Created
        """
        item = {"name": "a" * 100}
        response = client.post("/api/items/", json=item)
        
        assert response.status_code == 201
    
    def test_description_exactly_max_length(self, client):
        """
        Test: Item description exactly 500 characters
        Expected: 201 Created
        """
        item = {
            "name": "Test",
            "description": "b" * 500
        }
        response = client.post("/api/items/", json=item)
        
        assert response.status_code == 201
