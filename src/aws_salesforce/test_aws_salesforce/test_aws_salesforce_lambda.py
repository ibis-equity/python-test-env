"""
Unit tests for AWS Salesforce Lambda function
Tests all handlers, routing, and error handling
"""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from aws_salesforce_lambda import (
    LambdaResponse,
    create_account_handler,
    get_account_handler,
    update_account_handler,
    delete_account_handler,
    create_contact_handler,
    get_contact_handler,
    update_contact_handler,
    delete_contact_handler,
    create_opportunity_handler,
    get_opportunity_handler,
    update_opportunity_handler,
    delete_opportunity_handler,
    query_handler,
    batch_create_accounts_handler,
    health_check_handler,
    router,
)


# ==================== Test Fixtures ====================

@pytest.fixture
def mock_context():
    """Mock Lambda context"""
    context = MagicMock()
    context.function_name = "salesforce-api"
    context.aws_request_id = "test-request-id"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:salesforce-api"
    return context


@pytest.fixture
def mock_salesforce_client():
    """Mock Salesforce client"""
    client = AsyncMock()
    return client


# ==================== LambdaResponse Tests ====================

class TestLambdaResponse:
    """Test LambdaResponse helper class"""

    def test_success_response(self):
        """Test successful response format"""
        response = LambdaResponse.success({"id": "123", "name": "Test"}, 200)
        
        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["id"] == "123"
        assert "timestamp" in body

    def test_success_response_with_custom_status(self):
        """Test success response with custom status code"""
        response = LambdaResponse.success({"id": "456"}, 201)
        
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["success"] is True

    def test_error_response(self):
        """Test error response format"""
        response = LambdaResponse.error("Test error", 400, "INVALID_REQUEST")
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"] == "Test error"
        assert body["error_code"] == "INVALID_REQUEST"
        assert "timestamp" in body

    def test_error_response_default_status(self):
        """Test error response with default status code"""
        response = LambdaResponse.error("Test error")
        
        assert response["statusCode"] == 400


# ==================== Account Handler Tests ====================

class TestAccountHandlers:
    """Test Account CRUD handlers"""

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_create_account_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful account creation"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.create_account = AsyncMock(return_value=MagicMock(
            success=True,
            record_id="001xx000003DHP1",
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "body": json.dumps({
                "Name": "Test Company",
                "Phone": "555-1234",
                "Industry": "Technology"
            })
        }

        response = create_account_handler(event, mock_context)

        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["record_id"] == "001xx000003DHP1"

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_create_account_failure(self, mock_run_async, mock_get_client, mock_context):
        """Test account creation failure"""
        mock_client = MagicMock()
        mock_client.create_account = AsyncMock(return_value=MagicMock(
            success=False,
            error="Authentication failed"
        ))
        mock_run_async.return_value = mock_client

        event = {
            "body": json.dumps({"Name": "Test Company"})
        }

        response = create_account_handler(event, mock_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_get_account_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful account retrieval"""
        mock_client = MagicMock()
        mock_client.get_account = AsyncMock(return_value=MagicMock(
            success=True,
            data={"Id": "001xx000003DHP1", "Name": "Test Company"},
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "pathParameters": {"account_id": "001xx000003DHP1"}
        }

        response = get_account_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["Name"] == "Test Company"

    def test_get_account_missing_id(self, mock_context):
        """Test get account without ID"""
        event = {"pathParameters": None}

        response = get_account_handler(event, mock_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_update_account_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful account update"""
        mock_client = MagicMock()
        mock_client.update_account = AsyncMock(return_value=MagicMock(
            success=True,
            record_id="001xx000003DHP1",
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "pathParameters": {"account_id": "001xx000003DHP1"},
            "body": json.dumps({"Name": "Updated Company"})
        }

        response = update_account_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["status"] == "updated"

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_delete_account_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful account deletion"""
        mock_client = MagicMock()
        mock_client.delete_account = AsyncMock(return_value=MagicMock(
            success=True,
            record_id="001xx000003DHP1",
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "pathParameters": {"account_id": "001xx000003DHP1"}
        }

        response = delete_account_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["status"] == "deleted"


# ==================== Contact Handler Tests ====================

class TestContactHandlers:
    """Test Contact CRUD handlers"""

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_create_contact_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful contact creation"""
        mock_client = MagicMock()
        mock_client.create_contact = AsyncMock(return_value=MagicMock(
            success=True,
            record_id="003xx000004TMZ1",
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "body": json.dumps({
                "FirstName": "John",
                "LastName": "Doe",
                "Email": "john@example.com",
                "AccountId": "001xx000003DHP1"
            })
        }

        response = create_contact_handler(event, mock_context)

        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["contact_name"] == "John Doe"

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_get_contact_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful contact retrieval"""
        mock_client = MagicMock()
        mock_client.get_contact = AsyncMock(return_value=MagicMock(
            success=True,
            data={"Id": "003xx000004TMZ1", "FirstName": "John", "LastName": "Doe"},
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "pathParameters": {"contact_id": "003xx000004TMZ1"}
        }

        response = get_contact_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_update_contact_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful contact update"""
        mock_client = MagicMock()
        mock_client.update_contact = AsyncMock(return_value=MagicMock(
            success=True,
            record_id="003xx000004TMZ1",
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "pathParameters": {"contact_id": "003xx000004TMZ1"},
            "body": json.dumps({"Email": "newemail@example.com"})
        }

        response = update_contact_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_delete_contact_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful contact deletion"""
        mock_client = MagicMock()
        mock_client.delete_contact = AsyncMock(return_value=MagicMock(
            success=True,
            record_id="003xx000004TMZ1",
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "pathParameters": {"contact_id": "003xx000004TMZ1"}
        }

        response = delete_contact_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True


# ==================== Opportunity Handler Tests ====================

class TestOpportunityHandlers:
    """Test Opportunity CRUD handlers"""

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_create_opportunity_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful opportunity creation"""
        mock_client = MagicMock()
        mock_client.create_opportunity = AsyncMock(return_value=MagicMock(
            success=True,
            record_id="006xx000007MZF1",
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "body": json.dumps({
                "Name": "Enterprise Deal",
                "Amount": 250000.0,
                "StageName": "Negotiation/Review",
                "CloseDate": "2025-12-31",
                "AccountId": "001xx000003DHP1"
            })
        }

        response = create_opportunity_handler(event, mock_context)

        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["amount"] == 250000.0

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_get_opportunity_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful opportunity retrieval"""
        mock_client = MagicMock()
        mock_client.get_opportunity = AsyncMock(return_value=MagicMock(
            success=True,
            data={"Id": "006xx000007MZF1", "Name": "Enterprise Deal", "Amount": 250000},
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "pathParameters": {"opportunity_id": "006xx000007MZF1"}
        }

        response = get_opportunity_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_update_opportunity_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful opportunity update"""
        mock_client = MagicMock()
        mock_client.update_opportunity = AsyncMock(return_value=MagicMock(
            success=True,
            record_id="006xx000007MZF1",
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "pathParameters": {"opportunity_id": "006xx000007MZF1"},
            "body": json.dumps({"StageName": "Closed Won"})
        }

        response = update_opportunity_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_delete_opportunity_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful opportunity deletion"""
        mock_client = MagicMock()
        mock_client.delete_opportunity = AsyncMock(return_value=MagicMock(
            success=True,
            record_id="006xx000007MZF1",
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "pathParameters": {"opportunity_id": "006xx000007MZF1"}
        }

        response = delete_opportunity_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True


# ==================== Query Handler Tests ====================

class TestQueryHandler:
    """Test SOQL query handler"""

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_query_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful SOQL query"""
        mock_client = MagicMock()
        mock_client.query = AsyncMock(return_value=MagicMock(
            totalSize=2,
            done=True,
            records=[
                {"Id": "001xx000003DHP1", "Name": "Company 1"},
                {"Id": "001xx000003DHP2", "Name": "Company 2"}
            ]
        ))
        mock_run_async.return_value = mock_client

        event = {
            "body": json.dumps({
                "soql": "SELECT Id, Name FROM Account WHERE Industry = 'Technology'"
            })
        }

        response = query_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["total_size"] == 2
        assert len(body["data"]["records"]) == 2

    def test_query_missing_soql(self, mock_context):
        """Test query without SOQL"""
        event = {
            "body": json.dumps({})
        }

        response = query_handler(event, mock_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False

    def test_query_invalid_body(self, mock_context):
        """Test query with invalid JSON"""
        event = {
            "body": "invalid json"
        }

        response = query_handler(event, mock_context)

        assert response["statusCode"] in [400, 500]


# ==================== Batch Handler Tests ====================

class TestBatchHandlers:
    """Test batch operation handlers"""

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_batch_create_accounts_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful batch account creation"""
        mock_client = MagicMock()
        mock_client.create_account = AsyncMock(return_value=MagicMock(
            success=True,
            record_id="001xx000003DHP1",
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {
            "body": json.dumps([
                {"Name": "Company 1", "Phone": "555-0001"},
                {"Name": "Company 2", "Phone": "555-0002"}
            ])
        }

        response = batch_create_accounts_handler(event, mock_context)

        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["total"] == 2

    def test_batch_create_accounts_invalid_body(self, mock_context):
        """Test batch create with non-array body"""
        event = {
            "body": json.dumps({"Name": "Company 1"})
        }

        response = batch_create_accounts_handler(event, mock_context)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False


# ==================== Health Check Tests ====================

class TestHealthCheck:
    """Test health check handler"""

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_health_check_success(self, mock_run_async, mock_get_client, mock_context):
        """Test successful health check"""
        mock_client = MagicMock()
        mock_run_async.return_value = mock_client

        event = {}

        response = health_check_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["status"] == "healthy"
        assert body["data"]["salesforce_connected"] is True

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_health_check_connection_failure(self, mock_run_async, mock_get_client, mock_context):
        """Test health check with connection failure"""
        mock_run_async.side_effect = Exception("Connection failed")

        event = {}

        response = health_check_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["salesforce_connected"] is False


# ==================== Router Tests ====================

class TestRouter:
    """Test API Gateway router"""

    @patch("aws_salesforce_lambda.health_check_handler")
    def test_router_health_check(self, mock_handler, mock_context):
        """Test router dispatches to health check"""
        mock_handler.return_value = {"statusCode": 200, "body": "{}"}

        event = {
            "httpMethod": "GET",
            "path": "/health"
        }

        response = router(event, mock_context)

        assert response["statusCode"] == 200
        mock_handler.assert_called_once()

    @patch("aws_salesforce_lambda.create_account_handler")
    def test_router_create_account(self, mock_handler, mock_context):
        """Test router dispatches to create account"""
        mock_handler.return_value = {"statusCode": 201, "body": "{}"}

        event = {
            "httpMethod": "POST",
            "path": "/accounts"
        }

        response = router(event, mock_context)

        assert response["statusCode"] == 201
        mock_handler.assert_called_once()

    def test_router_not_found(self, mock_context):
        """Test router with non-existent route"""
        event = {
            "httpMethod": "GET",
            "path": "/nonexistent"
        }

        response = router(event, mock_context)

        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["success"] is False

    @patch("aws_salesforce_lambda.create_contact_handler")
    def test_router_with_path_parameters(self, mock_handler, mock_context):
        """Test router with path parameters"""
        mock_handler.return_value = {"statusCode": 201, "body": "{}"}

        event = {
            "httpMethod": "POST",
            "path": "/contacts"
        }

        response = router(event, mock_context)

        assert response["statusCode"] == 201

    def test_router_default_http_method(self, mock_context):
        """Test router with default HTTP method"""
        event = {
            "path": "/health"
        }

        # Should default to GET /health
        response = router(event, mock_context)

        # Should return a valid response (not an error)
        assert "statusCode" in response


# ==================== Error Handling Tests ====================

class TestErrorHandling:
    """Test error handling in handlers"""

    @patch("aws_salesforce_lambda.get_client")
    def test_authentication_error(self, mock_get_client, mock_context):
        """Test handler with authentication error"""
        mock_get_client.side_effect = Exception("Failed to authenticate with Salesforce")

        event = {
            "body": json.dumps({"Name": "Test Company"})
        }

        response = create_account_handler(event, mock_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["success"] is False

    def test_invalid_json_in_body(self, mock_context):
        """Test handler with invalid JSON"""
        event = {
            "body": "not valid json {"
        }

        response = create_account_handler(event, mock_context)

        assert response["statusCode"] == 500

    def test_missing_required_field(self, mock_context):
        """Test handler with missing required field"""
        event = {
            "body": json.dumps({})
        }

        # Should fail due to missing required fields
        with pytest.raises(Exception):
            response = create_account_handler(event, mock_context)


# ==================== Integration Tests ====================

class TestIntegration:
    """Integration tests for complete workflows"""

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_complete_account_workflow(self, mock_run_async, mock_get_client, mock_context):
        """Test complete account CRUD workflow"""
        mock_client = MagicMock()
        
        # Setup mock responses for each operation
        create_result = MagicMock(success=True, record_id="001xx000003DHP1", error=None)
        get_result = MagicMock(
            success=True,
            data={"Id": "001xx000003DHP1", "Name": "Test Company"},
            error=None
        )
        update_result = MagicMock(success=True, record_id="001xx000003DHP1", error=None)
        delete_result = MagicMock(success=True, record_id="001xx000003DHP1", error=None)
        
        mock_client.create_account = AsyncMock(return_value=create_result)
        mock_client.get_account = AsyncMock(return_value=get_result)
        mock_client.update_account = AsyncMock(return_value=update_result)
        mock_client.delete_account = AsyncMock(return_value=delete_result)
        
        mock_run_async.return_value = mock_client

        # Create
        create_event = {"body": json.dumps({"Name": "Test Company"})}
        create_response = create_account_handler(create_event, mock_context)
        assert json.loads(create_response["body"])["success"] is True

        # Get
        get_event = {"pathParameters": {"account_id": "001xx000003DHP1"}}
        get_response = get_account_handler(get_event, mock_context)
        assert json.loads(get_response["body"])["success"] is True

        # Update
        update_event = {
            "pathParameters": {"account_id": "001xx000003DHP1"},
            "body": json.dumps({"Name": "Updated Company"})
        }
        update_response = update_account_handler(update_event, mock_context)
        assert json.loads(update_response["body"])["success"] is True

        # Delete
        delete_event = {"pathParameters": {"account_id": "001xx000003DHP1"}}
        delete_response = delete_account_handler(delete_event, mock_context)
        assert json.loads(delete_response["body"])["success"] is True


# ==================== Performance Tests ====================

class TestPerformance:
    """Test performance characteristics"""

    @patch("aws_salesforce_lambda.get_client")
    @patch("aws_salesforce_lambda.run_async")
    def test_handler_response_format(self, mock_run_async, mock_get_client, mock_context):
        """Test handler response is properly formatted"""
        mock_client = MagicMock()
        mock_client.create_account = AsyncMock(return_value=MagicMock(
            success=True,
            record_id="001xx000003DHP1",
            error=None
        ))
        mock_run_async.return_value = mock_client

        event = {"body": json.dumps({"Name": "Test"})}
        response = create_account_handler(event, mock_context)

        # Verify response structure
        assert "statusCode" in response
        assert "body" in response
        assert "headers" in response
        assert response["headers"]["Content-Type"] == "application/json"
        
        # Verify body is valid JSON
        body = json.loads(response["body"])
        assert "success" in body
        assert "data" in body or "error" in body


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
