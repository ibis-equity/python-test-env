# Azure Integration Guide

## Overview

This project is fully integrated with Azure services including:
- **Azure App Service** - Host the FastAPI application
- **Azure Blob Storage** - Store files and data
- **Azure Cosmos DB** - NoSQL database
- **Azure Key Vault** - Secrets management
- **Azure Application Insights** - Monitoring and logging
- **Azure DevOps** - CI/CD pipeline
- **Azure Managed Identity** - Secure authentication

## Prerequisites

1. **Azure Subscription**
   ```bash
   az account list
   az account set --subscription <subscription-id>
   ```

2. **Azure CLI** (installed and authenticated)
   ```bash
   az login
   ```

3. **Docker** (for container deployment)
   ```bash
   docker --version
   ```

## Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update `.env` with your Azure resource values:
   ```bash
   AZURE_SUBSCRIPTION_ID=your_subscription_id
   AZURE_STORAGE_ACCOUNT_NAME=your_storage_account
   AZURE_COSMOS_ENDPOINT=your_cosmos_endpoint
   AZURE_KEY_VAULT_URL=your_vault_url
   ```

## Deployment Methods

### Method 1: Azure DevOps Pipeline (Recommended)

1. **Set up Azure DevOps Project**
   ```bash
   az devops project create --name python-api
   ```

2. **Create Service Connection**
   ```bash
   az devops service-endpoint azurerm create \
     --name azure-connection \
     --azure-rm-service-principal-id <app-id> \
     --azure-rm-service-principal-key <password> \
     --azure-rm-tenant-id <tenant-id>
   ```

3. **Push Repository**
   ```bash
   git remote add azure <azure-devops-repo-url>
   git push azure main
   ```

4. **Pipeline automatically:**
   - Runs tests
   - Builds Docker image
   - Deploys to Azure App Service

### Method 2: Manual ARM Deployment

1. **Deploy Azure Resources**
   ```bash
   az deployment group create \
     --name python-api-deployment \
     --resource-group python-api-rg \
     --template-file azure-deploy.json \
     --parameters appName=python-api location=eastus
   ```

2. **Build and Push Docker Image**
   ```bash
   docker build -t python-api:latest .
   docker tag python-api:latest <registry>.azurecr.io/python-api:latest
   docker push <registry>.azurecr.io/python-api:latest
   ```

3. **Deploy App Service**
   ```bash
   az webapp deployment container config \
     --name python-api-app \
     --resource-group python-api-rg \
     --enable-cd true
   ```

### Method 3: Azure App Service Deploy (Easiest)

1. **Create Resource Group**
   ```bash
   az group create --name python-api-rg --location eastus
   ```

2. **Create App Service Plan**
   ```bash
   az appservice plan create \
     --name python-api-plan \
     --resource-group python-api-rg \
     --sku B1 \
     --is-linux
   ```

3. **Create Web App**
   ```bash
   az webapp create \
     --resource-group python-api-rg \
     --plan python-api-plan \
     --name python-api-app \
     --runtime "PYTHON:3.13" \
     --deployment-local-git
   ```

4. **Configure App Settings**
   ```bash
   az webapp config appsettings set \
     --resource-group python-api-rg \
     --name python-api-app \
     --settings \
       AZURE_STORAGE_ACCOUNT_NAME=your_storage \
       AZURE_COSMOS_ENDPOINT=your_endpoint \
       SECRET_KEY=your_secret_key
   ```

## Using Azure Services

### Azure Blob Storage

```python
from azure_integration import upload_blob, download_blob, list_blobs

# Upload file
with open("file.txt", "rb") as f:
    upload_blob("data", "uploads/file.txt", f)

# Download file
data = download_blob("data", "uploads/file.txt")

# List files
blobs = list_blobs("data", prefix="uploads/")
```

### Azure Cosmos DB

```python
from azure_integration import insert_cosmos_document, query_cosmos_documents

# Insert document
doc = {
    "id": "1",
    "name": "Item 1",
    "category": "products"
}
insert_cosmos_document("python-api", "items", doc)

# Query documents
results = query_cosmos_documents(
    "python-api",
    "items",
    "SELECT * FROM c WHERE c.category = @cat",
    [{"name": "@cat", "value": "products"}]
)
```

### Azure Key Vault

```python
from azure_integration import get_secret

# Get secret
api_key = get_secret("api-key")
db_password = get_secret("db-password")
```

### Application Insights

```python
from azure_integration import configure_app_insights
import logging

# Configure at startup
configure_app_insights()

# Use standard logging
logger = logging.getLogger(__name__)
logger.info("Application started")
```

## Managed Identity Setup

### Enable System-Assigned Managed Identity

```bash
az webapp identity assign \
  --resource-group python-api-rg \
  --name python-api-app
```

### Grant Permissions

**Azure Blob Storage:**
```bash
az role assignment create \
  --assignee <managed-identity-object-id> \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/<sub-id>/resourceGroups/python-api-rg/providers/Microsoft.Storage/storageAccounts/<storage-account>
```

**Azure Cosmos DB:**
```bash
az role assignment create \
  --assignee <managed-identity-object-id> \
  --role "Cosmos DB Account Reader" \
  --scope /subscriptions/<sub-id>/resourceGroups/python-api-rg/providers/Microsoft.DocumentDB/databaseAccounts/<cosmos-account>
```

**Azure Key Vault:**
```bash
az keyvault set-policy \
  --name python-api-vault \
  --object-id <managed-identity-object-id> \
  --secret-permissions get list
```

## Monitoring and Diagnostics

### Enable Application Insights

```bash
az webapp config set \
  --resource-group python-api-rg \
  --name python-api-app \
  --app-insights-key <instrumentation-key>
```

### View Logs

```bash
# Stream logs in real-time
az webapp log tail \
  --resource-group python-api-rg \
  --name python-api-app

# Download logs
az webapp log download \
  --resource-group python-api-rg \
  --name python-api-app \
  --log-file logs.zip
```

## CI/CD with Azure DevOps

### Pipeline Features

1. **Build Stage**
   - Install dependencies
   - Lint code (flake8)
   - Run tests (pytest)
   - Generate coverage reports

2. **Docker Build Stage**
   - Build Docker image
   - Tag with build ID
   - Push to Azure Container Registry

3. **Deploy Stage**
   - Deploy ARM template
   - Configure resources
   - Deploy to App Service

### Manual Pipeline Trigger

```bash
az pipelines run \
  --project python-api \
  --definition-name "Python API CI/CD"
```

## Cost Optimization

### Recommended Configuration

- **App Service**: B1 tier ($13/month)
- **Storage**: Standard LRS ($0.024/GB)
- **Cosmos DB**: Serverless (~$1/month for light usage)
- **Key Vault**: Standard ($0.60/month)
- **Application Insights**: Pay-as-you-go

### Cost Monitoring

```bash
az costmanagement query create \
  --timeframe MonthToDate \
  --type Usage \
  --dataset aggregation='{totalCost:sum}' \
  --filter "resourceGroup/values in ['python-api-rg']"
```

## Scaling

### Auto-Scale App Service

```bash
az monitor autoscale create \
  --resource-group python-api-rg \
  --resource-name python-api-app \
  --resource-type "Microsoft.Web/serverfarms" \
  --min-count 1 \
  --max-count 10 \
  --count 2
```

### Cosmos DB Scaling

```bash
az cosmosdb update \
  --resource-group python-api-rg \
  --name python-api-cosmos \
  --max-throughput 4000
```

## Troubleshooting

### Check Deployment Status

```bash
az deployment group list \
  --resource-group python-api-rg \
  --query "[].{name:name,state:properties.provisioningState}"
```

### Validate Template

```bash
az deployment group validate \
  --resource-group python-api-rg \
  --template-file azure-deploy.json \
  --parameters appName=python-api
```

### View Resource Errors

```bash
az group deployment operation list \
  --resource-group python-api-rg \
  --name python-api-deployment \
  --query "[?properties.provisioningState=='Failed']"
```

## Security Best Practices

1. **Never commit secrets**
   - Use `.env` (add to `.gitignore`)
   - Store secrets in Key Vault
   - Use Managed Identity for Azure services

2. **Enable HTTPS**
   ```bash
   az webapp config set \
     --resource-group python-api-rg \
     --name python-api-app \
     --https-only true
   ```

3. **Configure CORS**
   - Update FastAPI CORS middleware
   - Restrict to specific domains

4. **Network Security**
   - Use Virtual Networks
   - Configure firewall rules
   - Enable SSL/TLS

## Resources

- [Azure CLI Reference](https://docs.microsoft.com/cli/azure/)
- [Azure Python SDK](https://docs.microsoft.com/python/azure/)
- [FastAPI on Azure](https://learn.microsoft.com/azure/app-service/quickstart-python)
- [Azure DevOps Pipelines](https://docs.microsoft.com/azure/devops/pipelines/)

## Support

For issues:
1. Check Azure portal for resource status
2. Review application logs in Application Insights
3. Check Azure DevOps pipeline logs
4. Consult Azure documentation

---

*Last Updated: January 5, 2026*
