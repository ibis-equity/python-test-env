# Salesforce API Integration

A comprehensive Salesforce REST API integration built with FastAPI, providing async/await support for CRUD operations and advanced querying capabilities.

## Features

- **OAuth 2.0 Authentication**: Secure authentication with Salesforce
- **Async Operations**: High-performance async/await implementation using httpx
- **CRUD Operations**: Create, Read, Update, Delete for Accounts, Contacts, and Opportunities
- **SOQL Support**: Execute Salesforce Object Query Language queries
- **Batch Operations**: Create multiple records in batch
- **Error Handling**: Comprehensive error handling and logging
- **Type Safety**: Full Pydantic models for data validation
- **API Documentation**: Interactive Swagger UI and ReDoc

## Project Structure

```
src/
├── salesforce_api.py          # Core Salesforce client implementation
├── salesforce_fastapi.py      # FastAPI integration and endpoints
├── test_salesforce_api.py     # Comprehensive test suite
└── requirements.txt           # Python dependencies
```

## Installation

### Prerequisites

- Python 3.8+
- Salesforce account with OAuth credentials

### Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment variables** (create `.env` file):
```env
SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_USERNAME=your_username
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_security_token
```

## Salesforce OAuth Setup

### Create Connected App

1. Go to **Setup** > **Apps** > **App Manager**
2. Click **New Connected App**
3. Fill in the required fields:
   - **Connected App Name**: Your App Name
   - **API Name**: Will auto-populate
   - **Contact Email**: Your email
4. Enable OAuth Settings:
   - **Callback URL**: `https://localhost:3000/callback` (or your redirect URI)
   - **Selected OAuth Scopes**:
     - `api` (Access and manage your data)
     - `refresh_token` (Obtain a refresh token)

5. Save and note your:
   - Client ID
   - Client Secret

### Get Security Token

1. Go to **Settings** > **Reset My Security Token**
2. Check your email for the token
3. Append to password when authenticating

## Usage

### Start the API Server

```bash
python -m uvicorn salesforce_fastapi:app --reload
```

The API will be available at `http://localhost:8000`

**Interactive Documentation**:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Core Salesforce Client

```python
from salesforce_api import SalesforceClient, SalesforceAccount
import asyncio

async def main():
    # Initialize client
    client = SalesforceClient()
    
    # Authenticate
    success = await client.authenticate()
    if not success:
        raise Exception("Authentication failed")
    
    # Create account
    account = SalesforceAccount(
        Name="Acme Corp",
        Phone="555-1234",
        Industry="Technology"
    )
    result = await client.create_account(account)
    print(f"Created account: {result.record_id}")
    
    # Query accounts
    soql = "SELECT Id, Name FROM Account LIMIT 10"
    results = await client.query(soql)
    print(f"Found {results.totalSize} accounts")

asyncio.run(main())
```

## API Endpoints

### Health Check

- **GET** `/health` - Check API and Salesforce connection status

### Accounts

- **POST** `/accounts` - Create a new account
- **GET** `/accounts/{account_id}` - Get account details
- **PATCH** `/accounts/{account_id}` - Update an account
- **DELETE** `/accounts/{account_id}` - Delete an account
- **GET** `/accounts/search/by-industry?industry=Technology` - Search by industry

### Contacts

- **POST** `/contacts` - Create a new contact
- **GET** `/contacts/{contact_id}` - Get contact details
- **PATCH** `/contacts/{contact_id}` - Update a contact
- **DELETE** `/contacts/{contact_id}` - Delete a contact
- **GET** `/contacts/account/{account_id}` - Get contacts for an account

### Opportunities

- **POST** `/opportunities` - Create a new opportunity
- **GET** `/opportunities/{opportunity_id}` - Get opportunity details
- **PATCH** `/opportunities/{opportunity_id}` - Update an opportunity
- **DELETE** `/opportunities/{opportunity_id}` - Delete an opportunity
- **GET** `/opportunities/search/by-stage?stage=Closed%20Won` - Search by stage

### Advanced Queries

- **POST** `/query` - Execute SOQL query

**Example**:
```json
{
  "soql": "SELECT Id, Name, Amount FROM Opportunity WHERE StageName = 'Closed Won'"
}
```

### Batch Operations

- **POST** `/batch/accounts` - Create multiple accounts
- **POST** `/batch/contacts` - Create multiple contacts
- **POST** `/batch/opportunities` - Create multiple opportunities

**Example**:
```json
[
  {
    "Name": "Company 1",
    "Phone": "555-0001"
  },
  {
    "Name": "Company 2",
    "Phone": "555-0002"
  }
]
```

## Data Models

### SalesforceAccount

```python
{
  "Id": "001xx000003DHP1",  # Auto-assigned
  "Name": "Company Name",
  "Phone": "555-1234",
  "Website": "https://example.com",
  "Industry": "Technology",
  "BillingCity": "San Francisco",
  "BillingCountry": "USA"
}
```

### SalesforceContact

```python
{
  "Id": "003xx000004TMZ1",  # Auto-assigned
  "FirstName": "John",
  "LastName": "Doe",
  "Email": "john@example.com",
  "Phone": "555-1234",
  "AccountId": "001xx000003DHP1"
}
```

### SalesforceOpportunity

```python
{
  "Id": "006xx000007MZF1",  # Auto-assigned
  "Name": "Deal Name",
  "Amount": 100000.0,
  "StageName": "Closed Won",
  "CloseDate": "2024-12-31",
  "AccountId": "001xx000003DHP1"
}
```

## Testing

### Run Tests

```bash
pytest test_salesforce_api.py -v
```

### Test Coverage

```bash
pytest test_salesforce_api.py --cov=salesforce_api --cov-report=html
```

Tests include:
- Authentication flow
- CRUD operations for all objects
- Query operations
- Error handling
- Data model validation
- Batch operations

## Advanced Usage

### Custom SOQL Queries

```python
# Complex query with multiple conditions
soql = """
SELECT Id, Name, Amount, StageName, AccountId
FROM Opportunity
WHERE StageName IN ('Closed Won', 'Negotiation/Review')
AND Amount > 50000
AND CloseDate <= NEXT_N_DAYS:90
ORDER BY Amount DESC
"""

results = await client.query(soql)
```

### Error Handling

```python
from salesforce_api import SalesforceClient

try:
    client = SalesforceClient()
    success = await client.authenticate()
    if not success:
        print("Authentication failed - check credentials")
except Exception as e:
    print(f"Error: {str(e)}")
```

### Batch Processing

```python
accounts = [
    SalesforceAccount(Name="Company 1", Industry="Tech"),
    SalesforceAccount(Name="Company 2", Industry="Finance"),
    SalesforceAccount(Name="Company 3", Industry="Retail"),
]

results = []
for account in accounts:
    result = await client.create_account(account)
    results.append(result)

successful = [r for r in results if r.success]
failed = [r for r in results if not r.success]
print(f"Created {len(successful)} accounts, {len(failed)} failed")
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SALESFORCE_INSTANCE_URL` | Your Salesforce instance URL | Yes |
| `SALESFORCE_CLIENT_ID` | OAuth 2.0 Client ID | Yes |
| `SALESFORCE_CLIENT_SECRET` | OAuth 2.0 Client Secret | Yes |
| `SALESFORCE_USERNAME` | Salesforce username | Yes |
| `SALESFORCE_PASSWORD` | Salesforce password | Yes |
| `SALESFORCE_SECURITY_TOKEN` | Security token (if required) | No |

## Performance Tips

1. **Connection Pooling**: The client uses httpx with connection pooling for optimal performance
2. **Async Operations**: Use async/await for non-blocking I/O
3. **Batch Operations**: Use batch endpoints for multiple record creation
4. **Query Optimization**: Use specific field selections in SOQL queries

## Salesforce API Limits

- **API Calls**: 1,000 per 15 minutes (varies by edition)
- **Batch Size**: Recommend 200 records per batch operation
- **Query Limits**: No limit on number of queries but plan calls accordingly

## Integration with Azure

The API is ready for Azure deployment:

1. **Container**: Can be containerized with provided Dockerfile
2. **Azure App Service**: Deploy using `azure-pipelines.yml`
3. **Key Vault**: Store sensitive credentials in Azure Key Vault
4. **Managed Identity**: Use for authentication to Azure services

## Troubleshooting

### Authentication Fails

1. Verify credentials in `.env` file
2. Check Salesforce instance URL format: `https://instance.salesforce.com`
3. Ensure security token is appended to password if required
4. Verify connected app is enabled and has correct callback URL

### Connection Timeouts

1. Check internet connectivity
2. Verify Salesforce instance is accessible
3. Increase timeout in httpx client
4. Check Salesforce API rate limits

### Record Not Found

1. Verify record ID format (18 characters alphanumeric)
2. Check if record still exists in Salesforce
3. Verify user permissions to access record
4. Check organization limits aren't exceeded

## Best Practices

1. **Use Environment Variables**: Never hardcode credentials
2. **Error Handling**: Always wrap API calls in try-except blocks
3. **Logging**: Enable logging for debugging
4. **Testing**: Write tests for custom operations
5. **Rate Limiting**: Implement backoff strategy for API limits
6. **Validation**: Use Pydantic models for data validation
7. **Async**: Use async operations for better performance

## Additional Resources

- [Salesforce REST API Documentation](https://developer.salesforce.com/docs/api/rest/)
- [SOQL and SOSL Reference](https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [httpx Documentation](https://www.python-httpx.org/)

## License

This integration is provided as-is for use with Salesforce.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review test cases for usage examples
3. Enable debug logging for detailed error messages
4. Contact your Salesforce administrator for permission issues
