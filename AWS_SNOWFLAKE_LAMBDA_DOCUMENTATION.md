# AWS Snowflake Lambda Documentation

## Overview

`aws_snowflake_lambda.py` is a comprehensive AWS Lambda function that provides REST API endpoints for integrating with Snowflake data warehouse. It leverages the Snowflake Python connector to perform CRUD operations on tables, execute SQL queries, manage schema metadata, and handle bulk data loading from S3.

**Version:** 1.0.0  
**Language:** Python 3.7+  
**Dependencies:** snowflake-connector-python, boto3

---

## Table of Contents

1. [Architecture](#architecture)
2. [Core Components](#core-components)
3. [API Endpoints](#api-endpoints)
4. [Request/Response Format](#requestresponse-format)
5. [Error Handling](#error-handling)
6. [Deployment](#deployment)
7. [Configuration](#configuration)
8. [Usage Examples](#usage-examples)
9. [Authentication](#authentication)
10. [Logging](#logging)

---

## Architecture

### Design Pattern

The Lambda function uses a **path-based routing pattern** that dispatches requests based on HTTP method and API path. Each endpoint has a dedicated handler function that:

1. Parses the incoming event
2. Validates required parameters
3. Establishes a Snowflake connection
4. Executes the requested SQL operation
5. Returns a standardized response
6. Properly closes database connections

### Connection Management

The function implements a **connection manager pattern** to:
- Centralize connection configuration
- Handle connection lifecycle (connect/disconnect)
- Manage credentials via environment variables
- Log all connection events

### Data Flow

```
API Gateway (HTTP Request)
    ↓
lambda_handler (Router)
    ↓
Handler Function (Business Logic)
    ↓
SnowflakeConnection (Database Management)
    ↓
Snowflake Warehouse (Data Operations)
```

### Key Design Principles

- **Resource Cleanup**: All connections are explicitly closed in finally blocks
- **Error Isolation**: Each handler has its own try/except for granular error handling
- **Type Safety**: Full type hints for all function parameters
- **Logging**: Comprehensive logging for troubleshooting
- **Standardization**: Consistent response format across all endpoints

---

## Core Components

### 1. LambdaResponse Class

Helper class for standardized Lambda response formatting.

**Methods:**

#### `success(data, status_code=200)`
Returns a successful response with the provided data.

```python
response = LambdaResponse.success({
    "rows": [{"id": 1, "name": "data"}],
    "count": 1
}, 200)
```

**Response Structure:**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {...},
    "timestamp": "2025-01-15T10:30:00.000000"
  },
  "headers": {
    "Content-Type": "application/json"
  }
}
```

#### `error(message, status_code=400, error_code="ERROR")`
Returns an error response with error details.

**Parameters:**
- `message` (str): Human-readable error message
- `status_code` (int): HTTP status code (default: 400)
- `error_code` (str): Machine-readable error code (default: "ERROR")

**Response Structure:**
```json
{
  "statusCode": 400,
  "body": {
    "success": false,
    "error": "Table not found in database",
    "error_code": "NOT_FOUND",
    "timestamp": "2025-01-15T10:30:00.000000"
  },
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### 2. SnowflakeConnection Class

Manages Snowflake database connections with configuration from environment variables.

**Attributes:**
```python
account         # Snowflake account ID (e.g., xy12345)
user            # Database username
password        # Database password
database        # Default database name
schema          # Default schema name
warehouse       # Compute warehouse name
role            # Database role (default: SYSADMIN)
```

**Methods:**

#### `connect() -> SnowflakeConnection`
Establishes a connection to Snowflake.

```python
conn = SnowflakeConnection()
connection = conn.connect()
```

**Raises:**
- `Exception`: Connection error with details

**Parameters Used:**
- `account`: Snowflake account identifier
- `user`: Database username
- `password`: Database password
- `database`: Default database
- `schema`: Default schema
- `warehouse`: Compute warehouse
- `role`: Database role

#### `disconnect(connection) -> None`
Closes a Snowflake connection safely.

```python
SnowflakeConnection.disconnect(connection)
```

**Features:**
- Gracefully handles already-closed connections
- Logs disconnection events
- Prevents connection leaks

---

## API Endpoints

All endpoints use path-based routing and are designed to work with AWS API Gateway.

### Data Query Operations

#### Execute Query
**Endpoint:** `POST /snowflake/query`

Executes arbitrary SQL queries against Snowflake.

**Request Body:**
```json
{
  "query": "SELECT * FROM USERS WHERE active = true LIMIT 100",
  "return_type": "dict"
}
```

**Parameters:**
- `query` (string, required): SQL query to execute
- `return_type` (string, optional): "dict" or "list" (default: "list")
  - "dict": Returns results as list of dictionaries with column names
  - "list": Returns results as list of tuples

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "rows": [
        {
          "ID": 1,
          "NAME": "John",
          "EMAIL": "john@example.com"
        },
        {
          "ID": 2,
          "NAME": "Jane",
          "EMAIL": "jane@example.com"
        }
      ],
      "count": 2
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Error Codes:**
- `400`: Missing query parameter or invalid JSON
- `500`: SQL syntax error or execution failure

**Query Examples:**
```sql
-- Simple select
SELECT * FROM ORDERS LIMIT 10;

-- Aggregate query
SELECT PRODUCT, SUM(AMOUNT) as total FROM SALES GROUP BY PRODUCT;

-- Join query
SELECT o.ID, o.ORDER_DATE, c.NAME 
FROM ORDERS o 
JOIN CUSTOMERS c ON o.CUSTOMER_ID = c.ID;

-- CTE query
WITH recent_orders AS (
  SELECT * FROM ORDERS WHERE ORDER_DATE > CURRENT_DATE - 30
)
SELECT * FROM recent_orders;
```

---

#### List Tables
**Endpoint:** `GET /snowflake/tables`

Lists all tables in the default database.

**Query Parameters:** None

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "tables": [
        "CUSTOMERS",
        "ORDERS",
        "PRODUCTS",
        "ORDER_ITEMS",
        "INVENTORY"
      ],
      "count": 5
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Error Codes:**
- `500`: Database connection or query execution error

---

#### Get Table Schema
**Endpoint:** `GET /snowflake/schema`

Retrieves the schema/structure of a specific table.

**Request Body:**
```json
{
  "table": "CUSTOMERS"
}
```

**Parameters:**
- `table` (string, required): Table name (case-insensitive, will be uppercased)

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "table": "CUSTOMERS",
      "columns": [
        {
          "name": "ID",
          "type": "NUMBER(38,0)",
          "nullable": false,
          "primary_key": true,
          "default": null
        },
        {
          "name": "NAME",
          "type": "VARCHAR(255)",
          "nullable": false,
          "primary_key": false,
          "default": null
        },
        {
          "name": "EMAIL",
          "type": "VARCHAR(255)",
          "nullable": true,
          "primary_key": false,
          "default": null
        },
        {
          "name": "CREATED_AT",
          "type": "TIMESTAMP_NTZ(9)",
          "nullable": false,
          "primary_key": false,
          "default": "CURRENT_TIMESTAMP()"
        }
      ],
      "column_count": 4
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Error Codes:**
- `400`: Missing table parameter
- `500`: Table doesn't exist or query error

---

### Data Modification Operations

#### Insert Data
**Endpoint:** `POST /snowflake/insert`

Inserts one or more rows into a table.

**Request Body:**
```json
{
  "table": "CUSTOMERS",
  "columns": ["ID", "NAME", "EMAIL"],
  "values": [
    [1, "John Doe", "john@example.com"],
    [2, "Jane Smith", "jane@example.com"],
    [3, "Bob Johnson", "bob@example.com"]
  ]
}
```

**Parameters:**
- `table` (string, required): Target table name
- `columns` (array, required): Column names
- `values` (array, required): Array of value arrays (each inner array is one row)

**Response (201 Created):**
```json
{
  "statusCode": 201,
  "body": {
    "success": true,
    "data": {
      "table": "CUSTOMERS",
      "inserted_rows": 3
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Error Codes:**
- `400`: Missing required parameters
- `500`: SQL error, constraint violation, or permission denied

**Example with Different Data Types:**
```json
{
  "table": "ORDERS",
  "columns": ["ORDER_ID", "CUSTOMER_ID", "AMOUNT", "ORDER_DATE", "NOTES"],
  "values": [
    [101, 1, 150.50, "2025-01-15", "Rush delivery"],
    [102, 2, 299.99, "2025-01-15", null]
  ]
}
```

---

#### Update Data
**Endpoint:** `PUT /snowflake/update`

Updates existing rows in a table.

**Request Body:**
```json
{
  "table": "CUSTOMERS",
  "updates": {
    "EMAIL": "newemail@example.com",
    "UPDATED_AT": "2025-01-15"
  },
  "where_clause": "WHERE ID = 1"
}
```

**Parameters:**
- `table` (string, required): Target table name
- `updates` (object, required): Column-value pairs to update
- `where_clause` (string, required): WHERE condition to identify rows

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "table": "CUSTOMERS",
      "updated_rows": 1
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Error Codes:**
- `400`: Missing required parameters
- `500`: SQL error or execution failure

**WHERE Clause Examples:**
```
WHERE ID = 5
WHERE NAME LIKE '%john%'
WHERE CREATED_AT > '2025-01-01'
WHERE STATUS = 'ACTIVE' AND AMOUNT > 100
WHERE ID IN (1, 2, 3, 4, 5)
```

**Safety Considerations:**
- Omit `where_clause` to update ALL rows (not recommended)
- Always verify your WHERE clause before executing
- Consider using transactions for critical updates

---

#### Delete Data
**Endpoint:** `DELETE /snowflake/delete`

Deletes rows from a table.

**Request Body:**
```json
{
  "table": "CUSTOMERS",
  "where_clause": "WHERE ID = 1"
}
```

**Parameters:**
- `table` (string, required): Target table name
- `where_clause` (string, optional): WHERE condition to identify rows

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "table": "CUSTOMERS",
      "deleted_rows": 1
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Error Codes:**
- `400`: Missing table parameter
- `500`: SQL error or constraint violation

**WHERE Clause Examples:**
```
WHERE ID = 5
WHERE STATUS = 'INACTIVE'
WHERE CREATED_AT < DATE_SUB(CURRENT_DATE, 365)
WHERE LAST_UPDATED IS NULL
```

**⚠️ WARNING:** Deleting without a WHERE clause will delete ALL rows from the table!

---

### Bulk Operations

#### Bulk Insert from S3
**Endpoint:** `POST /snowflake/bulk-insert`

Bulk loads data from S3 into a Snowflake table using the COPY command.

**Request Body:**
```json
{
  "table": "CUSTOMERS",
  "file_path": "s3://my-bucket/data/customers.csv",
  "file_format": "csv"
}
```

**Parameters:**
- `table` (string, required): Target table name
- `file_path` (string, required): S3 path to the file
- `file_format` (string, optional): File format - "csv", "json", or "parquet" (default: "csv")

**Response (201 Created):**
```json
{
  "statusCode": 201,
  "body": {
    "success": true,
    "data": {
      "table": "CUSTOMERS",
      "file_path": "s3://my-bucket/data/customers.csv",
      "status": "completed"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Error Codes:**
- `400`: Missing required parameters
- `500`: S3 access error, file format error, or SQL error

**S3 File Formats:**

**CSV Example (customers.csv):**
```csv
ID,NAME,EMAIL,CREATED_AT
1,John Doe,john@example.com,2025-01-01
2,Jane Smith,jane@example.com,2025-01-02
3,Bob Johnson,bob@example.com,2025-01-03
```

**JSON Example (customers.json):**
```json
{
  "ID": 1,
  "NAME": "John Doe",
  "EMAIL": "john@example.com",
  "CREATED_AT": "2025-01-01"
}
{
  "ID": 2,
  "NAME": "Jane Smith",
  "EMAIL": "jane@example.com",
  "CREATED_AT": "2025-01-02"
}
```

**Parquet Example:**
- Binary columnar format (generated from tools like Pandas, Apache Spark)
- Most efficient for large datasets

**Performance Tips:**
- CSV: Best for small to medium files (< 1 GB)
- JSON: Good for nested data, slightly larger than CSV
- Parquet: Best for large files and optimal compression
- Stage files in S3 in same region as Snowflake for faster loading
- Use multiple files instead of one large file for parallel loading

**Required Snowflake Privileges:**
- `USAGE` on database and schema
- `INSERT` on target table
- `READ` on S3 external stage (or AWS credentials configured)

---

## Request/Response Format

### Request Format

All requests follow the AWS Lambda/API Gateway event model:

```python
{
  "httpMethod": "POST",
  "path": "/snowflake/query",
  "body": "{\"query\": \"SELECT * FROM USERS\"}",
  "headers": {
    "Content-Type": "application/json"
  },
  "queryStringParameters": None,
  "pathParameters": None
}
```

### Response Format

All responses follow a standardized structure:

```python
{
  "statusCode": 200,
  "body": "{...JSON...}",  # String format for API Gateway
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/PUT/DELETE request |
| 201 | Created | Successful POST request (data insertion) |
| 400 | Bad Request | Invalid input, missing parameters, invalid JSON |
| 404 | Not Found | Endpoint not found |
| 500 | Internal Server Error | SQL error, connection failure, permission denied |

---

## Error Handling

### Error Response Structure

```json
{
  "statusCode": 400,
  "body": {
    "success": false,
    "error": "Query parameter is required",
    "error_code": "MISSING_QUERY",
    "timestamp": "2025-01-15T10:30:00.000000"
  },
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### Error Codes Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| MISSING_QUERY | 400 | Query parameter not provided |
| MISSING_PARAMETERS | 400 | Required parameters missing |
| MISSING_TABLE | 400 | Table parameter not provided |
| INVALID_JSON | 400 | Malformed JSON in request body |
| QUERY_ERROR | 500 | SQL syntax error or execution failure |
| INSERT_ERROR | 500 | Data insertion failed |
| UPDATE_ERROR | 500 | Data update failed |
| DELETE_ERROR | 500 | Data deletion failed |
| SCHEMA_ERROR | 500 | Schema retrieval failed |
| LIST_ERROR | 500 | Table listing failed |
| BULK_INSERT_ERROR | 500 | Bulk load failed |
| NOT_FOUND | 404 | Endpoint not found |
| INTERNAL_ERROR | 500 | Unhandled exception |

### Error Handling Strategy

1. **Input Validation** → 400 with specific error code
2. **Resource Not Found** → 404 or 400 depending on context
3. **SQL Errors** → 500 with error details
4. **Connection Errors** → 500 with connection error message
5. **Unhandled Exceptions** → 500 INTERNAL_ERROR

**Example Error Handling:**
```python
try:
    body = json.loads(event.get("body", "{}"))
except json.JSONDecodeError:
    return LambdaResponse.error(
        "Invalid JSON in request body", 
        400, 
        "INVALID_JSON"
    )
except Exception as e:
    logger.error(f"Error: {str(e)}")
    return LambdaResponse.error(
        str(e), 
        500, 
        "INTERNAL_ERROR"
    )
```

### Connection Error Handling

The function gracefully handles connection issues:

```python
try:
    connection = conn.connect()
    # ... execute query ...
finally:
    SnowflakeConnection.disconnect(connection)
```

---

## Deployment

### Prerequisites

1. AWS Account with Lambda permissions
2. Snowflake account with API access
3. Python 3.7+ runtime
4. snowflake-connector-python installed

### Step 1: Prepare the Package

```bash
# Create deployment directory
mkdir lambda-deployment
cd lambda-deployment

# Copy source files
cp aws_snowflake_lambda.py .

# Install dependencies (this is large!)
pip install snowflake-connector-python -t .
```

**Note:** The Snowflake connector package is large (~150 MB). You may need to use Lambda Layers for optimization.

### Step 2: Using Lambda Layers (Recommended)

```bash
# Create layers directory
mkdir python
cd python

# Install dependencies
pip install snowflake-connector-python -t .

# Zip the layer
cd ..
zip -r snowflake-layer.zip python

# Upload to Lambda
aws lambda publish-layer-version \
  --layer-name snowflake-connector \
  --zip-file fileb://snowflake-layer.zip \
  --compatible-runtimes python3.11
```

### Step 3: Create Lambda Function

**Using AWS Console:**
1. Navigate to Lambda → Create Function
2. Runtime: Python 3.11
3. Handler: `aws_snowflake_lambda.lambda_handler`
4. Add layer: snowflake-connector
5. Upload ZIP file with lambda code

**Using AWS CLI:**
```bash
zip -r lambda-deployment.zip aws_snowflake_lambda.py

aws lambda create-function \
  --function-name snowflake-api \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler aws_snowflake_lambda.lambda_handler \
  --zip-file fileb://lambda-deployment.zip \
  --layers arn:aws:lambda:REGION:ACCOUNT:layer:snowflake-connector:1 \
  --timeout 60 \
  --memory-size 512
```

### Step 4: Configure API Gateway

1. Create REST API in API Gateway
2. Create resources:
   - `/snowflake`
     - `/query` → POST
     - `/insert` → POST
     - `/update` → PUT
     - `/delete` → DELETE
     - `/schema` → GET
     - `/tables` → GET
     - `/bulk-insert` → POST
3. Integrate all methods with Lambda function
4. Deploy to stage (dev, prod, etc.)

**API Gateway Integration:**
```
POST /snowflake/query → execute_query_handler
POST /snowflake/insert → insert_data_handler
PUT /snowflake/update → update_data_handler
DELETE /snowflake/delete → delete_data_handler
GET /snowflake/schema → get_table_schema_handler
GET /snowflake/tables → list_tables_handler
POST /snowflake/bulk-insert → bulk_insert_handler
```

### Step 5: Set Environment Variables

In Lambda Configuration → Environment Variables:
```
SNOWFLAKE_ACCOUNT=xy12345
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=ANALYTICS
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=TRANSFORMER
```

### Step 6: Configure IAM Role

Lambda execution role needs:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:*:*:secret:snowflake/*"
    }
  ]
}
```

---

## Configuration

### Environment Variables

Required environment variables in Lambda:

| Variable | Description | Example |
|----------|-------------|---------|
| SNOWFLAKE_ACCOUNT | Account ID | `xy12345` |
| SNOWFLAKE_USER | Username | `api_user` |
| SNOWFLAKE_PASSWORD | Password | `SecurePass123!` |
| SNOWFLAKE_DATABASE | Database name | `ANALYTICS` |
| SNOWFLAKE_SCHEMA | Schema name | `PUBLIC` |
| SNOWFLAKE_WAREHOUSE | Warehouse name | `COMPUTE_WH` |
| SNOWFLAKE_ROLE | Database role | `TRANSFORMER` |

### Secure Configuration with AWS Secrets Manager

**Recommended for Production:**

1. Store credentials in Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name snowflake/credentials \
  --secret-string '{
    "account": "xy12345",
    "user": "api_user",
    "password": "SecurePass123!",
    "database": "ANALYTICS",
    "schema": "PUBLIC",
    "warehouse": "COMPUTE_WH",
    "role": "TRANSFORMER"
  }'
```

2. Modify Lambda to use Secrets Manager:
```python
import boto3
import json
import os

secrets_client = boto3.client('secretsmanager')

def get_snowflake_config():
    secret = secrets_client.get_secret_value(
        SecretId=os.getenv('SNOWFLAKE_SECRET_NAME', 'snowflake/credentials')
    )
    return json.loads(secret['SecretString'])

# Usage in SnowflakeConnection.__init__
config = get_snowflake_config()
self.account = config['account']
self.user = config['user']
# ... etc
```

### Lambda Configuration

Recommended settings:
- **Runtime:** Python 3.11
- **Memory:** 512 MB (for Snowflake connector)
- **Timeout:** 60 seconds (queries may be slow)
- **Ephemeral Storage:** 512 MB
- **Architecture:** x86_64

### Connection Pool Configuration

For high-throughput scenarios, consider implementing connection pooling:

```python
from sqlalchemy import create_engine
from snowflake.sqlalchemy import URL

# Create engine with connection pool
engine = create_engine(URL(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    role=os.getenv("SNOWFLAKE_ROLE"),
), pool_pre_ping=True, pool_recycle=3600)
```

---

## Usage Examples

### Example 1: Execute SELECT Query via cURL

```bash
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/prod/snowflake/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM CUSTOMERS LIMIT 10",
    "return_type": "dict"
  }'
```

### Example 2: Insert Data via Python

```python
import requests
import json

api_url = "https://your-api.execute-api.us-east-1.amazonaws.com/prod"

insert_payload = {
    "table": "CUSTOMERS",
    "columns": ["ID", "NAME", "EMAIL"],
    "values": [
        [1, "John Doe", "john@example.com"],
        [2, "Jane Smith", "jane@example.com"]
    ]
}

response = requests.post(
    f"{api_url}/snowflake/insert",
    headers={"Content-Type": "application/json"},
    json=insert_payload
)

result = response.json()
print(f"Inserted {result['data']['inserted_rows']} rows")
```

### Example 3: Update Data via JavaScript

```javascript
const apiUrl = 'https://your-api.execute-api.us-east-1.amazonaws.com/prod';

const updatePayload = {
  table: 'CUSTOMERS',
  updates: {
    EMAIL: 'newemail@example.com',
    UPDATED_AT: '2025-01-15'
  },
  where_clause: 'WHERE ID = 1'
};

fetch(`${apiUrl}/snowflake/update`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(updatePayload)
})
.then(res => res.json())
.then(data => {
  console.log(`Updated ${data.data.updated_rows} rows`);
});
```

### Example 4: Get Table Schema via Python

```python
import requests

api_url = "https://your-api.execute-api.us-east-1.amazonaws.com/prod"

response = requests.get(
    f"{api_url}/snowflake/schema",
    headers={"Content-Type": "application/json"},
    json={"table": "ORDERS"}
)

schema = response.json()['data']
print(f"Table: {schema['table']}")
for col in schema['columns']:
    nullable = "NULL" if col['nullable'] else "NOT NULL"
    print(f"  {col['name']} {col['type']} {nullable}")
```

### Example 5: Bulk Load from S3

```bash
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/prod/snowflake/bulk-insert \
  -H "Content-Type: application/json" \
  -d '{
    "table": "CUSTOMERS",
    "file_path": "s3://my-data-bucket/exports/customers_2025.csv",
    "file_format": "csv"
  }'
```

### Example 6: Delete Records

```python
import requests

api_url = "https://your-api.execute-api.us-east-1.amazonaws.com/prod"

delete_payload = {
    "table": "CUSTOMERS",
    "where_clause": "WHERE CREATED_AT < '2024-01-01'"
}

response = requests.delete(
    f"{api_url}/snowflake/delete",
    headers={"Content-Type": "application/json"},
    json=delete_payload
)

result = response.json()
print(f"Deleted {result['data']['deleted_rows']} rows")
```

---

## Authentication

### Snowflake Authentication Methods

The function supports Snowflake's native authentication using username/password:

**Authentication Flow:**
```
Username + Password
     ↓
Snowflake Server
     ↓
Session Token
     ↓
All Subsequent Requests Use Token
```

### Environment Variable Setup

1. **Create Snowflake User:**
```sql
CREATE USER api_user PASSWORD = 'SecurePassword123!';
GRANT USAGE ON WAREHOUSE compute_wh TO api_user;
GRANT USAGE ON DATABASE analytics TO api_user;
GRANT USAGE ON SCHEMA public TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics.public TO api_user;
```

2. **Set Lambda Environment Variables:**
   - SNOWFLAKE_ACCOUNT: Your account ID (from URL: https://`xy12345`.snowflakecomputing.com)
   - SNOWFLAKE_USER: api_user
   - SNOWFLAKE_PASSWORD: SecurePassword123!
   - SNOWFLAKE_DATABASE: analytics
   - SNOWFLAKE_SCHEMA: public
   - SNOWFLAKE_WAREHOUSE: compute_wh

### Advanced: API Gateway Authorization

Add API Gateway authorizer for additional security:

```python
# Custom authorizer function
def authorize(event, context):
    token = event['authorizationToken']
    
    # Validate token against your auth service
    if is_valid_token(token):
        return generate_policy('user', 'Allow', event['methodArn'])
    
    raise Exception('Unauthorized')
```

### Adding Authorization to Requests

```javascript
// Client-side with API key
const apiKey = 'your-api-key';
fetch('https://api.example.com/snowflake/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': apiKey
  },
  body: JSON.stringify({
    query: "SELECT * FROM CUSTOMERS"
  })
});
```

---

## Logging

### CloudWatch Logs

All operations are logged to CloudWatch with structured logging:

```python
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logger.info("Successfully connected to Snowflake")
logger.error(f"Failed to execute query: {str(e)}")
logger.warning(f"Query returned {len(data)} rows")
```

### Log Examples

**Successful Query Execution:**
```
[2025-01-15 10:30:00.123] INFO - Received POST request for path: /snowflake/query
[2025-01-15 10:30:00.234] INFO - Successfully connected to Snowflake
[2025-01-15 10:30:00.567] INFO - Query executed successfully, returned 25 rows
[2025-01-15 10:30:00.589] INFO - Snowflake connection closed
```

**Failed Insert Operation:**
```
[2025-01-15 10:30:15.123] INFO - Received POST request for path: /snowflake/insert
[2025-01-15 10:30:15.234] INFO - Successfully connected to Snowflake
[2025-01-15 10:30:15.345] ERROR - Error inserting data: Unique constraint violation
[2025-01-15 10:30:15.356] INFO - Snowflake connection closed
```

### CloudWatch Insights Queries

**Find all errors in the last hour:**
```
fields @timestamp, @message, error_code
| filter @message like /ERROR/
| stats count() by error_code
```

**Find slowest queries:**
```
fields @duration, @message
| filter @message like /Query executed/
| stats avg(@duration) as avg_ms, max(@duration) as max_ms by @message
```

**Count operations by endpoint:**
```
fields path
| filter @message like /Received/
| stats count() as request_count by path
```

**Find connection errors:**
```
fields @timestamp, @message
| filter @message like /Failed to connect/
| stats count() as error_count by @message
```

### Log Levels

- **INFO:** General operational events (connections, operations completed)
- **WARNING:** Unexpected but recoverable conditions
- **ERROR:** Error conditions with full context
- **DEBUG:** Detailed diagnostic info (not typically enabled in production)

---

## Performance Optimization

### Query Optimization

1. **Use LIMIT for large datasets:**
```sql
SELECT * FROM HUGE_TABLE LIMIT 1000;  -- Good
SELECT * FROM HUGE_TABLE;              -- Bad if millions of rows
```

2. **Use WHERE clauses:**
```sql
SELECT * FROM ORDERS WHERE YEAR = 2025;  -- Good
SELECT * FROM ORDERS;                     -- Bad
```

3. **Select only needed columns:**
```sql
SELECT ID, NAME, EMAIL FROM CUSTOMERS;  -- Good
SELECT * FROM CUSTOMERS;                 -- Bad
```

### Lambda Optimization

1. **Memory Configuration:**
   - 512 MB recommended for Snowflake operations
   - More memory = faster CPU = faster execution
   - Consider 1024 MB for heavy operations

2. **Timeout Configuration:**
   - Set to 60 seconds for queries
   - Long-running analytics may need 300 seconds

3. **Connection Reuse:**
   - Snowflake driver caches connections
   - Warm connections faster than cold starts

### Bulk Load Performance

1. **Use Parquet format for large files:**
   - Most compressed format
   - Fastest ingestion speed
   - Ideal for > 1 GB files

2. **Split large files:**
   - 10 GB file → 10x 1 GB files
   - Enables parallel loading
   - Faster overall ingestion

3. **Use external stage:**
```sql
-- Create stage in same region as S3 bucket
CREATE STAGE my_stage URL = 's3://my-bucket/path/' CREDENTIALS = (...);

-- Then reference in bulk load
COPY INTO my_table FROM @my_stage FILES = ('*.parquet');
```

---

## Best Practices

### 1. Error Handling
- Always validate input parameters
- Catch and log all exceptions
- Return meaningful error messages
- Use specific error codes

### 2. Security
- Store credentials in AWS Secrets Manager
- Use IAM roles instead of hardcoded credentials
- Validate all SQL input to prevent injection
- Use parameterized queries when possible
- Restrict Snowflake user privileges to minimum needed

### 3. Resource Management
- Always close connections in finally blocks
- Set appropriate Lambda timeout values
- Monitor CloudWatch metrics
- Use Lambda Layers for large dependencies

### 4. Data Validation
- Validate data types before insertion
- Check for NULL values in NOT NULL columns
- Verify foreign key constraints
- Test updates/deletes with WHERE clauses first

### 5. Monitoring
- Set CloudWatch alarms for error rates
- Monitor Lambda duration and memory usage
- Track API Gateway response times
- Alert on failed Snowflake connections

---

## Troubleshooting

### Issue: "Failed to connect to Snowflake"

**Causes:**
- Invalid account ID
- Wrong username/password
- Account suspended
- Network connectivity issue
- IP whitelisting restrictions

**Solution:**
```bash
# Verify credentials work locally
python -c "
import snowflake.connector
conn = snowflake.connector.connect(
    account='xy12345',
    user='api_user',
    password='password',
    database='ANALYTICS'
)
print('Connected!')
"

# Check Lambda environment variables
aws lambda get-function-configuration --function-name snowflake-api | jq '.Environment.Variables'
```

### Issue: "Permission denied" errors

**Causes:**
- User lacks required privileges
- Role not properly granted
- Object doesn't exist in expected schema

**Solution:**
```sql
-- Grant minimum required privileges
GRANT USAGE ON WAREHOUSE compute_wh TO api_user;
GRANT USAGE ON DATABASE analytics TO api_user;
GRANT USAGE ON SCHEMA public TO api_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics.public TO api_user;

-- Verify privileges
SHOW GRANTS TO USER api_user;
```

### Issue: Timeout (Lambda execution timeout)

**Causes:**
- Query too slow
- Lambda timeout too short
- Network latency

**Solution:**
```python
# Increase Lambda timeout to 60 seconds in configuration
# Optimize query with LIMIT and WHERE clauses
# Move to larger Lambda memory allocation

# Check query performance in Snowflake
-- View query history
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY 
WHERE USER_NAME = 'API_USER' 
ORDER BY START_TIME DESC 
LIMIT 10;
```

### Issue: Large response sizes

**Causes:**
- Returning too much data
- API Gateway payload limit (6 MB)

**Solution:**
```json
// Use pagination/LIMIT in queries
{
  "query": "SELECT * FROM CUSTOMERS LIMIT 1000",
  "return_type": "dict"
}

// Or use offset for pagination
{
  "query": "SELECT * FROM CUSTOMERS LIMIT 1000 OFFSET 5000",
  "return_type": "dict"
}
```

### Issue: Slow bulk inserts from S3

**Causes:**
- Large file size
- Inefficient file format
- S3 bucket in different region

**Solution:**
- Split file into smaller chunks
- Use Parquet format instead of CSV
- Ensure S3 bucket in same region as Snowflake
- Enable parallel COPY:
```sql
COPY INTO table
FROM 's3://bucket/path/'
FILE_FORMAT = (TYPE = CSV)
PARALLEL = 8;
```

---

## Advanced Usage

### Custom SQL Builder

Create type-safe query builder:

```python
class QueryBuilder:
    def __init__(self, table):
        self.table = table
        self.columns = []
        self.conditions = []
    
    def select(self, *cols):
        self.columns = list(cols)
        return self
    
    def where(self, condition):
        self.conditions.append(condition)
        return self
    
    def build(self):
        cols = ", ".join(self.columns) if self.columns else "*"
        query = f"SELECT {cols} FROM {self.table}"
        if self.conditions:
            query += " WHERE " + " AND ".join(self.conditions)
        return query

# Usage
query = QueryBuilder("CUSTOMERS") \
    .select("ID", "NAME", "EMAIL") \
    .where("CREATED_AT > '2025-01-01'") \
    .where("STATUS = 'ACTIVE'") \
    .build()
```

### Audit Logging

Log all data modifications:

```python
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
audit_table = dynamodb.Table('snowflake-audit')

def audit_operation(operation, table, rows_affected, user=None):
    audit_table.put_item(Item={
        'timestamp': datetime.utcnow().isoformat(),
        'operation': operation,
        'table': table,
        'rows_affected': rows_affected,
        'user': user or 'lambda-function'
    })

# Usage in handlers
if result.success:
    audit_operation('INSERT', 'CUSTOMERS', 3)
```

### Data Validation

Add validation before insert/update:

```python
def validate_customer_data(data):
    errors = []
    
    if not data.get('NAME'):
        errors.append('NAME is required')
    
    if not data.get('EMAIL'):
        errors.append('EMAIL is required')
    
    if '@' not in data.get('EMAIL', ''):
        errors.append('Invalid EMAIL format')
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True}

# Usage
validation = validate_customer_data(row)
if not validation['valid']:
    return LambdaResponse.error(
        str(validation['errors']), 
        400, 
        "VALIDATION_ERROR"
    )
```

---

## Additional Resources

- [Snowflake Python Connector Documentation](https://docs.snowflake.com/en/developer-guide/python-connector/)
- [Snowflake SQL Reference](https://docs.snowflake.com/en/sql-reference/)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/)
- [AWS API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)
- [Snowflake Cost Optimization](https://docs.snowflake.com/en/user-guide/cost-optimization.html)

---

## Support & Maintenance

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-15 | Initial release |

### Contributing

To extend this Lambda function:
1. Add new handler function
2. Register in `lambda_handler` router
3. Update API Gateway resources
4. Test in dev environment
5. Deploy to production

### Contact

For issues or questions, refer to the project documentation or contact your Snowflake administrator.
