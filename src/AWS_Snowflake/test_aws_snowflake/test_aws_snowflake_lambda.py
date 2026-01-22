"""
Unit tests for aws_snowflake_lambda.py

This test suite covers:
- LambdaResponse class methods
- SnowflakeConnection class methods
- All handler functions
- Error handling and edge cases
- Lambda router functionality
"""

import json
import pytest
import os
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AWS_Snowflake'))
from aws_snowflake_lambda import (
    LambdaResponse,
    SnowflakeConnection,
    execute_query_handler,
    insert_data_handler,
    update_data_handler,
    delete_data_handler,
    get_table_schema_handler,
    list_tables_handler,
    bulk_insert_handler,
    lambda_handler
)


# ==================== Fixtures ====================

@pytest.fixture
def mock_context():
    """Create a mock Lambda context"""
    context = Mock()
    context.function_name = "snowflake-api"
    context.function_version = "1"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789:function:snowflake-api"
    context.memory_limit_in_mb = 512
    context.get_remaining_time_in_millis = Mock(return_value=300000)
    return context


@pytest.fixture
def mock_snowflake_connection():
    """Create a mock Snowflake connection"""
    connection = MagicMock()
    connection.cursor = Mock()
    connection.commit = Mock()
    connection.close = Mock()
    return connection


@pytest.fixture
def mock_cursor():
    """Create a mock database cursor"""
    cursor = MagicMock()
    cursor.execute = Mock()
    cursor.fetchall = Mock(return_value=[])
    cursor.fetchone = Mock(return_value=None)
    cursor.rowcount = 0
    cursor.description = [("ID",), ("NAME",), ("EMAIL",)]
    cursor.close = Mock()
    return cursor


@pytest.fixture
def setup_env_vars():
    """Set up environment variables for testing"""
    env_vars = {
        "SNOWFLAKE_ACCOUNT": "test_account",
        "SNOWFLAKE_USER": "test_user",
        "SNOWFLAKE_PASSWORD": "test_password",
        "SNOWFLAKE_DATABASE": "TEST_DB",
        "SNOWFLAKE_SCHEMA": "PUBLIC",
        "SNOWFLAKE_WAREHOUSE": "COMPUTE_WH",
        "SNOWFLAKE_ROLE": "SYSADMIN"
    }
    with patch.dict(os.environ, env_vars):
        yield


# ==================== LambdaResponse Tests ====================

class TestLambdaResponse:
    """Tests for LambdaResponse class"""

    def test_success_response_default_status(self):
        """Test success response with default status code"""
        data = {"id": 1, "name": "test"}
        response = LambdaResponse.success(data)
        
        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"
        
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"] == data
        assert "timestamp" in body

    def test_success_response_custom_status(self):
        """Test success response with custom status code"""
        data = {"id": 1}
        response = LambdaResponse.success(data, status_code=201)
        
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["success"] is True

    def test_success_response_with_list_data(self):
        """Test success response with list data"""
        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = LambdaResponse.success(data)
        
        body = json.loads(response["body"])
        assert body["data"] == data
        assert len(body["data"]) == 3

    def test_error_response_default(self):
        """Test error response with defaults"""
        response = LambdaResponse.error("Test error")
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["success"] is False
        assert body["error"] == "Test error"
        assert body["error_code"] == "ERROR"

    def test_error_response_custom_status(self):
        """Test error response with custom status code"""
        response = LambdaResponse.error("Not found", status_code=404)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error"] == "Not found"

    def test_error_response_custom_code(self):
        """Test error response with custom error code"""
        response = LambdaResponse.error("Missing param", error_code="MISSING_PARAM")
        
        body = json.loads(response["body"])
        assert body["error_code"] == "MISSING_PARAM"

    def test_response_headers(self):
        """Test response headers"""
        response = LambdaResponse.success({})
        
        assert "headers" in response
        assert response["headers"]["Content-Type"] == "application/json"

    def test_response_timestamp(self):
        """Test that response includes timestamp"""
        before = datetime.utcnow().isoformat()
        response = LambdaResponse.success({})
        after = datetime.utcnow().isoformat()
        
        body = json.loads(response["body"])
        assert "timestamp" in body
        assert before <= body["timestamp"] <= after


# ==================== SnowflakeConnection Tests ====================

class TestSnowflakeConnection:
    """Tests for SnowflakeConnection class"""

    def test_connection_init(self, setup_env_vars):
        """Test SnowflakeConnection initialization"""
        conn = SnowflakeConnection()
        
        assert conn.account == "test_account"
        assert conn.user == "test_user"
        assert conn.password == "test_password"
        assert conn.database == "TEST_DB"
        assert conn.schema == "PUBLIC"
        assert conn.warehouse == "COMPUTE_WH"
        assert conn.role == "SYSADMIN"

    def test_connection_init_default_role(self):
        """Test SnowflakeConnection with default role"""
        env_vars = {
            "SNOWFLAKE_ACCOUNT": "test",
            "SNOWFLAKE_USER": "user",
            "SNOWFLAKE_PASSWORD": "pass",
            "SNOWFLAKE_DATABASE": "db",
            "SNOWFLAKE_SCHEMA": "schema",
            "SNOWFLAKE_WAREHOUSE": "wh"
        }
        with patch.dict(os.environ, env_vars):
            conn = SnowflakeConnection()
            assert conn.role == "SYSADMIN"

    @patch('aws_snowflake_lambda.snowflake.connector.connect')
    def test_connect_success(self, mock_connect, setup_env_vars, mock_snowflake_connection):
        """Test successful connection"""
        mock_connect.return_value = mock_snowflake_connection
        
        conn = SnowflakeConnection()
        result = conn.connect()
        
        assert result == mock_snowflake_connection
        mock_connect.assert_called_once()
        call_kwargs = mock_connect.call_args[1]
        assert call_kwargs["account"] == "test_account"
        assert call_kwargs["user"] == "test_user"

    @patch('aws_snowflake_lambda.snowflake.connector.connect')
    def test_connect_failure(self, mock_connect, setup_env_vars):
        """Test connection failure"""
        mock_connect.side_effect = Exception("Connection failed")
        
        conn = SnowflakeConnection()
        with pytest.raises(Exception):
            conn.connect()

    def test_disconnect_success(self, mock_snowflake_connection):
        """Test successful disconnection"""
        SnowflakeConnection.disconnect(mock_snowflake_connection)
        
        mock_snowflake_connection.close.assert_called_once()

    def test_disconnect_none_connection(self):
        """Test disconnect with None connection"""
        # Should not raise an error
        SnowflakeConnection.disconnect(None)

    def test_disconnect_already_closed(self):
        """Test disconnect when connection already closed"""
        connection = MagicMock()
        connection.close.side_effect = Exception("Already closed")
        
        # Should not raise an error
        SnowflakeConnection.disconnect(connection)


# ==================== Handler Tests ====================

class TestExecuteQueryHandler:
    """Tests for execute_query_handler function"""

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_execute_query_success(self, mock_conn_class, mock_context):
        """Test successful query execution"""
        # Setup mocks
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"ID": 1, "NAME": "John"},
            {"ID": 2, "NAME": "Jane"}
        ]
        mock_cursor.description = [("ID",), ("NAME",)]
        mock_connection.cursor.return_value = mock_cursor
        
        # Create event
        event = {
            "httpMethod": "POST",
            "path": "/snowflake/query",
            "body": json.dumps({"query": "SELECT * FROM USERS", "return_type": "dict"})
        }
        
        # Execute
        response = execute_query_handler(event, mock_context)
        
        # Assert
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["success"] is True
        assert body["data"]["count"] == 2

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_execute_query_no_results(self, mock_conn_class, mock_context):
        """Test query with no results"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.description = [("ID",), ("NAME",)]
        mock_connection.cursor.return_value = mock_cursor
        
        event = {
            "body": json.dumps({"query": "SELECT * FROM USERS WHERE ID = 999"})
        }
        
        response = execute_query_handler(event, mock_context)
        
        body = json.loads(response["body"])
        assert body["data"]["count"] == 0

    def test_execute_query_missing_query(self, mock_context):
        """Test query handler with missing query parameter"""
        event = {
            "body": json.dumps({})
        }
        
        response = execute_query_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "MISSING_QUERY"

    def test_execute_query_invalid_json(self, mock_context):
        """Test query handler with invalid JSON"""
        event = {
            "body": "invalid json{{"
        }
        
        response = execute_query_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "INVALID_JSON"

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_execute_query_connection_error(self, mock_conn_class, mock_context):
        """Test query handler with connection error"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        mock_conn.connect.side_effect = Exception("Connection failed")
        
        event = {
            "body": json.dumps({"query": "SELECT 1"})
        }
        
        response = execute_query_handler(event, mock_context)
        
        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert body["error_code"] == "QUERY_ERROR"


class TestInsertDataHandler:
    """Tests for insert_data_handler function"""

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_insert_data_success(self, mock_conn_class, mock_context):
        """Test successful data insertion"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 2
        mock_connection.cursor.return_value = mock_cursor
        
        event = {
            "body": json.dumps({
                "table": "USERS",
                "columns": ["ID", "NAME"],
                "values": [[1, "John"], [2, "Jane"]]
            })
        }
        
        response = insert_data_handler(event, mock_context)
        
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["data"]["inserted_rows"] == 2
        assert body["data"]["table"] == "USERS"

    def test_insert_data_missing_table(self, mock_context):
        """Test insert with missing table parameter"""
        event = {
            "body": json.dumps({
                "columns": ["ID", "NAME"],
                "values": [[1, "John"]]
            })
        }
        
        response = insert_data_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "MISSING_PARAMETERS"

    def test_insert_data_missing_columns(self, mock_context):
        """Test insert with missing columns parameter"""
        event = {
            "body": json.dumps({
                "table": "USERS",
                "values": [[1, "John"]]
            })
        }
        
        response = insert_data_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "MISSING_PARAMETERS"

    def test_insert_data_missing_values(self, mock_context):
        """Test insert with missing values parameter"""
        event = {
            "body": json.dumps({
                "table": "USERS",
                "columns": ["ID", "NAME"]
            })
        }
        
        response = insert_data_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "MISSING_PARAMETERS"

    def test_insert_data_invalid_json(self, mock_context):
        """Test insert with invalid JSON"""
        event = {
            "body": "not valid json"
        }
        
        response = insert_data_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "INVALID_JSON"


class TestUpdateDataHandler:
    """Tests for update_data_handler function"""

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_update_data_success(self, mock_conn_class, mock_context):
        """Test successful data update"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_connection.cursor.return_value = mock_cursor
        
        event = {
            "body": json.dumps({
                "table": "USERS",
                "updates": {"NAME": "John Updated", "EMAIL": "john@example.com"},
                "where_clause": "WHERE ID = 1"
            })
        }
        
        response = update_data_handler(event, mock_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["updated_rows"] == 1

    def test_update_data_missing_table(self, mock_context):
        """Test update with missing table parameter"""
        event = {
            "body": json.dumps({
                "updates": {"NAME": "John"},
                "where_clause": "WHERE ID = 1"
            })
        }
        
        response = update_data_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "MISSING_PARAMETERS"

    def test_update_data_missing_updates(self, mock_context):
        """Test update with missing updates parameter"""
        event = {
            "body": json.dumps({
                "table": "USERS",
                "where_clause": "WHERE ID = 1"
            })
        }
        
        response = update_data_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "MISSING_PARAMETERS"

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_update_data_no_matches(self, mock_conn_class, mock_context):
        """Test update when no rows match WHERE clause"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0
        mock_connection.cursor.return_value = mock_cursor
        
        event = {
            "body": json.dumps({
                "table": "USERS",
                "updates": {"NAME": "John"},
                "where_clause": "WHERE ID = 999"
            })
        }
        
        response = update_data_handler(event, mock_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["updated_rows"] == 0


class TestDeleteDataHandler:
    """Tests for delete_data_handler function"""

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_delete_data_success(self, mock_conn_class, mock_context):
        """Test successful data deletion"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_connection.cursor.return_value = mock_cursor
        
        event = {
            "body": json.dumps({
                "table": "USERS",
                "where_clause": "WHERE ID = 1"
            })
        }
        
        response = delete_data_handler(event, mock_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["deleted_rows"] == 1

    def test_delete_data_missing_table(self, mock_context):
        """Test delete with missing table parameter"""
        event = {
            "body": json.dumps({
                "where_clause": "WHERE ID = 1"
            })
        }
        
        response = delete_data_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "MISSING_TABLE"

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_delete_data_no_where_clause(self, mock_conn_class, mock_context):
        """Test delete with no WHERE clause (deletes all)"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 100
        mock_connection.cursor.return_value = mock_cursor
        
        event = {
            "body": json.dumps({
                "table": "USERS"
            })
        }
        
        response = delete_data_handler(event, mock_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["deleted_rows"] == 100


class TestGetTableSchemaHandler:
    """Tests for get_table_schema_handler function"""

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_get_schema_success(self, mock_conn_class, mock_context):
        """Test successful schema retrieval"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"name": "ID", "type": "NUMBER", "null?": "N", "primary key": "Y", "default": None},
            {"name": "NAME", "type": "VARCHAR", "null?": "N", "primary key": "N", "default": None}
        ]
        mock_connection.cursor.return_value = mock_cursor
        
        event = {
            "body": json.dumps({"table": "USERS"})
        }
        
        response = get_table_schema_handler(event, mock_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["column_count"] == 2
        assert body["data"]["table"] == "USERS"

    def test_get_schema_missing_table(self, mock_context):
        """Test schema retrieval with missing table parameter"""
        event = {
            "body": json.dumps({})
        }
        
        response = get_table_schema_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "MISSING_TABLE"


class TestListTablesHandler:
    """Tests for list_tables_handler function"""

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_list_tables_success(self, mock_conn_class, mock_context):
        """Test successful table listing"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"name": "USERS"},
            {"name": "ORDERS"},
            {"name": "PRODUCTS"}
        ]
        mock_connection.cursor.return_value = mock_cursor
        
        event = {}
        
        response = list_tables_handler(event, mock_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["count"] == 3
        assert "USERS" in body["data"]["tables"]

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_list_tables_empty(self, mock_conn_class, mock_context):
        """Test table listing with no tables"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        
        event = {}
        
        response = list_tables_handler(event, mock_context)
        
        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["data"]["count"] == 0


class TestBulkInsertHandler:
    """Tests for bulk_insert_handler function"""

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_bulk_insert_success(self, mock_conn_class, mock_context):
        """Test successful bulk insert"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {"status": "loaded"}
        mock_connection.cursor.return_value = mock_cursor
        
        event = {
            "body": json.dumps({
                "table": "CUSTOMERS",
                "file_path": "s3://bucket/data.csv",
                "file_format": "csv"
            })
        }
        
        response = bulk_insert_handler(event, mock_context)
        
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert body["data"]["status"] == "completed"

    def test_bulk_insert_missing_table(self, mock_context):
        """Test bulk insert with missing table parameter"""
        event = {
            "body": json.dumps({
                "file_path": "s3://bucket/data.csv"
            })
        }
        
        response = bulk_insert_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "MISSING_PARAMETERS"

    def test_bulk_insert_missing_file_path(self, mock_context):
        """Test bulk insert with missing file_path parameter"""
        event = {
            "body": json.dumps({
                "table": "CUSTOMERS"
            })
        }
        
        response = bulk_insert_handler(event, mock_context)
        
        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error_code"] == "MISSING_PARAMETERS"

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_bulk_insert_default_format(self, mock_conn_class, mock_context):
        """Test bulk insert with default file format"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {}
        mock_connection.cursor.return_value = mock_cursor
        
        event = {
            "body": json.dumps({
                "table": "CUSTOMERS",
                "file_path": "s3://bucket/data.csv"
                # file_format omitted, should default to "csv"
            })
        }
        
        response = bulk_insert_handler(event, mock_context)
        
        assert response["statusCode"] == 201


# ==================== Lambda Router Tests ====================

class TestLambdaRouter:
    """Tests for lambda_handler router function"""

    @patch('aws_snowflake_lambda.execute_query_handler')
    def test_route_query_post(self, mock_handler, mock_context):
        """Test routing to query handler with POST"""
        mock_handler.return_value = LambdaResponse.success({})
        
        event = {
            "httpMethod": "POST",
            "path": "/snowflake/query"
        }
        
        response = lambda_handler(event, mock_context)
        mock_handler.assert_called_once()

    @patch('aws_snowflake_lambda.insert_data_handler')
    def test_route_insert_post(self, mock_handler, mock_context):
        """Test routing to insert handler with POST"""
        mock_handler.return_value = LambdaResponse.success({})
        
        event = {
            "httpMethod": "POST",
            "path": "/snowflake/insert"
        }
        
        response = lambda_handler(event, mock_context)
        mock_handler.assert_called_once()

    @patch('aws_snowflake_lambda.update_data_handler')
    def test_route_update_put(self, mock_handler, mock_context):
        """Test routing to update handler with PUT"""
        mock_handler.return_value = LambdaResponse.success({})
        
        event = {
            "httpMethod": "PUT",
            "path": "/snowflake/update"
        }
        
        response = lambda_handler(event, mock_context)
        mock_handler.assert_called_once()

    @patch('aws_snowflake_lambda.delete_data_handler')
    def test_route_delete_delete(self, mock_handler, mock_context):
        """Test routing to delete handler with DELETE"""
        mock_handler.return_value = LambdaResponse.success({})
        
        event = {
            "httpMethod": "DELETE",
            "path": "/snowflake/delete"
        }
        
        response = lambda_handler(event, mock_context)
        mock_handler.assert_called_once()

    @patch('aws_snowflake_lambda.get_table_schema_handler')
    def test_route_schema_get(self, mock_handler, mock_context):
        """Test routing to schema handler with GET"""
        mock_handler.return_value = LambdaResponse.success({})
        
        event = {
            "httpMethod": "GET",
            "path": "/snowflake/schema"
        }
        
        response = lambda_handler(event, mock_context)
        mock_handler.assert_called_once()

    @patch('aws_snowflake_lambda.list_tables_handler')
    def test_route_tables_get(self, mock_handler, mock_context):
        """Test routing to tables handler with GET"""
        mock_handler.return_value = LambdaResponse.success({})
        
        event = {
            "httpMethod": "GET",
            "path": "/snowflake/tables"
        }
        
        response = lambda_handler(event, mock_context)
        mock_handler.assert_called_once()

    @patch('aws_snowflake_lambda.bulk_insert_handler')
    def test_route_bulk_insert_post(self, mock_handler, mock_context):
        """Test routing to bulk insert handler with POST"""
        mock_handler.return_value = LambdaResponse.success({})
        
        event = {
            "httpMethod": "POST",
            "path": "/snowflake/bulk-insert"
        }
        
        response = lambda_handler(event, mock_context)
        mock_handler.assert_called_once()

    def test_route_invalid_path(self, mock_context):
        """Test routing with invalid path"""
        event = {
            "httpMethod": "GET",
            "path": "/invalid/path"
        }
        
        response = lambda_handler(event, mock_context)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error_code"] == "NOT_FOUND"

    @patch('aws_snowflake_lambda.execute_query_handler')
    def test_route_query_wrong_method(self, mock_handler, mock_context):
        """Test query endpoint with wrong HTTP method"""
        event = {
            "httpMethod": "GET",
            "path": "/snowflake/query"
        }
        
        response = lambda_handler(event, mock_context)
        
        assert response["statusCode"] == 404
        body = json.loads(response["body"])
        assert body["error_code"] == "NOT_FOUND"

    def test_route_case_insensitive_method(self, mock_context):
        """Test that HTTP method is case-insensitive"""
        with patch('aws_snowflake_lambda.execute_query_handler') as mock_handler:
            mock_handler.return_value = LambdaResponse.success({})
            
            event = {
                "httpMethod": "post",  # lowercase
                "path": "/snowflake/query"
            }
            
            response = lambda_handler(event, mock_context)
            mock_handler.assert_called_once()

    def test_route_empty_path(self, mock_context):
        """Test router with empty path"""
        event = {
            "httpMethod": "GET",
            "path": ""
        }
        
        response = lambda_handler(event, mock_context)
        
        assert response["statusCode"] == 404


# ==================== Integration Tests ====================

class TestIntegration:
    """Integration tests for the complete workflow"""

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_complete_workflow(self, mock_conn_class, mock_context):
        """Test a complete workflow: insert -> query -> delete"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        
        mock_connection = MagicMock()
        mock_conn.connect.return_value = mock_connection
        
        # Setup cursor
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_cursor.fetchall.return_value = [{"ID": 1, "NAME": "Test"}]
        mock_cursor.description = [("ID",), ("NAME",)]
        mock_connection.cursor.return_value = mock_cursor
        
        # Insert
        insert_event = {
            "body": json.dumps({
                "table": "TEST_TABLE",
                "columns": ["ID", "NAME"],
                "values": [[1, "Test"]]
            })
        }
        insert_response = insert_data_handler(insert_event, mock_context)
        assert insert_response["statusCode"] == 201
        
        # Query
        query_event = {
            "body": json.dumps({"query": "SELECT * FROM TEST_TABLE"})
        }
        query_response = execute_query_handler(query_event, mock_context)
        assert query_response["statusCode"] == 200
        
        # Delete
        delete_event = {
            "body": json.dumps({
                "table": "TEST_TABLE",
                "where_clause": "WHERE ID = 1"
            })
        }
        delete_response = delete_data_handler(delete_event, mock_context)
        assert delete_response["statusCode"] == 200

    @patch('aws_snowflake_lambda.SnowflakeConnection')
    def test_error_recovery(self, mock_conn_class, mock_context):
        """Test error handling and recovery"""
        mock_conn = MagicMock()
        mock_conn_class.return_value = mock_conn
        mock_conn.connect.side_effect = [
            Exception("Connection failed"),  # First call fails
            MagicMock()  # Second call succeeds
        ]
        
        # First request should fail
        event1 = {
            "body": json.dumps({"query": "SELECT 1"})
        }
        response1 = execute_query_handler(event1, mock_context)
        assert response1["statusCode"] == 500
        
        # Second request should be independent (since we reset)
        mock_conn.connect.side_effect = None
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_conn.connect.return_value = mock_connection
        
        event2 = {
            "body": json.dumps({"query": "SELECT 1"})
        }
        response2 = execute_query_handler(event2, mock_context)
        assert response2["statusCode"] == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
