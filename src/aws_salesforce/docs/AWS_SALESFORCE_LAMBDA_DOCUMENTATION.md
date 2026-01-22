# AWS Salesforce Lambda Documentation

## Overview

`aws_salesforce_lambda.py` is a comprehensive AWS Lambda function that provides REST API endpoints for integrating with Salesforce CRM. It leverages the Salesforce REST API to perform CRUD operations on Accounts, Contacts, and Opportunities, as well as execute SOQL queries and batch operations.

**Version:** 1.0.0  
**Language:** Python 3.7+  
**Dependencies:** boto3, salesforce-bulk, simple-salesforce, asyncio

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

The Lambda function uses a **router pattern** to handle multiple endpoints with different HTTP methods. Each endpoint has a dedicated handler function that:

1. Parses the incoming event
2. Validates required parameters
3. Creates a Salesforce client connection
4. Executes the requested operation asynchronously
5. Returns a standardized response

### Async/Await Pattern

The function employs asynchronous operations for Salesforce API calls to improve performance:
- Uses `asyncio` event loops for async execution
- `run_async()` helper function manages event loop lifecycle
- All Salesforce client operations are awaitable

### Layered Architecture

```
API Gateway (HTTP Request)
    ↓
Router Function (Path & Method Matching)
    ↓
Handler Functions (Business Logic)
    ↓
Salesforce Client (API Integration)
    ↓
Salesforce CRM (Data Operations)
```

---

## Core Components

### 1. LambdaResponse Class

Helper class for standardized Lambda response formatting.

**Methods:**

#### `success(data, status_code=200)`
Returns a successful response with the provided data.

```python
response = LambdaResponse.success({
    "record_id": "001xx000003DHP1",
    "account_name": "Acme Corp"
}, 201)
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
    "error": "Account not found",
    "error_code": "NOT_FOUND",
    "timestamp": "2025-01-15T10:30:00.000000"
  },
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### 2. Async Helper Functions

#### `run_async(coro: Coroutine) -> Any`
Executes asynchronous coroutines in Lambda's synchronous context.

```python
result = run_async(get_client())
```

#### `get_client() -> SalesforceClient`
Creates and authenticates a Salesforce client connection.

**Raises:**
- `Exception`: If authentication fails

---

## API Endpoints

All endpoints use the router pattern and are designed to work with AWS API Gateway.

### Accounts Management

#### Create Account
**Endpoint:** `POST /accounts`

Creates a new Salesforce Account record.

**Request Body:**
```json
{
  "Name": "Acme Corporation",
  "Phone": "555-123-4567",
  "Website": "https://acme.com",
  "Industry": "Technology",
  "BillingCity": "San Francisco",
  "BillingCountry": "USA"
}
```

**Response (201 Created):**
```json
{
  "statusCode": 201,
  "body": {
    "success": true,
    "data": {
      "record_id": "001xx000003DHP1",
      "account_name": "Acme Corporation"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Error Codes:**
- `400`: Bad request, validation failed
- `500`: Salesforce API error

---

#### Get Account
**Endpoint:** `GET /accounts/{account_id}`

Retrieves a specific Salesforce Account by ID.

**Path Parameters:**
- `account_id` (string, required): Salesforce Account ID (18-character alphanumeric)

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "Id": "001xx000003DHP1",
      "Name": "Acme Corporation",
      "Phone": "555-123-4567",
      "Website": "https://acme.com",
      "Industry": "Technology",
      "BillingCity": "San Francisco",
      "BillingCountry": "USA",
      "CreatedDate": "2025-01-01T00:00:00.000+0000"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Error Codes:**
- `400`: Missing account_id parameter
- `404`: Account not found
- `500`: Salesforce API error

---

#### Update Account
**Endpoint:** `PATCH /accounts/{account_id}`

Updates an existing Salesforce Account.

**Path Parameters:**
- `account_id` (string, required): Salesforce Account ID

**Request Body:** (All fields optional)
```json
{
  "Name": "Acme Corporation Updated",
  "Phone": "555-987-6543",
  "Website": "https://newacme.com",
  "Industry": "Software",
  "BillingCity": "Seattle",
  "BillingCountry": "USA"
}
```

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "record_id": "001xx000003DHP1",
      "status": "updated"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

---

#### Delete Account
**Endpoint:** `DELETE /accounts/{account_id}`

Deletes a Salesforce Account permanently.

**Path Parameters:**
- `account_id` (string, required): Salesforce Account ID

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "record_id": "001xx000003DHP1",
      "status": "deleted"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Note:** Deleted records may still exist in Salesforce's recycle bin for 15 days.

---

### Contacts Management

#### Create Contact
**Endpoint:** `POST /contacts`

Creates a new Salesforce Contact record.

**Request Body:**
```json
{
  "FirstName": "John",
  "LastName": "Doe",
  "Email": "john.doe@acme.com",
  "Phone": "555-123-4567",
  "AccountId": "001xx000003DHP1"
}
```

**Response (201 Created):**
```json
{
  "statusCode": 201,
  "body": {
    "success": true,
    "data": {
      "record_id": "003xx000004DAA1",
      "contact_name": "John Doe"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

---

#### Get Contact
**Endpoint:** `GET /contacts/{contact_id}`

Retrieves a specific Salesforce Contact.

**Path Parameters:**
- `contact_id` (string, required): Salesforce Contact ID

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "Id": "003xx000004DAA1",
      "FirstName": "John",
      "LastName": "Doe",
      "Email": "john.doe@acme.com",
      "Phone": "555-123-4567",
      "AccountId": "001xx000003DHP1",
      "CreatedDate": "2025-01-01T00:00:00.000+0000"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

---

#### Update Contact
**Endpoint:** `PATCH /contacts/{contact_id}`

Updates an existing Contact.

**Path Parameters:**
- `contact_id` (string, required): Salesforce Contact ID

**Request Body:** (All fields optional)
```json
{
  "FirstName": "Jonathan",
  "LastName": "Smith",
  "Email": "jonathan.smith@acme.com",
  "Phone": "555-987-6543"
}
```

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "record_id": "003xx000004DAA1",
      "status": "updated"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

---

#### Delete Contact
**Endpoint:** `DELETE /contacts/{contact_id}`

Deletes a Salesforce Contact.

**Path Parameters:**
- `contact_id` (string, required): Salesforce Contact ID

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "record_id": "003xx000004DAA1",
      "status": "deleted"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

---

### Opportunities Management

#### Create Opportunity
**Endpoint:** `POST /opportunities`

Creates a new Salesforce Opportunity record.

**Request Body:**
```json
{
  "Name": "Enterprise Deal",
  "Amount": 150000.00,
  "StageName": "Prospecting",
  "CloseDate": "2025-12-31",
  "AccountId": "001xx000003DHP1"
}
```

**Standard Opportunity Stages:**
- Prospecting
- Qualification
- Needs Analysis
- Value Proposition
- Proposal/Price Quote
- Negotiation/Review
- Closed Won
- Closed Lost

**Response (201 Created):**
```json
{
  "statusCode": 201,
  "body": {
    "success": true,
    "data": {
      "record_id": "006xx000003DMIA1",
      "opportunity_name": "Enterprise Deal",
      "amount": 150000.00
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

---

#### Get Opportunity
**Endpoint:** `GET /opportunities/{opportunity_id}`

Retrieves a specific Salesforce Opportunity.

**Path Parameters:**
- `opportunity_id` (string, required): Salesforce Opportunity ID

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "Id": "006xx000003DMIA1",
      "Name": "Enterprise Deal",
      "Amount": 150000.00,
      "StageName": "Proposal/Price Quote",
      "CloseDate": "2025-12-31",
      "AccountId": "001xx000003DHP1",
      "Probability": 75,
      "CreatedDate": "2025-01-01T00:00:00.000+0000"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

---

#### Update Opportunity
**Endpoint:** `PATCH /opportunities/{opportunity_id}`

Updates an existing Opportunity.

**Path Parameters:**
- `opportunity_id` (string, required): Salesforce Opportunity ID

**Request Body:** (All fields optional)
```json
{
  "Name": "Enterprise Deal - Updated",
  "Amount": 200000.00,
  "StageName": "Negotiation/Review",
  "CloseDate": "2025-06-30"
}
```

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "record_id": "006xx000003DMIA1",
      "status": "updated"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

---

#### Delete Opportunity
**Endpoint:** `DELETE /opportunities/{opportunity_id}`

Deletes a Salesforce Opportunity.

**Path Parameters:**
- `opportunity_id` (string, required): Salesforce Opportunity ID

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "record_id": "006xx000003DMIA1",
      "status": "deleted"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

---

### Advanced Operations

#### Execute SOQL Query
**Endpoint:** `POST /query`

Executes a Salesforce Object Query Language (SOQL) query.

**Request Body:**
```json
{
  "soql": "SELECT Id, Name, Phone FROM Account WHERE Industry = 'Technology' LIMIT 100"
}
```

**Response (200 OK):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "total_size": 25,
      "done": true,
      "records": [
        {
          "Id": "001xx000003DHP1",
          "Name": "Acme Corporation",
          "Phone": "555-123-4567"
        },
        {
          "Id": "001xx000003DHP2",
          "Name": "TechCorp Inc",
          "Phone": "555-987-6543"
        }
      ]
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Common SOQL Examples:**

Get all accounts with their contacts:
```sql
SELECT Id, Name, (SELECT Id, FirstName, LastName FROM Contacts) FROM Account
```

Get high-value opportunities:
```sql
SELECT Id, Name, Amount, StageName FROM Opportunity 
WHERE Amount > 100000 AND StageName != 'Closed Lost'
ORDER BY Amount DESC
```

Count records by type:
```sql
SELECT COUNT() FROM Account WHERE Industry = 'Technology'
```

**Error Codes:**
- `400`: Invalid SOQL syntax or missing query parameter
- `500`: Salesforce API error

---

#### Batch Create Accounts
**Endpoint:** `POST /batch/accounts`

Creates multiple accounts in a single API call.

**Request Body:**
```json
[
  {
    "Name": "Company 1",
    "Phone": "555-0001",
    "Industry": "Technology"
  },
  {
    "Name": "Company 2",
    "Phone": "555-0002",
    "Industry": "Manufacturing"
  },
  {
    "Name": "Company 3",
    "Phone": "555-0003",
    "Industry": "Finance"
  }
]
```

**Response (201 Created):**
```json
{
  "statusCode": 201,
  "body": {
    "success": true,
    "data": {
      "total": 3,
      "successful": 3,
      "failed": 0,
      "results": [
        {
          "success": true,
          "record_id": "001xx000003DHP1",
          "error": null
        },
        {
          "success": true,
          "record_id": "001xx000003DHP2",
          "error": null
        },
        {
          "success": true,
          "record_id": "001xx000003DHP3",
          "error": null
        }
      ]
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Partial Success Example:**
```json
{
  "statusCode": 201,
  "body": {
    "success": true,
    "data": {
      "total": 3,
      "successful": 2,
      "failed": 1,
      "results": [
        {"success": true, "record_id": "001xx000003DHP1", "error": null},
        {"success": false, "record_id": null, "error": "Required field missing: Name"},
        {"success": true, "record_id": "001xx000003DHP3", "error": null}
      ]
    }
  }
}
```

---

### Health Check

#### Health Check
**Endpoint:** `GET /health`

Performs a health check and validates Salesforce connectivity.

**Response (200 OK - Healthy):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "status": "healthy",
      "salesforce_connected": true,
      "function": "aws_salesforce_lambda",
      "version": "1.0.0"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

**Response (200 OK - Degraded):**
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "data": {
      "status": "degraded",
      "salesforce_connected": false,
      "error": "Authentication failed: Invalid credentials"
    },
    "timestamp": "2025-01-15T10:30:00.000000"
  }
}
```

---

## Request/Response Format

### Request Format

All requests follow the AWS Lambda/API Gateway event model:

```python
{
  "httpMethod": "POST",
  "path": "/accounts",
  "body": "{\"Name\": \"Acme Corp\"}",
  "headers": {
    "Content-Type": "application/json"
  },
  "pathParameters": {
    "account_id": "001xx000003DHP1"  # For path-based IDs
  },
  "queryStringParameters": {
    "filter": "value"  # Optional query parameters
  }
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
| 200 | OK | Successful GET/PATCH request |
| 201 | Created | Successful POST request |
| 400 | Bad Request | Invalid input, missing parameters |
| 404 | Not Found | Record doesn't exist |
| 500 | Internal Server Error | Salesforce API error, auth failure |

---

## Error Handling

### Error Response Structure

```json
{
  "statusCode": 400,
  "body": {
    "success": false,
    "error": "Human-readable error message",
    "error_code": "MACHINE_READABLE_CODE",
    "timestamp": "2025-01-15T10:30:00.000000"
  },
  "headers": {
    "Content-Type": "application/json"
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| MISSING_PARAMETERS | Required parameters not provided |
| NOT_FOUND | Record doesn't exist in Salesforce |
| QUERY_ERROR | SOQL query syntax error |
| AUTH_ERROR | Salesforce authentication failed |
| INTERNAL_ERROR | Unhandled exception in Lambda |
| INVALID_JSON | Malformed JSON in request body |

### Error Handling Strategy

1. **Validation Errors** → Return 400 with specific error code
2. **Not Found** → Return 404 with error message
3. **Salesforce Errors** → Return 500 with error details
4. **Async Errors** → Caught in try/except, logged, returned as 500

```python
try:
    body = json.loads(event.get("body", "{}"))
except json.JSONDecodeError:
    return LambdaResponse.error("Invalid JSON in request body", 400, "INVALID_JSON")
except Exception as e:
    logger.error(f"Error: {str(e)}")
    return LambdaResponse.error(str(e), 500, "INTERNAL_ERROR")
```

---

## Deployment

### Prerequisites

1. AWS Account with Lambda permissions
2. Salesforce account with API enabled
3. Python 3.7+ runtime
4. Required dependencies installed

### Step 1: Prepare the Package

```bash
# Create deployment directory
mkdir lambda-deployment
cd lambda-deployment

# Copy source files
cp aws_salesforce_lambda.py .
cp salesforce_api.py .

# Install dependencies
pip install -r requirements.txt -t .
```

### Step 2: Create Lambda Function

**Using AWS Console:**
1. Navigate to Lambda → Create Function
2. Runtime: Python 3.11
3. Handler: `aws_salesforce_lambda.router`
4. Upload ZIP file with all files

**Using AWS CLI:**
```bash
zip -r lambda-deployment.zip .
aws lambda create-function \
  --function-name salesforce-api \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler aws_salesforce_lambda.router \
  --zip-file fileb://lambda-deployment.zip
```

### Step 3: Configure API Gateway

1. Create REST API in API Gateway
2. Create resources for each endpoint
3. Create methods (GET, POST, PATCH, DELETE)
4. Integrate with Lambda function
5. Deploy to stage (dev, prod)

**API Gateway Integration:**
```
Resource: /accounts/{account_id}
├── GET → get_account_handler
├── PATCH → update_account_handler
└── DELETE → delete_account_handler
```

### Step 4: Set Environment Variables

In Lambda Configuration → Environment Variables:
```
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_token
SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
```

### Step 5: Configure IAM Role

Ensure Lambda execution role has:
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`
- (Optional) `secretsmanager:GetSecretValue` for secure credential storage

---

## Configuration

### Environment Variables

Required environment variables must be set in Lambda:

| Variable | Description | Example |
|----------|-------------|---------|
| SALESFORCE_CLIENT_ID | OAuth Client ID | `3MVG9...` |
| SALESFORCE_CLIENT_SECRET | OAuth Secret | `abc123...` |
| SALESFORCE_USERNAME | Salesforce username | `admin@acme.com` |
| SALESFORCE_PASSWORD | Salesforce password | `SecurePass123!` |
| SALESFORCE_SECURITY_TOKEN | Security token | `abc123def456` |
| SALESFORCE_INSTANCE_URL | Instance URL | `https://acme.salesforce.com` |

### Secure Configuration with AWS Secrets Manager

**Recommended for Production:**

1. Store credentials in Secrets Manager:
```bash
aws secretsmanager create-secret \
  --name salesforce/credentials \
  --secret-string '{
    "client_id": "...",
    "client_secret": "...",
    "username": "...",
    "password": "...",
    "security_token": "..."
  }'
```

2. Modify Lambda to use Secrets Manager:
```python
import boto3
import json

secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='salesforce/credentials')
credentials = json.loads(secret['SecretString'])
```

### Lambda Configuration

Recommended settings:
- **Memory:** 256 MB - 512 MB
- **Timeout:** 30 seconds
- **Ephemeral Storage:** 512 MB
- **Architecture:** x86_64

---

## Usage Examples

### Example 1: Create Account via cURL

```bash
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/prod/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "Name": "Acme Corporation",
    "Phone": "555-123-4567",
    "Website": "https://acme.com",
    "Industry": "Technology",
    "BillingCity": "San Francisco",
    "BillingCountry": "USA"
  }'
```

### Example 2: Get Account via Python

```python
import requests

api_url = "https://your-api.execute-api.us-east-1.amazonaws.com/prod"
account_id = "001xx000003DHP1"

response = requests.get(f"{api_url}/accounts/{account_id}")
account = response.json()

print(f"Account: {account['data']['Name']}")
print(f"Phone: {account['data']['Phone']}")
```

### Example 3: Update Contact via JavaScript

```javascript
const apiUrl = 'https://your-api.execute-api.us-east-1.amazonaws.com/prod';
const contactId = '003xx000004DAA1';

const updateData = {
  FirstName: 'Jane',
  LastName: 'Smith',
  Email: 'jane.smith@acme.com'
};

fetch(`${apiUrl}/contacts/${contactId}`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(updateData)
})
.then(res => res.json())
.then(data => console.log('Contact updated:', data.data.record_id));
```

### Example 4: Execute SOQL Query via Python

```python
import requests
import json

api_url = "https://your-api.execute-api.us-east-1.amazonaws.com/prod"

soql = "SELECT Id, Name, Amount FROM Opportunity WHERE Amount > 100000 ORDER BY Amount DESC"

response = requests.post(
  f"{api_url}/query",
  headers={"Content-Type": "application/json"},
  json={"soql": soql}
)

results = response.json()
print(f"Found {results['data']['total_size']} opportunities")
for opp in results['data']['records']:
    print(f"- {opp['Name']}: ${opp['Amount']}")
```

### Example 5: Batch Create Accounts

```bash
curl -X POST https://your-api.execute-api.us-east-1.amazonaws.com/prod/batch/accounts \
  -H "Content-Type: application/json" \
  -d '[
    {
      "Name": "Tech Startup 1",
      "Industry": "Software",
      "Phone": "555-0001"
    },
    {
      "Name": "Tech Startup 2",
      "Industry": "SaaS",
      "Phone": "555-0002"
    },
    {
      "Name": "Tech Startup 3",
      "Industry": "Cloud",
      "Phone": "555-0003"
    }
  ]'
```

---

## Authentication

### Salesforce OAuth Flow

The `SalesforceClient` (from `salesforce_api.py`) handles authentication automatically:

1. **Obtain Credentials:**
   - OAuth Client ID/Secret (from Connected App)
   - Username and Password
   - Security Token (appended to password)

2. **Authentication Process:**
   ```
   Client ID + Secret + Username + (Password + Token)
   → Salesforce OAuth Endpoint
   → Access Token + Refresh Token
   → Set as default headers
   ```

3. **Token Management:**
   - Tokens typically valid for 2 hours
   - Refresh token used for renewal
   - Auto-refresh handled by client

### Setting Up OAuth in Salesforce

1. **Create Connected App:**
   - Setup → Apps → App Manager
   - New Connected App
   - Enable OAuth Settings
   - Set Redirect URI: `https://your-domain/callback`

2. **Get Credentials:**
   - Consumer Key (Client ID)
   - Consumer Secret (Client Secret)

3. **Generate Security Token:**
   - My Settings → Reset My Security Token
   - Token sent to email

### Adding Authorization Headers

For API Gateway integration with authorization:

```javascript
// Client-side request with API key
const apiKey = "your-api-key";
fetch('https://api-gateway/accounts', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${apiKey}` // Optional API key auth
  },
  body: JSON.stringify({...})
});
```

---

## Logging

### CloudWatch Logs

All operations are logged to CloudWatch with structured logging:

```python
logger.setLevel(logging.INFO)
logger.info("Successfully connected to Salesforce")
logger.error(f"Failed to create account: {str(e)}")
logger.warning("Health check: Salesforce connection failed")
```

### Log Examples

**Successful Account Creation:**
```
[2025-01-15 10:30:00] INFO - Created account: 001xx000003DHP1
```

**Failed Query:**
```
[2025-01-15 10:30:15] ERROR - Error executing query: Invalid SOQL syntax
```

**Health Check:**
```
[2025-01-15 10:30:30] INFO - Health check: Salesforce connection successful
```

### CloudWatch Insights Query

Find all errors in last hour:
```
fields @timestamp, @message, error_code
| filter @message like /ERROR/
| stats count() by error_code
```

Find slowest operations:
```
fields @duration
| stats avg(@duration) as avg_duration, max(@duration) as max_duration by @message
```

### Log Levels

- **DEBUG:** Detailed diagnostic info (not typically enabled)
- **INFO:** General informational messages
- **WARNING:** Warning conditions (e.g., degraded service)
- **ERROR:** Error messages with full context
- **CRITICAL:** Severe errors requiring immediate attention

---

## Best Practices

### 1. Error Handling
- Always wrap Salesforce calls in try/except
- Return specific error codes for different scenarios
- Log all errors with context

### 2. Performance
- Use async/await for Salesforce operations
- Batch operations when possible
- Consider caching frequently accessed data

### 3. Security
- Store credentials in AWS Secrets Manager
- Use IAM roles instead of hardcoded credentials
- Enable API Gateway authentication
- Validate all input parameters

### 4. Monitoring
- Set up CloudWatch alarms for error rates
- Monitor Lambda duration and memory usage
- Track API Gateway 4xx/5xx error rates

### 5. Testing
- Test with sample Salesforce data
- Test error scenarios (invalid IDs, auth failures)
- Load test before production deployment

---

## Troubleshooting

### Issue: "Failed to authenticate with Salesforce"

**Causes:**
- Invalid credentials
- Security token expired
- Connected App not approved
- IP whitelist restrictions

**Solution:**
```bash
# Verify credentials in Secrets Manager
aws secretsmanager get-secret-value --secret-id salesforce/credentials

# Reset security token in Salesforce
# Check API usage logs
```

### Issue: SOQL Query Returns Empty Results

**Causes:**
- Query syntax error
- No matching records
- User doesn't have access to fields

**Solution:**
```sql
-- Test query in Salesforce Developer Console first
-- Check object and field names (case-sensitive in some contexts)
-- Verify user permissions
```

### Issue: Timeout (Gateway Timeout)

**Causes:**
- Lambda timeout too short
- Salesforce API slow
- Network connectivity issue

**Solution:**
```python
# Increase Lambda timeout in configuration
# Optimize Salesforce queries
# Add query limits: SELECT ... LIMIT 1000
```

### Issue: Cold Start Performance

**Causes:**
- Lambda container initialization
- Salesforce client creation
- Dependency imports

**Solution:**
- Use provisioned concurrency
- Pre-warm Lambda with periodic invocations
- Move initialization outside handler

---

## Advanced Usage

### Custom Error Handling

Create custom exceptions:

```python
class SalesforceException(Exception):
    def __init__(self, message, error_code):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

# Usage
try:
    result = await client.get_account(account_id)
except SalesforceException as e:
    return LambdaResponse.error(e.message, 400, e.error_code)
```

### Extending with Custom Logic

Add business logic before Salesforce operations:

```python
def create_account_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    
    # Custom validation
    if not body.get("Name"):
        return LambdaResponse.error("Name is required", 400)
    
    # Business logic
    account_name = body.get("Name").upper()
    
    # Create in Salesforce
    account = SalesforceAccount(Name=account_name, ...)
    ...
```

### Database Auditing

Log all changes to DynamoDB:

```python
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
audit_table = dynamodb.Table('salesforce-audit')

def audit_change(operation, record_id, data):
    audit_table.put_item(Item={
        'timestamp': datetime.utcnow().isoformat(),
        'operation': operation,
        'record_id': record_id,
        'data': json.dumps(data)
    })

# Usage in handlers
if result.success:
    audit_change('CREATE_ACCOUNT', result.record_id, account.__dict__)
```

---

## Additional Resources

- [Salesforce REST API Documentation](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/)
- [SOQL Query Language Reference](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/)
- [AWS API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)

---

## Support & Maintenance

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-15 | Initial release |

### Contributing

To extend this Lambda function:
1. Add new handler function
2. Register in HANDLERS dictionary
3. Update API Gateway resources
4. Test in dev environment
5. Deploy to production

### Contact

For issues or questions, refer to the `SALESFORCE_README.md` in the project root.
