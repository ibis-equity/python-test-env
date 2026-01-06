# FastAPI Swagger Documentation

## Overview

This document describes the Python API built with FastAPI. The API provides comprehensive documentation through:

1. **Interactive Swagger UI** - Available at `/docs`
2. **ReDoc Documentation** - Available at `/redoc`
3. **OpenAPI Schema** - Available at `/api/v1/openapi.json`

## Accessing Documentation

### Swagger UI (Recommended for Testing)
```
http://localhost:8000/docs
```
Features:
- Interactive endpoint testing
- Request/response examples
- Parameter documentation
- Authentication testing

### ReDoc (For Reading)
```
http://localhost:8000/redoc
```
Features:
- Clean, readable documentation
- Better for documentation viewing
- Mobile-friendly

### OpenAPI Schema
```
http://localhost:8000/api/v1/openapi.json
```
Features:
- Machine-readable OpenAPI 3.0.2 specification
- Can be imported into tools like Postman

## API Endpoints

### 1. Welcome Endpoint
**GET** `/`

Returns a welcome message and links to documentation.

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
**GET** `/api/health`

Monitor the API health status. Use this for load balancers and monitoring systems.

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

**Use Cases:**
- Kubernetes liveness probes
- Container health checks
- Load balancer monitoring
- Uptime monitoring

---

### 3. Get Item by ID
**GET** `/api/items/{item_id}`

Retrieve a specific item by its ID.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `item_id` | integer | Yes | The ID of the item (must be > 0) |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | No | Optional search query (1-50 characters) |

**Examples:**

Get item with ID 1:
```
GET /api/items/1
```

Get item with query parameter:
```
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

---

### 4. Create Item
**POST** `/api/items/`

Create a new item in the system.

**Request Body:**
```json
{
  "name": "New Item",
  "description": "Optional description of the item",
  "status": "created"
}
```

**Request Schema:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | string | Yes | 1-100 characters | Name of the item |
| `description` | string | No | Max 500 characters | Detailed description |
| `status` | string | No | Default: "created" | Current status |

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/items/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My New Item",
    "description": "This is a new item"
  }'
```

**Response (201):**
```json
{
  "name": "My New Item",
  "description": "This is a new item",
  "status": "created"
}
```

---

## Response Models

### ItemResponse
Common response format for item operations.

```json
{
  "item_id": 1,
  "name": "Item Name",
  "description": "Item description",
  "status": "created",
  "query": null
}
```

**Fields:**
- `item_id` (integer, nullable): Unique identifier
- `name` (string, nullable): Item name
- `description` (string, nullable): Item description
- `status` (string): Operation or item status
- `query` (string, nullable): Query parameter from request

### HealthResponse
Health check response format.

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

**Fields:**
- `status` (string): Current health status
- `version` (string): API version

---

## HTTP Status Codes

| Code | Description | Example Scenario |
|------|-------------|------------------|
| 200 | OK | Successful GET request |
| 201 | Created | Successful POST request |
| 400 | Bad Request | Invalid parameters or body |
| 404 | Not Found | Item doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

---

## Authentication & Authorization

Currently, the API requires **no authentication** (demo mode).

For production, implement:
- OAuth 2.0
- API Keys
- JWT Bearer tokens

---

## Rate Limiting

Currently, **no rate limiting** is implemented (demo mode).

For production, consider:
- Rate limiting by IP
- Rate limiting by API key
- Throttling strategies

---

## CORS (Cross-Origin Resource Sharing)

Currently, CORS is not configured. To enable for frontend applications, add:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Error Handling

The API returns structured error responses:

```json
{
  "detail": [
    {
      "loc": ["body", "item", "name"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.str.regex"
    }
  ]
}
```

---

## Testing with cURL

### 1. Health Check
```bash
curl http://localhost:8000/api/health
```

### 2. Get Item
```bash
curl http://localhost:8000/api/items/1
curl http://localhost:8000/api/items/1?q=test
```

### 3. Create Item
```bash
curl -X POST http://localhost:8000/api/items/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Item","description":"Test Description"}'
```

---

## Testing with Python

```python
import requests

# Base URL
BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/api/health")
print(response.json())

# Get item
response = requests.get(f"{BASE_URL}/api/items/1")
print(response.json())

# Create item
payload = {
    "name": "New Item",
    "description": "Test description"
}
response = requests.post(f"{BASE_URL}/api/items/", json=payload)
print(response.json())
```

---

## Testing with Postman

1. Import the OpenAPI schema: `http://localhost:8000/api/v1/openapi.json`
2. Create a new collection from the schema
3. Use the generated requests for testing
4. Customize environment variables as needed

---

## Performance & Optimization

- **Async/Await**: All endpoints are asynchronous for better concurrency
- **Connection Pooling**: Configured for database connections
- **Caching**: Consider adding caching headers for GET requests
- **Compression**: FastAPI automatically compresses responses > 500 bytes

---

## Deployment

### Docker
```bash
docker build -t python-api:latest ./api
docker run -p 8000:8000 python-api:latest
```

### AWS Lambda
Configure lambda_handler.py as the entry point.

### Kubernetes
Deploy using the provided Docker image with appropriate ingress configuration.

---

## Monitoring & Logging

Key metrics to monitor:
- Request latency (p50, p95, p99)
- Error rates by endpoint
- API availability
- Response time trends

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAPI Specification](https://spec.openapis.org/oas/v3.0.3)
- [Pydantic Models](https://pydantic-docs.helpmanual.io/)

---

## API Changes & Versioning

### Current Version: 1.0.0

Versioning strategy:
- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes

Future versions will be available at:
- `/api/v2/` (when released)

---

## Support

For questions or issues:
1. Check the interactive documentation at `/docs`
2. Review this documentation
3. Check API logs for errors
4. Contact: support@example.com

---

*Last Updated: January 5, 2026*
