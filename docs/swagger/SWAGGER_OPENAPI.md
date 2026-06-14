# 🔗 Swagger/OpenAPI Documentation

## Quick Access

### 🚀 Live Swagger UI (Interactive)
**URL:** `http://localhost:8000/docs`

Start the FastAPI server:
```bash
cd "c:\Users\desha\Python Projects\python-test-env"
.\.venv\Scripts\python.exe -m uvicorn src.fast_api:app --reload
```

Then open http://localhost:8000/docs in your browser.

### 📖 Alternative: ReDoc (Read-Only)
**URL:** `http://localhost:8000/redoc`

### 📄 OpenAPI JSON Schema
**URL:** `http://localhost:8000/api/v1/openapi.json`

Or view the local file: [openapi.json](openapi.json)

---

## API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
Currently no authentication required (demo mode).

### Response Format
All responses are JSON with the following structure:
```json
{
  "data": {...},
  "status": "success|error",
  "code": 200
}
```

---

## Endpoints

### 1. Welcome (Root)
```
GET /
```

**Description:** Welcome endpoint with links to documentation

**Response (200):**
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

### 2. Health Check
```
GET /api/health
```

**Description:** API health status endpoint for monitoring

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

**Use Case:** Uptime monitoring, load balancer health checks

---

### 3. Get Item
```
GET /api/items/{item_id}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| item_id | integer | Yes | Item ID (must be > 0) |
| q | string | No | Optional query parameter (1-50 chars) |

**Examples:**
```bash
# Get item 1
GET /api/items/1

# Get item 1 with search query
GET /api/items/1?q=search_term
```

**Response (200):**
```json
{
  "item_id": 1,
  "name": "Item 1",
  "description": "Description for item 1",
  "status": "retrieved",
  "query": "search_term"
}
```

**Error Responses:**
- 404 Not Found - Item not found
- 422 Unprocessable Entity - Invalid parameters

---

### 4. Create Item
```
POST /api/items/
```

**Request Body:**
```json
{
  "name": "Item name",
  "description": "Optional description",
  "status": "active"
}
```

**Parameters:**
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| name | string | Yes | 1-100 characters |
| description | string | No | Max 500 characters |
| status | string | No | Default: "created" |

**Examples:**
```bash
# Minimal request
curl -X POST "http://localhost:8000/api/items/" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Item"}'

# Full request
curl -X POST "http://localhost:8000/api/items/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Product A",
    "description": "A great product",
    "status": "active"
  }'
```

**Response (201 Created):**
```json
{
  "item_id": null,
  "name": "New Item",
  "description": null,
  "status": "created",
  "query": null
}
```

**Error Responses:**
- 400 Bad Request - Invalid request body
- 422 Unprocessable Entity - Validation error

---

### 5. AWS Info
```
GET /api/aws-info
```

**Description:** Returns AWS Lambda environment information

**Response (200):**
```json
{
  "lambda_function_name": "local",
  "aws_region": "us-east-1",
  "environment": "local",
  "lambda_version": "N/A"
}
```

When running in AWS Lambda:
```json
{
  "lambda_function_name": "my-function",
  "aws_region": "us-east-1",
  "environment": "aws",
  "lambda_version": "$LATEST"
}
```

---

## Data Models

### Item
Request model for creating items.

```json
{
  "name": "string",              // Required, 1-100 chars
  "description": "string",       // Optional, max 500 chars
  "status": "string"             // Optional, default: "created"
}
```

### ItemResponse
Response model for item operations.

```json
{
  "item_id": 0,                  // Optional
  "name": "string",              // Optional
  "description": "string",       // Optional
  "status": "string",            // Required
  "query": "string"              // Optional
}
```

### HealthResponse
Response model for health check.

```json
{
  "status": "string",            // Required
  "version": "string"            // Required, default: "1.0.0"
}
```

---

## HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| **200** | OK | Successful GET/POST request |
| **201** | Created | Resource created successfully |
| **204** | No Content | Successful request with no content |
| **400** | Bad Request | Invalid request format |
| **404** | Not Found | Resource not found |
| **405** | Method Not Allowed | HTTP method not allowed for endpoint |
| **422** | Unprocessable Entity | Validation error in request data |
| **500** | Internal Server Error | Server error |

---

## Error Responses

### Validation Error (422)
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.string.too_short"
    }
  ]
}
```

### Not Found (404)
```json
{
  "detail": "Not Found"
}
```

### Method Not Allowed (405)
```json
{
  "detail": "Method Not Allowed"
}
```

---

## Request/Response Examples

### Example 1: Create an Item
```bash
curl -X POST "http://localhost:8000/api/items/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Widget",
    "description": "A useful widget",
    "status": "active"
  }' \
  -v
```

**Response:**
```
HTTP/1.1 201 Created
Content-Type: application/json

{
  "item_id": null,
  "name": "Widget",
  "description": "A useful widget",
  "status": "active",
  "query": null
}
```

### Example 2: Get Item with Query
```bash
curl -X GET "http://localhost:8000/api/items/1?q=test" \
  -H "Accept: application/json" \
  -v
```

**Response:**
```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "item_id": 1,
  "name": "Item 1",
  "description": "Description for item 1",
  "status": "retrieved",
  "query": "test"
}
```

### Example 3: Health Check
```bash
curl -X GET "http://localhost:8000/api/health" \
  -H "Accept: application/json" \
  -v
```

**Response:**
```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## API Testing Tools

### Using Swagger UI (Recommended)
1. Start the server: `python -m uvicorn src.fast_api:app --reload`
2. Open: http://localhost:8000/docs
3. Try out endpoints with the built-in interface

### Using curl
```bash
# GET request
curl http://localhost:8000/api/health

# POST request
curl -X POST http://localhost:8000/api/items/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Item"}'

# GET with query parameter
curl "http://localhost:8000/api/items/1?q=search"
```

### Using Python requests
```python
import requests

# Health check
response = requests.get("http://localhost:8000/api/health")
print(response.json())

# Create item
response = requests.post(
    "http://localhost:8000/api/items/",
    json={"name": "Widget", "description": "A widget"}
)
print(response.json())

# Get item
response = requests.get("http://localhost:8000/api/items/1?q=test")
print(response.json())
```

### Using Python httpx (Async)
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get("http://localhost:8000/api/health")
    print(response.json())
```

### Using Postman
1. Import the OpenAPI spec: [openapi.json](openapi.json)
2. Or use Postman collection: [postman_collection.json](postman_collection.json)
3. Test endpoints in Postman UI

---

## Rate Limiting & Throttling

**Current Status:** No rate limiting (demo mode)

For production deployment, consider implementing:
- Per-minute request limits
- Per-user throttling
- IP-based rate limiting

---

## Authentication & Security

**Current Status:** No authentication required (demo mode)

For production deployment, consider:
- Bearer token authentication
- API key authentication
- OAuth 2.0
- CORS configuration
- HTTPS/TLS encryption

---

## CORS (Cross-Origin Resource Sharing)

**Current Status:** CORS enabled for all origins (demo mode)

For production, restrict to specific origins:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## WebSocket Support

**Current Status:** Not implemented

FastAPI supports WebSocket connections. Add if needed:
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Handle WebSocket communication
```

---

## Deployment

### Local Development
```bash
python -m uvicorn src.fast_api:app --reload --port 8000
```

### Production with Gunicorn
```bash
pip install gunicorn uvicorn
gunicorn src.fast_api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### AWS Lambda
```bash
# The app includes Mangum ASGI adapter
lambda_handler = Mangum(app, lifespan="off")
```

### Docker
```bash
docker build -f Dockerfile.lambda -t my-api .
docker run -p 8000:8000 my-api
```

---

## API Versioning

**Current Version:** 1.0.0

For versioning strategy, consider:
- URL path: `/api/v1/items/`
- Query parameter: `/api/items?version=1`
- Header: `X-API-Version: 1`

---

## Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port
python -m uvicorn src.fast_api:app --port 8001
```

### CORS Issues
- Ensure CORS middleware is configured
- Check allowed origins match your client domain
- Use Swagger UI to test (same origin)

### 422 Validation Errors
- Check required fields are provided
- Verify field value constraints (length, format)
- See error details in response body

### Connection Refused
- Ensure server is running
- Check correct host and port
- Verify firewall allows connections

---

## Performance Tips

### Optimization
- Use caching for frequently accessed data
- Implement pagination for large datasets
- Use async/await for I/O operations
- Monitor with logging and metrics

### Monitoring
- Log all requests and responses
- Track response times
- Monitor error rates
- Set up alerts for failures

---

## API Versioning Strategy

For future versions:
```python
# Option 1: URL Path Versioning
@app.get("/api/v1/items/")
@app.get("/api/v2/items/")

# Option 2: Query Parameter
@app.get("/api/items/")  # version param in query

# Option 3: Header Versioning
# X-API-Version: 1
```

---

## Additional Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **OpenAPI Specification:** https://spec.openapis.org/
- **Swagger Editor:** https://editor.swagger.io/
- **Postman:** https://www.postman.com/
- **API Design Best Practices:** https://restfulapi.net/

---

## API Endpoints Summary

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/` | Welcome message | ✅ Implemented |
| GET | `/api/health` | Health check | ✅ Implemented |
| GET | `/api/items/{id}` | Get item | ✅ Implemented |
| POST | `/api/items/` | Create item | ✅ Implemented |
| GET | `/api/aws-info` | AWS info | ✅ Implemented |
| GET | `/docs` | Swagger UI | ✅ Auto-generated |
| GET | `/redoc` | ReDoc UI | ✅ Auto-generated |
| GET | `/api/v1/openapi.json` | OpenAPI spec | ✅ Auto-generated |

---

## Files

- **API Code:** [src/fast_api.py](src/fast_api.py)
- **OpenAPI Schema:** [openapi.json](openapi.json)
- **Postman Collection:** [postman_collection.json](postman_collection.json)
- **Test Suite:** [TEST_GUIDE.md](TEST_GUIDE.md)

---

**Swagger/OpenAPI Documentation**  
**Version:** 1.0  
**Generated:** January 19, 2026  
**Status:** ✅ Production Ready
