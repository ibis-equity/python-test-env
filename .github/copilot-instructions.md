# Copilot instructions for this repository

## Architecture overview
- This repo is a collection of integration examples centered around FastAPI plus AWS/Azure/Salesforce helpers.
- Primary FastAPI app: `src/fast_api.py` (public API, Pydantic models, and AWS Lambda wrapper via `Mangum`).
- AWS API Gateway utilities live in `src/aws_gateway_integration.py` (event parsing, response formatting, CORS/auth helpers, request logging).
- Standalone Lambda handlers:
  - `src/lambda_api.py` reads from S3 using query params.
  - `src/lambda_datastream.py` processes Kinesis records → Pandas → Parquet → S3, and updates Glue tables.
- Azure integrations in `src/azure_integration.py` (Blob, Cosmos DB, Key Vault, Application Insights) using Managed Identity or DefaultAzureCredential.
- Salesforce integration:
  - `src/salesforce_api.py` is an async client using OAuth + httpx and Pydantic models.
  - `src/salesforce_fastapi.py` exposes CRUD and query endpoints; it initializes a global client during FastAPI lifespan.

## Dev workflows (project-specific)
- Tests are pytest-based with fixtures in `src/conftest.py` and test modules under `src/test_*.py`.
- The canonical test+coverage run is in `run_tests.py` (writes HTML to `htmlcov/` and XML to `coverage.xml`).
- Pytest options and markers are configured in `pytest.ini` (e.g., strict markers, 10s timeout).

## Conventions & patterns
- API responses are consistently modeled with Pydantic models (see `Item`, `ItemResponse`, `HealthResponse` in `src/fast_api.py`).
- AWS Lambda handlers return API Gateway-compatible dictionaries via helpers like `create_response` or `APIGatewayResponse`.
- AWS events are normalized through `APIGatewayEvent` for REST vs HTTP API differences.
- Salesforce requests are async; prefer `SalesforceClient` methods and `get_salesforce_client()` rather than raw HTTP calls.
- Azure clients are created through helper functions that read environment variables (e.g., `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_COSMOS_ENDPOINT`).

## Integration points & external deps
- AWS: `boto3` (S3, Kinesis, Glue) and `mangum` for API Gateway → ASGI.
- Azure: `azure-identity`, `azure-storage-blob`, `azure-cosmos`, `azure-keyvault-secrets`, `azure-monitor-opentelemetry`.
- Salesforce: `httpx`, `python-dotenv`, optional `simple-salesforce` and `salesforce-bulk` in `src/requirements.txt`.

## Guidance for changes
- Keep FastAPI route signatures and response models aligned with existing tests in `src/test_fast_api.py`.
- If you add new Lambda handlers, follow the API Gateway response shape used in `src/lambda_api.py`.
- When extending AWS Gateway utilities, update corresponding tests in `src/test_aws_gateway_integration.py` and fixtures in `src/conftest.py`.
