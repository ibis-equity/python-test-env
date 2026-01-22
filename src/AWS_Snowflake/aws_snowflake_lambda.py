"""
AWS Lambda function for Snowflake API integration
Provides handlers for various Snowflake operations via Lambda events
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import snowflake.connector
from snowflake.connector import DictCursor

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaResponse:
    """Helper class for Lambda response formatting"""

    @staticmethod
    def success(data: Any, status_code: int = 200) -> Dict[str, Any]:
        """Return success response"""
        return {
            "statusCode": status_code,
            "body": json.dumps({
                "success": True,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }

    @staticmethod
    def error(message: str, status_code: int = 400, error_code: str = "ERROR") -> Dict[str, Any]:
        """Return error response"""
        return {
            "statusCode": status_code,
            "body": json.dumps({
                "success": False,
                "error": message,
                "error_code": error_code,
                "timestamp": datetime.utcnow().isoformat()
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }


class SnowflakeConnection:
    """Snowflake connection manager"""

    def __init__(self):
        """Initialize Snowflake connection parameters from environment variables"""
        self.account = os.getenv("SNOWFLAKE_ACCOUNT")
        self.user = os.getenv("SNOWFLAKE_USER")
        self.password = os.getenv("SNOWFLAKE_PASSWORD")
        self.database = os.getenv("SNOWFLAKE_DATABASE")
        self.schema = os.getenv("SNOWFLAKE_SCHEMA")
        self.warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        self.role = os.getenv("SNOWFLAKE_ROLE", "SYSADMIN")

    def connect(self) -> snowflake.connector.SnowflakeConnection:
        """Create and return a Snowflake connection"""
        try:
            connection = snowflake.connector.connect(
                account=self.account,
                user=self.user,
                password=self.password,
                database=self.database,
                schema=self.schema,
                warehouse=self.warehouse,
                role=self.role
            )
            logger.info("Successfully connected to Snowflake")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {str(e)}")
            raise

    @staticmethod
    def disconnect(connection: snowflake.connector.SnowflakeConnection) -> None:
        """Close Snowflake connection"""
        try:
            if connection:
                connection.close()
                logger.info("Snowflake connection closed")
        except Exception as e:
            logger.error(f"Error closing Snowflake connection: {str(e)}")


# ==================== Query Handlers ====================

def execute_query_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to execute a Snowflake query
    
    Event body:
    {
        "query": "SELECT * FROM table_name LIMIT 100",
        "return_type": "list"  # "list" or "dict"
    }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        query = body.get("query")
        return_type = body.get("return_type", "list")

        if not query:
            return LambdaResponse.error("Query parameter is required", 400, "MISSING_QUERY")

        conn = SnowflakeConnection()
        connection = conn.connect()
        
        try:
            if return_type == "dict":
                cursor = connection.cursor(DictCursor)
            else:
                cursor = connection.cursor()

            cursor.execute(query)
            results = cursor.fetchall()
            
            # Get column names if using DictCursor
            if return_type == "dict":
                data = results
            else:
                # Convert tuple results to list of dicts with column names
                columns = [desc[0] for desc in cursor.description]
                data = [dict(zip(columns, row)) for row in results]

            cursor.close()
            logger.info(f"Query executed successfully, returned {len(data)} rows")
            return LambdaResponse.success({"rows": data, "count": len(data)})

        finally:
            SnowflakeConnection.disconnect(connection)

    except json.JSONDecodeError:
        return LambdaResponse.error("Invalid JSON in request body", 400, "INVALID_JSON")
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return LambdaResponse.error(f"Query execution failed: {str(e)}", 500, "QUERY_ERROR")


def insert_data_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to insert data into Snowflake
    
    Event body:
    {
        "table": "table_name",
        "columns": ["col1", "col2", "col3"],
        "values": [[val1, val2, val3], [val1, val2, val3]],
        "return_count": true
    }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        table = body.get("table")
        columns = body.get("columns", [])
        values = body.get("values", [])

        if not table or not columns or not values:
            return LambdaResponse.error(
                "table, columns, and values parameters are required",
                400,
                "MISSING_PARAMETERS"
            )

        conn = SnowflakeConnection()
        connection = conn.connect()

        try:
            cursor = connection.cursor()
            
            # Build INSERT statement
            placeholders = ",".join(["?" for _ in columns])
            insert_query = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
            
            # Execute inserts
            inserted_count = 0
            for row in values:
                cursor.execute(insert_query, row)
                inserted_count += 1

            connection.commit()
            logger.info(f"Inserted {inserted_count} rows into {table}")
            cursor.close()
            
            return LambdaResponse.success({
                "table": table,
                "inserted_rows": inserted_count
            }, 201)

        finally:
            SnowflakeConnection.disconnect(connection)

    except json.JSONDecodeError:
        return LambdaResponse.error("Invalid JSON in request body", 400, "INVALID_JSON")
    except Exception as e:
        logger.error(f"Error inserting data: {str(e)}")
        return LambdaResponse.error(f"Insert operation failed: {str(e)}", 500, "INSERT_ERROR")


def update_data_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to update data in Snowflake
    
    Event body:
    {
        "table": "table_name",
        "updates": {"col1": "value1", "col2": "value2"},
        "where_clause": "WHERE id = 1"
    }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        table = body.get("table")
        updates = body.get("updates", {})
        where_clause = body.get("where_clause", "")

        if not table or not updates:
            return LambdaResponse.error(
                "table and updates parameters are required",
                400,
                "MISSING_PARAMETERS"
            )

        conn = SnowflakeConnection()
        connection = conn.connect()

        try:
            cursor = connection.cursor()
            
            # Build UPDATE statement
            set_clause = ", ".join([f"{col} = %s" for col in updates.keys()])
            update_query = f"UPDATE {table} SET {set_clause} {where_clause}"
            
            cursor.execute(update_query, list(updates.values()))
            connection.commit()
            
            rows_updated = cursor.rowcount
            logger.info(f"Updated {rows_updated} rows in {table}")
            cursor.close()
            
            return LambdaResponse.success({
                "table": table,
                "updated_rows": rows_updated
            })

        finally:
            SnowflakeConnection.disconnect(connection)

    except json.JSONDecodeError:
        return LambdaResponse.error("Invalid JSON in request body", 400, "INVALID_JSON")
    except Exception as e:
        logger.error(f"Error updating data: {str(e)}")
        return LambdaResponse.error(f"Update operation failed: {str(e)}", 500, "UPDATE_ERROR")


def delete_data_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to delete data from Snowflake
    
    Event body:
    {
        "table": "table_name",
        "where_clause": "WHERE id = 1"
    }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        table = body.get("table")
        where_clause = body.get("where_clause", "")

        if not table:
            return LambdaResponse.error("table parameter is required", 400, "MISSING_TABLE")

        conn = SnowflakeConnection()
        connection = conn.connect()

        try:
            cursor = connection.cursor()
            delete_query = f"DELETE FROM {table} {where_clause}"
            
            cursor.execute(delete_query)
            connection.commit()
            
            rows_deleted = cursor.rowcount
            logger.info(f"Deleted {rows_deleted} rows from {table}")
            cursor.close()
            
            return LambdaResponse.success({
                "table": table,
                "deleted_rows": rows_deleted
            })

        finally:
            SnowflakeConnection.disconnect(connection)

    except json.JSONDecodeError:
        return LambdaResponse.error("Invalid JSON in request body", 400, "INVALID_JSON")
    except Exception as e:
        logger.error(f"Error deleting data: {str(e)}")
        return LambdaResponse.error(f"Delete operation failed: {str(e)}", 500, "DELETE_ERROR")


def get_table_schema_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to get the schema of a Snowflake table
    
    Event body:
    {
        "table": "table_name"
    }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        table = body.get("table")

        if not table:
            return LambdaResponse.error("table parameter is required", 400, "MISSING_TABLE")

        conn = SnowflakeConnection()
        connection = conn.connect()

        try:
            cursor = connection.cursor(DictCursor)
            schema_query = f"DESCRIBE TABLE {table}"
            
            cursor.execute(schema_query)
            schema = cursor.fetchall()
            
            # Format schema information
            columns = []
            for col in schema:
                columns.append({
                    "name": col.get("name"),
                    "type": col.get("type"),
                    "nullable": col.get("null?") == "Y",
                    "primary_key": col.get("primary key") == "Y",
                    "default": col.get("default"),
                })

            cursor.close()
            logger.info(f"Retrieved schema for table {table}")
            
            return LambdaResponse.success({
                "table": table,
                "columns": columns,
                "column_count": len(columns)
            })

        finally:
            SnowflakeConnection.disconnect(connection)

    except json.JSONDecodeError:
        return LambdaResponse.error("Invalid JSON in request body", 400, "INVALID_JSON")
    except Exception as e:
        logger.error(f"Error getting table schema: {str(e)}")
        return LambdaResponse.error(f"Schema retrieval failed: {str(e)}", 500, "SCHEMA_ERROR")


def list_tables_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to list all tables in Snowflake database
    """
    try:
        conn = SnowflakeConnection()
        connection = conn.connect()

        try:
            cursor = connection.cursor(DictCursor)
            list_query = "SHOW TABLES IN DATABASE"
            
            cursor.execute(list_query)
            tables = cursor.fetchall()
            
            table_names = [table.get("name") for table in tables]
            cursor.close()
            
            logger.info(f"Retrieved {len(table_names)} tables from database")
            return LambdaResponse.success({
                "tables": table_names,
                "count": len(table_names)
            })

        finally:
            SnowflakeConnection.disconnect(connection)

    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        return LambdaResponse.error(f"Table listing failed: {str(e)}", 500, "LIST_ERROR")


def bulk_insert_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for bulk insert operations
    
    Event body:
    {
        "table": "table_name",
        "file_path": "s3://bucket/path/to/file.csv",
        "file_format": "csv"  # csv, json, parquet
    }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        table = body.get("table")
        file_path = body.get("file_path")
        file_format = body.get("file_format", "csv").upper()

        if not table or not file_path:
            return LambdaResponse.error(
                "table and file_path parameters are required",
                400,
                "MISSING_PARAMETERS"
            )

        conn = SnowflakeConnection()
        connection = conn.connect()

        try:
            cursor = connection.cursor()
            
            # Snowflake COPY command for bulk loading
            copy_query = f"""
            COPY INTO {table}
            FROM '{file_path}'
            FILE_FORMAT = (TYPE = {file_format})
            ON_ERROR = 'SKIP_FILE'
            """
            
            cursor.execute(copy_query)
            connection.commit()
            
            # Get load status
            result = cursor.fetchone()
            logger.info(f"Bulk insert completed for {table}")
            cursor.close()
            
            return LambdaResponse.success({
                "table": table,
                "file_path": file_path,
                "status": "completed"
            }, 201)

        finally:
            SnowflakeConnection.disconnect(connection)

    except json.JSONDecodeError:
        return LambdaResponse.error("Invalid JSON in request body", 400, "INVALID_JSON")
    except Exception as e:
        logger.error(f"Error in bulk insert: {str(e)}")
        return LambdaResponse.error(f"Bulk insert failed: {str(e)}", 500, "BULK_INSERT_ERROR")


# ==================== Main Router ====================

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler that routes to appropriate function based on httpMethod and path
    """
    try:
        http_method = event.get("httpMethod", "").upper()
        path = event.get("path", "")

        logger.info(f"Received {http_method} request for path: {path}")

        # Route based on path
        if path.startswith("/snowflake/query"):
            if http_method == "POST":
                return execute_query_handler(event, context)

        elif path.startswith("/snowflake/insert"):
            if http_method == "POST":
                return insert_data_handler(event, context)

        elif path.startswith("/snowflake/update"):
            if http_method == "PUT":
                return update_data_handler(event, context)

        elif path.startswith("/snowflake/delete"):
            if http_method == "DELETE":
                return delete_data_handler(event, context)

        elif path.startswith("/snowflake/schema"):
            if http_method == "GET":
                return get_table_schema_handler(event, context)

        elif path.startswith("/snowflake/tables"):
            if http_method == "GET":
                return list_tables_handler(event, context)

        elif path.startswith("/snowflake/bulk-insert"):
            if http_method == "POST":
                return bulk_insert_handler(event, context)

        else:
            return LambdaResponse.error(
                f"Unsupported path: {path}",
                404,
                "NOT_FOUND"
            )

    except Exception as e:
        logger.error(f"Unhandled error in lambda_handler: {str(e)}")
        return LambdaResponse.error(
            "Internal server error",
            500,
            "INTERNAL_ERROR"
        )
