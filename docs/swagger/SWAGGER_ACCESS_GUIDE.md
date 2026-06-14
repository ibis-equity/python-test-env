# 🎯 Swagger/OpenAPI Access Guide

## 🚀 Quick Start - Access Swagger UI Now!

### Step 1: Start the FastAPI Server
```bash
cd "c:\Users\desha\Python Projects\python-test-env"
.\.venv\Scripts\python.exe -m uvicorn src.fast_api:app --reload
```

### Step 2: Open Swagger UI in Browser
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

## 📍 Available Documentation URLs

### Interactive Swagger UI (Recommended)
- **URL:** http://localhost:8000/docs
- **Type:** Interactive API explorer
- **Features:** Test endpoints, see responses, download spec
- **Best for:** Development and testing

### Alternative: ReDoc (Read-only)
- **URL:** http://localhost:8000/redoc
- **Type:** Beautiful static documentation
- **Features:** Browse endpoints, see models, download spec
- **Best for:** Reading/sharing documentation

### OpenAPI JSON Schema
- **URL:** http://localhost:8000/api/v1/openapi.json
- **Type:** Machine-readable specification
- **Features:** Import to tools, generate clients
- **Best for:** Automation and CI/CD

### Local OpenAPI File
- **File:** `openapi.json` (21.3 KB)
- **Location:** Project root directory
- **Usage:** Use with Swagger Editor, Postman, etc.

---

## 📚 API Endpoints at a Glance

### All Endpoints in Swagger
When you open Swagger UI, you'll see these endpoints:

```
GET /
    └─ Welcome endpoint

GET /api/health
    └─ Health check endpoint

GET /api/items/{item_id}
    └─ Get item by ID

POST /api/items/
    └─ Create a new item

GET /api/aws-info
    └─ Get AWS environment info
```

---

## 🎮 Using Swagger UI

### 1. Try an Endpoint
1. Click on an endpoint (e.g., "GET /api/health")
2. Click "Try it out"
3. Fill in parameters if needed
4. Click "Execute"
5. See the response below

### 2. Create an Item
1. Click "POST /api/items/"
2. Click "Try it out"
3. In request body, enter:
```json
{
  "name": "My First Item",
  "description": "Created via Swagger",
  "status": "active"
}
```
4. Click "Execute"
5. See response with status 201

### 3. Get Item Details
1. Click "GET /api/items/{item_id}"
2. Click "Try it out"
3. Enter item_id: `1`
4. (Optional) Enter query parameter: `q=test`
5. Click "Execute"
6. See response

### 4. Download OpenAPI Spec
1. In Swagger UI, look for download button (top right)
2. Or use: `/api/v1/openapi.json` directly

---

## 📋 What You Can Do in Swagger UI

### ✅ Testing
- Execute real API calls
- Send different parameters
- View response codes
- See response bodies

### ✅ Documentation
- Read endpoint descriptions
- View required parameters
- See data models
- Check examples

### ✅ Learning
- Explore API structure
- Understand data formats
- See authentication requirements
- Learn response formats

### ✅ Integration
- Download OpenAPI spec
- Import to Postman
- Generate client code
- Create API documentation

---

## 🔗 Integration Examples

### Import to Postman
1. Download `openapi.json` from Swagger UI
2. In Postman: File → Import → Upload file
3. All endpoints will be imported as collection

### Import to Swagger Editor
1. Visit https://editor.swagger.io/
2. File → Import URL
3. Use: `http://localhost:8000/api/v1/openapi.json`
4. Get interactive editor

### Generate Python Client
```bash
pip install openapi-python-client
openapi-python-client generate --url http://localhost:8000/api/v1/openapi.json
```

### Generate TypeScript Client
```bash
npm install -D @openapitools/openapi-generator-cli
openapi-generator-cli generate -i http://localhost:8000/api/v1/openapi.json -g typescript-axios -o ./src/api
```

---

## 🧪 Testing Common Scenarios

### Scenario 1: Create Item and View It
```
1. POST /api/items/
   Input: {"name": "Widget", "description": "A widget"}
   Result: 201 Created

2. GET /api/items/1
   See the created item
   Result: 200 OK
```

### Scenario 2: Validate Constraints
```
1. POST /api/items/
   Input: {"name": ""}  (empty name)
   Result: 422 Validation Error

2. POST /api/items/
   Input: {"name": "a" * 101}  (too long)
   Result: 422 Validation Error
```

### Scenario 3: Query Parameters
```
1. GET /api/items/1?q=search
   See query in response
   Result: 200 OK

2. GET /api/items/1?q=a_very_long_search_query_more_than_50_chars
   Result: 422 Validation Error
```

---

## 📊 API Documentation Structure

When you access Swagger UI, you'll see:

### Top Section
- API Title: "Python API"
- Version: "1.0.0"
- Description: API overview
- Contact: API Support info

### Endpoints Section
- List of all endpoints
- Grouped by tags (General, Items, Health, AWS)
- Color-coded by HTTP method
- Summary for each endpoint

### Try It Out
- Parameter inputs
- Request body editor
- Execute button
- Response display

### Models Section
- Data model definitions
- Field types and descriptions
- Required vs optional fields
- Validation constraints

---

## 🔐 Authentication & Authorization

### Current Status
- No authentication required (demo mode)
- All endpoints publicly accessible

### To Add Authentication
Add Bearer token header:
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/api/items/")
async def get_items(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    # Validate token
    return items
```

---

## 📈 API Specification Details

### OpenAPI Version
3.1.0 (latest standard)

### Info Object
- Title: Python API
- Version: 1.0.0
- Description: Complete API overview
- License: MIT
- Contact: support@example.com

### Paths Object
All 5 endpoints documented:
- GET /
- GET /api/health
- GET /api/items/{item_id}
- POST /api/items/
- GET /api/aws-info

### Components (Schemas)
- Item
- ItemResponse
- HealthResponse

---

## 🎨 Swagger UI Customization

### Change Swagger UI Theme
Edit `src/fast_api.py`:
```python
app = FastAPI(
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 1,
        "persistAuthorization": True,
        "displayOperationId": False,
        "docExpansion": "none",  # "list", "full", "none"
        "deepLinking": True,
        "filter": True,
        "showExtensions": False,
        "tryItOutEnabled": True,
    }
)
```

### Disable ReDoc
```python
app = FastAPI(redoc_url=None)
```

### Custom Logo/Title
```python
app = FastAPI(
    title="My API",
    swagger_ui_parameters={
        "url": "/custom-logo.png",
    }
)
```

---

## 🔍 Searching in Swagger UI

1. Use browser Ctrl+F to search
2. Search for:
   - Endpoint names (/api/items)
   - HTTP methods (POST, GET)
   - Parameter names (item_id)
   - Model names (Item, ItemResponse)

---

## 🐛 Troubleshooting Swagger Access

### Swagger UI Not Loading
**Problem:** Page shows "Swagger UI is not available"

**Solutions:**
1. Verify server is running
2. Check URL: http://localhost:8000/docs
3. Check console for errors
4. Restart server

### Can't Execute Requests
**Problem:** "Connection refused" error

**Solutions:**
1. Verify server is running
2. Check CORS settings
3. Use direct URLs instead
4. Try ReDoc instead (/redoc)

### OpenAPI JSON Invalid
**Problem:** Swagger shows errors

**Solutions:**
1. Check FastAPI version compatibility
2. Validate response models
3. Check endpoint decorators
4. See console output for errors

### Port Already in Use
**Problem:** Port 8000 in use

**Solution:**
```bash
.\.venv\Scripts\python.exe -m uvicorn src.fast_api:app --port 8001
```

Then access: http://localhost:8001/docs

---

## 📱 Mobile/Remote Access

### Local Network Access
From another computer on same network:
```
http://<YOUR_IP>:8000/docs
```

Find your IP:
```bash
ipconfig
```

### Remote Server Access
With HTTPS enabled:
```
https://api.example.com/docs
```

---

## 🔗 Useful Links

### When You Have Server Running

| Link | Purpose |
|------|---------|
| http://localhost:8000/ | Welcome page |
| http://localhost:8000/docs | **Swagger UI** |
| http://localhost:8000/redoc | ReDoc documentation |
| http://localhost:8000/api/v1/openapi.json | OpenAPI spec |

### External Tools

| Tool | Purpose |
|------|---------|
| https://editor.swagger.io | Swagger Editor |
| https://www.postman.com | API testing |
| https://www.insomnia.rest | REST client |
| https://restclient.org | Online REST client |

---

## 📝 Quick Reference

### Start Server
```bash
cd project
.\.venv\Scripts\python.exe -m uvicorn src.fast_api:app --reload
```

### Access Swagger
```
Browser: http://localhost:8000/docs
```

### Get OpenAPI Spec
```
URL: http://localhost:8000/api/v1/openapi.json
File: openapi.json (in project root)
```

### Test in Browser
```bash
# Health check
curl http://localhost:8000/api/health

# Create item
curl -X POST http://localhost:8000/api/items/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Item"}'
```

---

## 🎓 Learning Path

### 5-Minute Quick Start
1. Start server
2. Open http://localhost:8000/docs
3. Try "GET /api/health"
4. Try "POST /api/items/"

### 15-Minute Deep Dive
1. Explore all endpoints in Swagger
2. Try each endpoint with different parameters
3. See how validation works
4. View response models

### 30-Minute Integration
1. Download openapi.json
2. Import to Postman
3. Generate client code
4. Set up for your project

---

## ✅ What's Included

- ✅ Swagger UI at /docs
- ✅ ReDoc at /redoc
- ✅ OpenAPI JSON schema
- ✅ All endpoints documented
- ✅ All models documented
- ✅ Try it out functionality
- ✅ Example requests/responses
- ✅ Full parameter documentation
- ✅ Response code documentation

---

## 📞 Next Steps

1. **Start the server:**
   ```bash
   .\.venv\Scripts\python.exe -m uvicorn src.fast_api:app --reload
   ```

2. **Open Swagger UI:**
   👉 [http://localhost:8000/docs](http://localhost:8000/docs)

3. **Try an endpoint:**
   - Click any endpoint
   - Click "Try it out"
   - Click "Execute"

4. **Explore more:**
   - See all endpoints
   - Try POST endpoint to create items
   - View response models
   - Download OpenAPI spec

---

**Swagger/OpenAPI Access Guide**  
**Version:** 1.0  
**Created:** January 19, 2026  
**Status:** ✅ Ready to Use
