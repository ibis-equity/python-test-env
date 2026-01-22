# FastAPI AWS Lambda Integration - Complete Function & Method Reference

## Table of Contents

1. [FastAPI Application (fast_api.py)](#fastapi-application)
2. [AWS Gateway Integration (aws_gateway_integration.py)](#aws-gateway-integration)
3. [Data Models](#data-models)
4. [API Endpoints](#api-endpoints)
5. [Utility Classes](#utility-classes)
6. [Usage Examples](#usage-examples)
7. [Integration Flow](#integration-flow)

---

## FastAPI Application

### File: `src/fast_api.py`

This is the main FastAPI application that serves as the REST API for both local development and AWS Lambda deployment.

---

### **Data Models**

#### `class Item(BaseModel)`

Pydantic model representing an item to be created or stored.

**Purpose**: Validates incoming request data for item creation

**Attributes**:
```python
name: str
    - Type: String
    - Constraints: 1-100 characters
    - Description: Name of the item
    - Required: Yes
    
description: Optional[str] = None
    - Type: String or None
    - Constraints: 0-500 characters
    - Description: Detailed description of the item
    - Required: No
    
status: Optional[str] = "created"
    - Type: String or None
    - Default: "created"
    - Description: Current status of the item
    - Required: No
```

**Example Usage**:
```python
# Creating an Item instance
item = Item(
    name="Sample Item",
    description="This is a sample item",
    status="active"
)
```

**Validation Rules**:
- `name` must be between 1-100 characters
- `description` can be at most 500 characters
- Invalid data will raise a 422 Unprocessable Entity error

---

#### `class ItemResponse(BaseModel)`

Pydantic model for API responses containing item information.

**Purpose**: Formats item data for API responses with additional metadata

**Attributes**:
```python
item_id: Optional[int] = None
    - Type: Integer or None
    - Description: Unique identifier for the item
    - Required: No
    
name: Optional[str] = None
    - Type: String or None
    - Description: Name of the item
    - Required: No
    
description: Optional[str] = None
    - Type: String or None
    - Description: Description of the item
    - Required: No
    
status: str
    - Type: String
    - Description: Status of the operation or item
    - Required: Yes (always included)
    
query: Optional[str] = None
    - Type: String or None
    - Description: Query parameter if provided in request
    - Required: No
```

**Example Response**:
```json
{
    "item_id": 42,
    "name": "Sample Item",
    "description": "This is a sample item",
    "status": "retrieved",
    "query": "search_term"
}
```

---

#### `class HealthResponse(BaseModel)`

Pydantic model for health check endpoint responses.

**Purpose**: Standardizes health check response format

**Attributes**:
```python
status: str
    - Type: String
    - Description: Health status of the API
    - Required: Yes
    - Typical Values: "healthy", "degraded", "unhealthy"
    
version: str
    - Type: String
    - Default: "1.0.0"
    - Description: API version
    - Required: No
```

**Example Response**:
```json
{
    "status": "healthy",
    "version": "1.0.0"
}
```

---

### **Endpoint Functions**

#### `async def read_root()`

**Route**: `GET /`

**Tags**: General

**Purpose**: Welcome endpoint that returns API information

**Parameters**: None

**Returns**: 
```python
dict: {
    "message": "Welcome to the Python API",
    "endpoints": {
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/api/v1/openapi.json"
    }
}
```

**Response Code**: 200 OK

**Use Cases**:
- Health check (simple verification that API is running)
- Endpoint discovery
- Client integration verification

**Example Request**:
```bash
curl http://localhost:8000/
```

**Example Response**:
```json
{
    "message": "Welcome to the Python API",
    "endpoints": {
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/api/v1/openapi.json"
    }
}
```

---

#### `async def read_item(item_id, q)`

**Route**: `GET /api/items/{item_id}`

**Tags**: Items

**Purpose**: Retrieve an item by its ID with optional query parameter

**Parameters**:
```python
item_id: int
    - Location: URL path
    - Constraints: Must be greater than 0
    - Description: The unique identifier of the item to retrieve
    - Type: Integer
    - Required: Yes
    
q: Optional[str] = None
    - Location: Query string
    - Constraints: 1-50 characters if provided
    - Description: Optional search query parameter
    - Type: String or None
    - Required: No
```

**Returns**: `ItemResponse`
```python
{
    "item_id": <int>,
    "query": <str or None>,
    "name": f"Item {item_id}",
    "description": f"Description for item {item_id}",
    "status": "retrieved"
}
```

**Response Code**: 200 OK

**Error Responses**:
- 422 Unprocessable Entity: If `item_id` is not > 0
- 422 Unprocessable Entity: If `q` is longer than 50 characters

**Use Cases**:
- Fetch specific item information
- Search for items with query parameters
- Pagination support via query

**Example Requests**:
```bash
# Basic item retrieval
curl http://localhost:8000/api/items/1

# With query parameter
curl http://localhost:8000/api/items/42?q=search_term

# With AWS Lambda
curl https://api-id.execute-api.us-east-1.amazonaws.com/prod/api/items/42?q=test
```

**Example Response**:
```json
{
    "item_id": 42,
    "query": "search_term",
    "name": "Item 42",
    "description": "Description for item 42",
    "status": "retrieved"
}
```

**Implementation Details**:
- `item_id` must be positive (validated by FastAPI)
- Query parameter is optional
- Response always includes status "retrieved"
- Demonstrates path parameters and query string handling

---

#### `async def create_item(item)`

**Route**: `POST /api/items/`

**Tags**: Items

**Purpose**: Create a new item with provided name and optional description

**Parameters**:
```python
item: Item
    - Location: Request body (JSON)
    - Required: Yes
    - Type: Item model
    - Schema:
        {
            "name": "string (1-100 chars)",
            "description": "string (0-500 chars, optional)",
            "status": "string (optional, default: 'created')"
        }
```

**Returns**: `ItemResponse`
```python
{
    "item_id": None,  # Not set in this mock
    "name": <item.name>,
    "description": <item.description>,
    "status": <item.status or "created">,
    "query": None
}
```

**Response Code**: 201 Created

**Error Responses**:
- 400 Bad Request: If request body is invalid
- 422 Unprocessable Entity: If validation fails
  - `name` is empty or > 100 characters
  - `description` is > 500 characters

**Use Cases**:
- Create new items in the system
- Accept user input for item creation
- Demonstrate POST request handling

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/items/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Item",
    "description": "A new item description",
    "status": "draft"
  }'
```

**Request Body**:
```json
{
    "name": "New Item",
    "description": "A new item description",
    "status": "draft"
}
```

**Example Response**:
```json
{
    "item_id": null,
    "name": "New Item",
    "description": "A new item description",
    "status": "draft",
    "query": null
}
```

**Implementation Details**:
- Uses Pydantic for automatic validation
- Returns 201 Created status code
- `item_id` is null (not persisting to database)
- Demonstrates request body parsing
- Status defaults to "created" if not provided

---

#### `async def health_check()`

**Route**: `GET /api/health`

**Tags**: Health

**Purpose**: Health check endpoint for monitoring the API status

**Parameters**: None

**Returns**: `HealthResponse`
```python
{
    "status": "healthy",
    "version": "1.0.0"
}
```

**Response Code**: 200 OK

**Use Cases**:
- Kubernetes/container health probes
- Load balancer health checks
- Monitoring and alerting systems
- Deployment verification
- API availability verification

**Example Request**:
```bash
curl http://localhost:8000/api/health
```

**Example Response**:
```json
{
    "status": "healthy",
    "version": "1.0.0"
}
```

**CloudWatch Monitoring**:
- This endpoint is commonly monitored by AWS CloudWatch
- Lambda alarms can be triggered if health check fails
- Expected response time: < 100ms

**Best Practices**:
- Use for automated health monitoring
- Call this endpoint every 30 seconds for continuous monitoring
- Alert if status is not "healthy"
- Log response time and status

---

#### `async def get_aws_info()`

**Route**: `GET /api/aws-info`

**Tags**: AWS

**Purpose**: Returns AWS Lambda environment information when running in Lambda

**Parameters**: None

**Returns**: `dict`
```python
{
    "lambda_function_name": str,  # Function name or "local"
    "aws_region": str,             # AWS region or "us-east-1"
    "environment": str,            # "aws" or "local"
    "lambda_version": str          # Function version or "N/A"
}
```

**Response Code**: 200 OK

**Environment Variables Used**:
- `AWS_LAMBDA_FUNCTION_NAME` - Set by AWS Lambda
- `AWS_REGION` - Set by AWS Lambda
- `AWS_LAMBDA_FUNCTION_VERSION` - Set by AWS Lambda

**Use Cases**:
- Verify API is running in Lambda vs local
- Debugging deployment issues
- Monitoring Lambda function information
- Verification after deployment

**Example Requests**:
```bash
# Local development
curl http://localhost:8000/api/aws-info

# AWS Lambda
curl https://api-id.execute-api.us-east-1.amazonaws.com/prod/api/aws-info
```

**Example Response (Local)**:
```json
{
    "lambda_function_name": "local",
    "aws_region": "us-east-1",
    "environment": "local",
    "lambda_version": "N/A"
}
```

**Example Response (AWS Lambda)**:
```json
{
    "lambda_function_name": "fastapi-app",
    "aws_region": "us-east-1",
    "environment": "aws",
    "lambda_version": "$LATEST"
}
```

**Implementation Details**:
- Uses `os.getenv()` to read environment variables
- Defaults to "local" if not in Lambda environment
- Useful for debugging and verification
- Lightweight endpoint with no dependencies

---

### **Module-Level Configuration**

#### Logging Configuration

```python
logger = logging.getLogger()
logger.setLevel(logging.INFO)
```

**Purpose**: Configure CloudWatch logging for AWS Lambda

**Details**:
- Root logger used for Lambda compatibility
- Set to INFO level (captures info, warning, error, critical)
- Messages automatically sent to CloudWatch
- Each log entry includes timestamp, level, and message

**Log Levels**:
- DEBUG (10): Detailed diagnostic information
- INFO (20): Confirmation that things are working
- WARNING (30): Something unexpected or deprecated
- ERROR (40): A serious problem
- CRITICAL (50): A very serious problem

**Usage**:
```python
logger.info(f"Processing request: {request_id}")
logger.error(f"Error occurred: {error_message}")
```

---

#### FastAPI Application Configuration

```python
app = FastAPI(
    title="Python API",
    description="...",
    version="1.0.0",
    contact={...},
    license_info={...},
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={...}
)
```

**Configuration Parameters**:

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `title` | "Python API" | API name in documentation |
| `description` | Multi-line string | API description with features |
| `version` | "1.0.0" | API version number |
| `contact.name` | "API Support" | Contact person name |
| `contact.url` | "http://localhost:8000/docs" | Contact URL |
| `contact.email` | "support@example.com" | Support email |
| `license_info.name` | "MIT" | License type |
| `openapi_url` | "/api/v1/openapi.json" | OpenAPI schema endpoint |
| `docs_url` | "/docs" | Swagger UI endpoint |
| `redoc_url` | "/redoc" | ReDoc endpoint |

**Generated Endpoints**:
- `/docs` - Swagger UI interactive documentation
- `/redoc` - ReDoc alternative documentation
- `/api/v1/openapi.json` - OpenAPI schema (JSON)
- `/openapi.json` - Default OpenAPI schema

---

#### Lambda Handler

```python
lambda_handler = Mangum(app, lifespan="off")
```

**Purpose**: Converts FastAPI ASGI application to AWS Lambda handler

**Parameters**:
- `app` - FastAPI application instance
- `lifespan` - "off" (disables startup/shutdown events in Lambda)

**Function Signature**:
```python
def lambda_handler(event: dict, context: object) -> dict:
    """
    AWS Lambda handler that processes API Gateway events.
    
    Args:
        event: API Gateway event (REST API format)
        context: Lambda context object
    
    Returns:
        dict: API Gateway response format
    """
```

**Input Event Format** (API Gateway REST API):
```python
{
    "resource": "/api/items",
    "path": "/api/items",
    "httpMethod": "POST",
    "headers": {
        "Host": "example.com",
        "Content-Type": "application/json"
    },
    "queryStringParameters": None,
    "pathParameters": None,
    "body": '{"name": "item"}',
    "isBase64Encoded": False,
    "requestContext": {
        "httpMethod": "POST",
        "path": "/api/items",
        "identity": {"sourceIp": "192.168.1.1"}
    }
}
```

**Output Response Format** (API Gateway):
```python
{
    "statusCode": 200,
    "headers": {
        "Content-Type": "application/json"
    },
    "body": '{"message": "success"}',
    "isBase64Encoded": False
}
```

**How It Works**:
1. Receives API Gateway event
2. Converts to ASGI format via Mangum
3. FastAPI processes the request
4. Response converted back to API Gateway format
5. Returns to API Gateway

---

### **Application Entry Point**

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Purpose**: Run FastAPI locally with Uvicorn development server

**Parameters**:
- `app` - FastAPI application instance
- `host` - "0.0.0.0" (accessible from any network interface)
- `port` - 8000 (standard FastAPI development port)

**Usage**:
```bash
cd src
python fast_api.py

# Or using uvicorn directly
python -m uvicorn fast_api:app --reload --port 8000
```

**Available Options**:
- `--reload` - Auto-reload on file changes
- `--host 0.0.0.0` - Listen on all interfaces
- `--port 8000` - Use port 8000
- `--log-level info` - Set log level

**Access**:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## AWS Gateway Integration

### File: `src/aws_gateway_integration.py`

This module provides utilities for working with AWS API Gateway events and responses.

---

### **APIGatewayEvent Class**

Parses and provides convenient access to API Gateway event data.

#### `__init__(self, event: Dict[str, Any])`

**Purpose**: Initialize the event parser

**Parameters**:
```python
event: Dict[str, Any]
    - The raw API Gateway event from Lambda
    - Can be REST API or HTTP API format
```

**Attributes Set**:
```python
self.event = event                          # Raw event
self.is_http_api = boolean                  # True if HTTP API format
self.is_rest_api = boolean                  # True if REST API format
```

**Example Usage**:
```python
# REST API event
rest_event = {
    "httpMethod": "GET",
    "path": "/api/items",
    "requestContext": {"requestId": "123"}
}
event = APIGatewayEvent(rest_event)
print(event.is_rest_api)  # True
print(event.is_http_api)  # False

# HTTP API event
http_event = {
    "requestContext": {
        "http": {"method": "GET", "path": "/api/items"}
    }
}
event = APIGatewayEvent(http_event)
print(event.is_http_api)  # True
```

---

#### `@property method`

**Purpose**: Get HTTP method from event

**Returns**: `str` - HTTP method (GET, POST, PUT, DELETE, etc.)

**Behavior**:
- REST API: Reads from `event["httpMethod"]`
- HTTP API: Reads from `event["requestContext"]["http"]["method"]`
- Default: "GET"

**Example**:
```python
event = APIGatewayEvent(api_gateway_event)
method = event.method  # "POST"
```

---

#### `@property path`

**Purpose**: Get request path from event

**Returns**: `str` - Request path (e.g., "/api/items/42")

**Behavior**:
- REST API: Reads from `event["path"]`
- HTTP API: Reads from `event["requestContext"]["http"]["path"]`
- Default: "/"

**Example**:
```python
path = event.path  # "/api/items/42"
```

---

#### `@property headers`

**Purpose**: Get request headers from event

**Returns**: `Dict[str, str]` - Dictionary of headers

**Behavior**:
- Returns `event["headers"]` dict
- Default: Empty dict if not present
- Case-sensitive keys

**Example**:
```python
headers = event.headers
auth = headers.get("Authorization")
content_type = headers.get("Content-Type")
```

---

#### `@property query_params`

**Purpose**: Get query parameters from event

**Returns**: `Dict[str, str]` - Dictionary of query parameters

**Behavior**:
- REST API: Parses `event["queryStringParameters"]`
- HTTP API: Parses `event["rawQueryString"]`
- Returns empty dict if no parameters

**Example**:
```python
params = event.query_params
page = params.get("page", "1")
limit = params.get("limit", "10")
```

---

#### `@property body`

**Purpose**: Get request body from event

**Returns**: `Optional[str]` - Decoded body content

**Behavior**:
- Checks `event["isBase64Encoded"]` flag
- Decodes base64 if necessary
- Returns None if no body

**Example**:
```python
body_str = event.body
if body_str:
    data = json.loads(body_str)
    print(data)
```

---

#### `@property source_ip`

**Purpose**: Get client IP address from event

**Returns**: `str` - Client IP address

**Behavior**:
- REST API: `event["requestContext"]["identity"]["sourceIp"]`
- HTTP API: `event["requestContext"]["http"]["sourceIp"]`
- Default: "0.0.0.0"

**Example**:
```python
ip = event.source_ip  # "192.168.1.1"
```

---

#### `@property request_id`

**Purpose**: Get unique request ID from event

**Returns**: `str` - Request ID for tracing

**Behavior**:
- REST API: `event["requestContext"]["requestId"]`
- HTTP API: `event["requestContext"]["requestId"]`
- Default: "unknown"

**Example**:
```python
request_id = event.request_id  # "req-abc-123"
```

---

### **APIGatewayResponse Class**

Formats responses in the correct API Gateway format.

#### `@staticmethod success(...)`

**Purpose**: Create a successful API Gateway response

**Parameters**:
```python
status_code: int = 200
    - HTTP status code (e.g., 200, 201, 204)
    
body: Optional[Dict[str, Any]] = None
    - Response body as dict (will be JSON serialized)
    
headers: Optional[Dict[str, str]] = None
    - HTTP response headers
    
is_base64_encoded: bool = False
    - Whether body is base64 encoded
```

**Returns**: `Dict[str, Any]` - API Gateway response

**Response Format**:
```python
{
    "statusCode": 200,
    "headers": {"Content-Type": "application/json", ...},
    "body": '{"key": "value"}',
    "isBase64Encoded": False
}
```

**Example Usage**:
```python
# Simple success response
response = APIGatewayResponse.success(
    status_code=200,
    body={"message": "Success"}
)

# With custom headers
response = APIGatewayResponse.success(
    status_code=201,
    body={"id": 123},
    headers={"X-Custom-Header": "value"}
)

# No body (204 No Content)
response = APIGatewayResponse.success(
    status_code=204,
    body=None
)
```

---

#### `@staticmethod error(...)`

**Purpose**: Create an error API Gateway response

**Parameters**:
```python
status_code: int = 500
    - HTTP error status code
    
message: str = "Internal Server Error"
    - User-friendly error message
    
error_code: Optional[str] = None
    - Error code for client handling
    
details: Optional[Dict[str, Any]] = None
    - Error details (logged but not sent to client)
    
headers: Optional[Dict[str, str]] = None
    - HTTP response headers
```

**Returns**: `Dict[str, Any]` - API Gateway error response

**Response Format**:
```python
{
    "statusCode": 404,
    "headers": {"Content-Type": "application/json"},
    "body": '{"error": "Not found", "status_code": 404, "timestamp": "...", "error_code": "NOT_FOUND"}',
    "isBase64Encoded": False
}
```

**Example Usage**:
```python
# Simple error
response = APIGatewayResponse.error(
    status_code=404,
    message="Not found"
)

# With error code
response = APIGatewayResponse.error(
    status_code=401,
    message="Unauthorized",
    error_code="INVALID_TOKEN"
)

# With details (server-side logging)
response = APIGatewayResponse.error(
    status_code=400,
    message="Invalid request",
    error_code="VALIDATION_ERROR",
    details={"field": "email", "reason": "invalid format"}
)
```

---

### **CORSHelper Class**

Configures Cross-Origin Resource Sharing (CORS) headers.

#### `@staticmethod get_cors_headers(...)`

**Purpose**: Generate CORS headers for API Gateway response

**Parameters**:
```python
allow_origins: Optional[list] = None
    - List of allowed origins (default: "*")
    - Example: ["https://example.com"]
    
allow_methods: Optional[list] = None
    - List of allowed HTTP methods
    - Default: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    
allow_headers: Optional[list] = None
    - List of allowed request headers
    - Example: ["Content-Type", "Authorization"]
    
allow_credentials: bool = True
    - Whether credentials (cookies) are allowed
    
max_age: int = 3600
    - Cache duration in seconds for preflight requests
```

**Returns**: `Dict[str, str]` - CORS headers

**Generated Headers**:
```python
{
    "Access-Control-Allow-Origin": "https://example.com",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Max-Age": "3600"
}
```

**Example Usage**:
```python
# Allow all origins
headers = CORSHelper.get_cors_headers()

# Specific origins
headers = CORSHelper.get_cors_headers(
    allow_origins=["https://app.example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"]
)

# Use in response
response = APIGatewayResponse.success(
    body={"data": "value"},
    headers=headers
)
```

---

### **AuthenticationHelper Class**

Handles authentication token extraction and validation.

#### `@staticmethod get_authorization_token(headers: Dict[str, str])`

**Purpose**: Extract Bearer token from Authorization header

**Parameters**:
```python
headers: Dict[str, str]
    - Request headers dictionary
    - Case-insensitive key lookup
```

**Returns**: `Optional[str]` - Token without "Bearer " prefix, or None

**Behavior**:
- Checks for "Authorization" or "authorization" header
- Expects format: "Bearer {token}"
- Returns token if found, None otherwise

**Example Usage**:
```python
headers = {"Authorization": "Bearer my-token-123"}
token = AuthenticationHelper.get_authorization_token(headers)
print(token)  # "my-token-123"

# No token
headers = {}
token = AuthenticationHelper.get_authorization_token(headers)
print(token)  # None
```

---

#### `@staticmethod is_authorized(headers: Dict[str, str], expected_token: Optional[str] = None)`

**Purpose**: Check if request is authorized

**Parameters**:
```python
headers: Dict[str, str]
    - Request headers dictionary
    
expected_token: Optional[str] = None
    - Token to validate against
    - If None, just checks if token is present
```

**Returns**: `bool` - True if authorized, False otherwise

**Behavior**:
- If `expected_token` provided, checks if token matches
- If no `expected_token`, checks if token is present
- Case-sensitive token comparison

**Example Usage**:
```python
headers = {"Authorization": "Bearer my-token"}

# Check if token is present
if AuthenticationHelper.is_authorized(headers):
    print("Token is present")

# Check if token matches
if AuthenticationHelper.is_authorized(headers, "my-token"):
    print("Token is valid")

# Check if token matches (wrong token)
if AuthenticationHelper.is_authorized(headers, "wrong-token"):
    print("Won't execute - wrong token")
```

---

### **RequestLogger Class**

Logs API requests and responses to CloudWatch.

#### `@staticmethod log_request(event: APIGatewayEvent)`

**Purpose**: Log incoming API Gateway request

**Parameters**:
```python
event: APIGatewayEvent
    - Parsed API Gateway event
```

**Logged Information**:
```python
{
    "method": "GET",
    "path": "/api/items",
    "source_ip": "192.168.1.1",
    "request_id": "req-123",
    "headers": {...}
}
```

**Example Usage**:
```python
event = APIGatewayEvent(api_gateway_event)
RequestLogger.log_request(event)
# Output to CloudWatch Logs
```

---

#### `@staticmethod log_response(request_id: str, status_code: int, response_time_ms: float)`

**Purpose**: Log API response with performance metrics

**Parameters**:
```python
request_id: str
    - Request identifier
    
status_code: int
    - HTTP response status code
    
response_time_ms: float
    - Request duration in milliseconds
```

**Logged Information**:
```python
{
    "request_id": "req-123",
    "status_code": 200,
    "response_time_ms": 123.45
}
```

**Example Usage**:
```python
import time

start = time.time()
# Process request
elapsed = (time.time() - start) * 1000  # Convert to milliseconds

RequestLogger.log_response(
    request_id="req-123",
    status_code=200,
    response_time_ms=elapsed
)
```

---

### **Decorators**

#### `@api_gateway_handler`

**Purpose**: Decorator for Lambda handlers to automate event parsing, logging, and error handling

**Function Signature**:
```python
def api_gateway_handler(func: Callable) -> Callable:
    """
    Wrap a Lambda handler with API Gateway utilities.
    
    Args:
        func: Async handler function
        
    Returns:
        Wrapped handler function
    """
```

**What It Does**:
1. Parses API Gateway event
2. Logs incoming request
3. Calls handler function
4. Logs response with timing
5. Handles exceptions automatically

**Example Usage**:
```python
@api_gateway_handler
async def my_handler(event, context):
    # event is raw dict, parsed automatically
    parsed_event = APIGatewayEvent(event)
    
    if parsed_event.method == "GET":
        return APIGatewayResponse.success(
            body={"items": []}
        )
    
    return APIGatewayResponse.error(404, "Not found")
```

---

## Data Models

### **Item Model (Pydantic)**

```python
class Item(BaseModel):
    name: str                          # 1-100 characters
    description: Optional[str] = None  # 0-500 characters
    status: Optional[str] = "created"  # Custom status
```

**Validation**:
- Automatically validates types
- Enforces length constraints
- Provides helpful error messages
- Converts compatible types (e.g., int to str)

---

### **ItemResponse Model (Pydantic)**

```python
class ItemResponse(BaseModel):
    item_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: str
    query: Optional[str] = None
```

**Used By**: All item endpoints for responses

---

### **HealthResponse Model (Pydantic)**

```python
class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
```

**Used By**: Health check endpoint

---

## API Endpoints

### **Summary Table**

| Method | Path | Function | Status Code |
|--------|------|----------|-------------|
| GET | / | read_root | 200 |
| GET | /api/items/{item_id} | read_item | 200 |
| POST | /api/items/ | create_item | 201 |
| GET | /api/health | health_check | 200 |
| GET | /api/aws-info | get_aws_info | 200 |
| GET | /docs | Swagger UI | 200 |
| GET | /redoc | ReDoc | 200 |

---

## Utility Classes

### **Complete Class Hierarchy**

```
APIGatewayEvent
├── Properties
│   ├── method: str
│   ├── path: str
│   ├── headers: Dict[str, str]
│   ├── query_params: Dict[str, str]
│   ├── body: Optional[str]
│   ├── source_ip: str
│   └── request_id: str
└── Attributes
    ├── event: Dict
    ├── is_http_api: bool
    └── is_rest_api: bool

APIGatewayResponse
└── Static Methods
    ├── success(status_code, body, headers, is_base64_encoded)
    └── error(status_code, message, error_code, details, headers)

CORSHelper
└── Static Methods
    └── get_cors_headers(allow_origins, allow_methods, allow_headers, allow_credentials, max_age)

AuthenticationHelper
└── Static Methods
    ├── get_authorization_token(headers)
    └── is_authorized(headers, expected_token)

RequestLogger
└── Static Methods
    ├── log_request(event)
    └── log_response(request_id, status_code, response_time_ms)
```

---

## Usage Examples

### **Example 1: Complete Request Handler**

```python
async def handle_get_item(event, context):
    """Complete example of handling a GET request."""
    
    # Parse event
    parsed_event = APIGatewayEvent(event)
    RequestLogger.log_request(parsed_event)
    
    # Check authentication
    auth_headers = parsed_event.headers
    token = AuthenticationHelper.get_authorization_token(auth_headers)
    
    if not token:
        return APIGatewayResponse.error(
            status_code=401,
            message="Missing authentication token",
            error_code="NO_AUTH"
        )
    
    # Validate token
    if not AuthenticationHelper.is_authorized(auth_headers, expected_token="valid-token"):
        return APIGatewayResponse.error(
            status_code=403,
            message="Invalid token",
            error_code="INVALID_AUTH"
        )
    
    # Add CORS headers
    cors_headers = CORSHelper.get_cors_headers(
        allow_origins=["https://app.example.com"]
    )
    
    # Return success response
    return APIGatewayResponse.success(
        status_code=200,
        body={"item_id": 1, "name": "Item 1"},
        headers=cors_headers
    )
```

---

### **Example 2: POST Request with Validation**

```python
async def handle_create_item(event, context):
    """Complete example of handling a POST request."""
    
    parsed_event = APIGatewayEvent(event)
    
    # Parse body
    if not parsed_event.body:
        return APIGatewayResponse.error(
            status_code=400,
            message="Request body required",
            error_code="NO_BODY"
        )
    
    try:
        data = json.loads(parsed_event.body)
        item = Item(**data)
    except json.JSONDecodeError:
        return APIGatewayResponse.error(
            status_code=400,
            message="Invalid JSON in request body",
            error_code="INVALID_JSON"
        )
    except ValueError as e:
        return APIGatewayResponse.error(
            status_code=422,
            message="Validation failed",
            error_code="VALIDATION_ERROR",
            details={"validation_error": str(e)}
        )
    
    # Create item (mock)
    new_item = {
        "id": 1,
        "name": item.name,
        "description": item.description,
        "status": item.status or "created"
    }
    
    return APIGatewayResponse.success(
        status_code=201,
        body=new_item
    )
```

---

### **Example 3: Error Handling Pattern**

```python
@api_gateway_handler
async def safe_handler(event, context):
    """Complete error handling example."""
    
    try:
        parsed_event = APIGatewayEvent(event)
        
        # Validate required parameters
        if not parsed_event.path:
            raise ValueError("Path is required")
        
        # Check authentication
        if not AuthenticationHelper.get_authorization_token(parsed_event.headers):
            raise PermissionError("Not authenticated")
        
        # Process request
        if parsed_event.method == "GET":
            return APIGatewayResponse.success(
                body={"data": []}
            )
        
        # Unsupported method
        raise NotImplementedError(f"Method {parsed_event.method} not supported")
        
    except ValueError as e:
        return APIGatewayResponse.error(
            status_code=400,
            message=str(e),
            error_code="INVALID_INPUT"
        )
    
    except PermissionError as e:
        return APIGatewayResponse.error(
            status_code=403,
            message=str(e),
            error_code="FORBIDDEN"
        )
    
    except NotImplementedError as e:
        return APIGatewayResponse.error(
            status_code=405,
            message=str(e),
            error_code="METHOD_NOT_ALLOWED"
        )
    
    except Exception as e:
        logger.exception("Unhandled exception")
        return APIGatewayResponse.error(
            status_code=500,
            message="Internal server error",
            error_code="INTERNAL_ERROR"
        )
```

---

## Integration Flow

### **Local Development Flow**

```
User Request
    ↓
Uvicorn (localhost:8000)
    ↓
FastAPI Router
    ↓
Endpoint Function (e.g., read_item)
    ↓
Response Model Validation
    ↓
JSON Response
    ↓
Browser/Client
```

### **AWS Lambda Flow**

```
API Gateway Request
    ↓
Lambda Handler (lambda_handler)
    ↓
Mangum ASGI Adapter
    ↓
FastAPI Router
    ↓
Endpoint Function (e.g., read_item)
    ↓
Response Model Validation
    ↓
Mangum Converts to API Gateway Format
    ↓
API Gateway Response
    ↓
Client
```

### **With AWS Integration Utilities Flow**

```
API Gateway Event
    ↓
APIGatewayEvent Parser (parse event data)
    ↓
AuthenticationHelper (check auth token)
    ↓
Business Logic
    ↓
APIGatewayResponse (format response)
    ↓
CORSHelper (add CORS headers)
    ↓
RequestLogger (log request/response)
    ↓
Lambda Returns Response
    ↓
API Gateway
    ↓
Client
```

---

## HTTP Status Codes

### **Success Codes**

| Code | Meaning | Use Case |
|------|---------|----------|
| 200 | OK | Successful GET request |
| 201 | Created | Successful POST request |
| 204 | No Content | Successful DELETE request |

### **Client Error Codes**

| Code | Meaning | Use Case |
|------|---------|----------|
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation failed |

### **Server Error Codes**

| Code | Meaning | Use Case |
|------|---------|----------|
| 500 | Internal Server Error | Unhandled exception |
| 502 | Bad Gateway | Lambda cold start timeout |
| 503 | Service Unavailable | Lambda throttled |

---

## Environment Variables

### **AWS Lambda Environment Variables**

| Variable | Set By | Example Value |
|----------|--------|---------------|
| AWS_LAMBDA_FUNCTION_NAME | AWS Lambda | "fastapi-app" |
| AWS_REGION | AWS Lambda | "us-east-1" |
| AWS_LAMBDA_FUNCTION_VERSION | AWS Lambda | "$LATEST" |
| PYTHONPATH | Custom | "/var/task" |

---

## Best Practices

### **API Design**
1. Always validate input using Pydantic models
2. Use appropriate HTTP status codes
3. Include meaningful error messages
4. Log all requests and responses
5. Document all endpoints with docstrings

### **Security**
1. Always authenticate requests
2. Use HTTPS (automatic with API Gateway)
3. Validate CORS origins
4. Don't expose stack traces in error responses
5. Log suspicious activity

### **Performance**
1. Use Lambda Layers to reduce cold start
2. Cache responses when possible
3. Use async/await for concurrent operations
4. Monitor response times
5. Set appropriate timeouts

### **Monitoring**
1. Log all requests to CloudWatch
2. Track error rates and types
3. Monitor response time metrics
4. Set up alarms for high error rates
5. Review logs regularly

---

## Troubleshooting

### **Common Issues**

#### Module Import Error
```
ModuleNotFoundError: No module named 'aws_gateway_integration'
```
**Solution**: Ensure `sys.path` includes the src directory
```python
import sys
sys.path.insert(0, '/var/task')
from aws_gateway_integration import APIGatewayEvent
```

#### JSON Decode Error
```
json.decoder.JSONDecodeError: Expecting value
```
**Solution**: Check if body is base64 encoded
```python
body = event.get('body', '')
if event.get('isBase64Encoded'):
    body = base64.b64decode(body).decode('utf-8')
```

#### Authorization Header Not Found
```
Token is None
```
**Solution**: Check header case sensitivity
```python
headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
auth = headers.get('authorization', '')
```

---

## Function Quick Reference

| Function | Location | Returns | Purpose |
|----------|----------|---------|---------|
| read_root | fast_api.py | dict | Welcome endpoint |
| read_item | fast_api.py | ItemResponse | Get item by ID |
| create_item | fast_api.py | ItemResponse | Create new item |
| health_check | fast_api.py | HealthResponse | Health status |
| get_aws_info | fast_api.py | dict | AWS environment info |
| APIGatewayEvent.__init__ | aws_gateway_integration.py | None | Parse event |
| APIGatewayEvent.method | aws_gateway_integration.py | str | Get HTTP method |
| APIGatewayEvent.path | aws_gateway_integration.py | str | Get request path |
| APIGatewayResponse.success | aws_gateway_integration.py | dict | Format success response |
| APIGatewayResponse.error | aws_gateway_integration.py | dict | Format error response |
| CORSHelper.get_cors_headers | aws_gateway_integration.py | dict | Get CORS headers |
| AuthenticationHelper.get_authorization_token | aws_gateway_integration.py | Optional[str] | Extract token |
| AuthenticationHelper.is_authorized | aws_gateway_integration.py | bool | Check authorization |
| RequestLogger.log_request | aws_gateway_integration.py | None | Log request |
| RequestLogger.log_response | aws_gateway_integration.py | None | Log response |

---

**Document Version**: 1.0
**Last Updated**: January 2025
**Status**: Complete and Ready for Production
