# Terraform Deployment Guide - FastAPI to AWS Lambda

Complete guide to deploy your FastAPI application to AWS Lambda using Terraform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Deployment Steps](#deployment-steps)
5. [Verification](#verification)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Cleanup](#cleanup)

---

## Prerequisites

### Required Software

- **Terraform** (v1.0+) - [Install](https://www.terraform.io/downloads.html)
- **AWS CLI** (v2+) - [Install](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- **Python** (3.11+) - Already installed
- **Git** (optional but recommended)

### AWS Account

- AWS account with appropriate permissions
- AWS credentials configured locally

### Verify Installation

```powershell
# Check Terraform version
terraform version

# Check AWS CLI version
aws --version

# Verify AWS credentials
aws sts get-caller-identity
```

---

## Quick Start

### 1. Deploy with Default Settings (Dev Environment)

```powershell
# Navigate to terraform directory
cd terraform

# Initialize Terraform (required first time)
terraform init

# Review what will be created
terraform plan

# Deploy to AWS
terraform apply

# When prompted, type: yes
```

### 2. Get Your API Endpoint

```powershell
# Display outputs including API endpoint
terraform output

# Or get specific output
terraform output -json api_endpoint
```

### 3. Test Your Deployed API

```powershell
# Get the API endpoint from terraform output
$API_ENDPOINT = terraform output -raw api_endpoint

# Test health endpoint
curl "$API_ENDPOINT/api/health"

# Create an item
curl -X POST "$API_ENDPOINT/api/items/" `
  -H "Content-Type: application/json" `
  -d '{"name":"Test Item","description":"Test Description"}'

# Get an item
curl "$API_ENDPOINT/api/items/1"
```

---

## Configuration

### Environment Variables

The Terraform configuration uses `terraform.tfvars` file. Create or update it:

```bash
# Copy the example
cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# Edit with your values
code terraform/terraform.tfvars
```

### terraform.tfvars Example

```hcl
# AWS Configuration
aws_region  = "us-east-1"
environment = "dev"
project_name = "python-api"

# Lambda Configuration
function_name      = "python-api-lambda"
lambda_runtime     = "python3.11"
lambda_memory      = 512
lambda_timeout      = 30

# API Gateway Configuration
api_stage_name = "dev"

# Logging
log_retention_days = 7
log_level         = "INFO"

# Environment Variables (for Salesforce if needed)
environment_variables = {
  SALESFORCE_INSTANCE_URL  = ""
  SALESFORCE_CLIENT_ID     = ""
  SALESFORCE_CLIENT_SECRET = ""
  SALESFORCE_USERNAME      = ""
  SALESFORCE_PASSWORD      = ""
}

# CloudWatch Alarms
error_threshold    = 5
duration_threshold = 25000

# CORS
cors_allow_origins = ["*"]

# Tags
tags = {
  Owner       = "Your Name"
  CostCenter  = "Engineering"
  Application = "python-api"
}
```

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | us-east-1 | AWS region for deployment |
| `environment` | dev | Environment name (dev, staging, prod) |
| `lambda_memory` | 512 | Lambda memory in MB (128-10240) |
| `lambda_timeout` | 30 | Lambda timeout in seconds |
| `log_retention_days` | 7 | CloudWatch log retention |
| `error_threshold` | 5 | CloudWatch alarm error threshold |

---

## Deployment Steps

### Step 1: Prepare Your Code

```powershell
# Ensure you're in the workspace root
cd "c:\Users\desha\Python Projects\python-test-env"

# Verify tests pass
.\.venv\Scripts\python.exe -m pytest tests/ -v

# Build requirements are included in src/requirements.txt
# Terraform will package everything automatically
```

### Step 2: Initialize Terraform

```powershell
cd terraform

# This downloads the AWS provider and sets up backend
terraform init

# Output should show:
# - Initializing the backend...
# - Downloading plugin for provider registry.terraform.io/hashicorp/aws
# - Terraform has been successfully initialized!
```

### Step 3: Create Terraform Variables File

```powershell
# If not already created
Copy-Item terraform.tfvars.example terraform.tfvars

# Edit the file with your settings
code terraform.tfvars
```

### Step 4: Plan the Deployment

```powershell
# Review what Terraform will create
terraform plan -out=tfplan

# Review the output carefully:
# - Resources to be created (+)
# - Resources to be modified (~)
# - Resources to be destroyed (-)
```

### Step 5: Apply the Terraform Configuration

```powershell
# Deploy to AWS (this takes 2-5 minutes)
terraform apply tfplan

# Or without saving plan file:
terraform apply

# When prompted, type: yes
```

### Step 6: Save Outputs

```powershell
# Export outputs to file
terraform output > deployment_output.txt

# Or save as JSON
terraform output -json > deployment_output.json

# Display key outputs
terraform output
```

---

## Verification

### Verify Lambda Function Created

```powershell
# List Lambda functions
aws lambda list-functions --region us-east-1

# Get specific function info
aws lambda get-function --function-name python-api-lambda --region us-east-1
```

### Verify API Gateway Created

```powershell
# List APIs
aws apigatewayv2 get-apis --region us-east-1

# Get specific API details
$API_ID = (terraform output -raw api_id)
aws apigatewayv2 get-api --api-id $API_ID --region us-east-1
```

### Test API Endpoints

```powershell
# Get API endpoint
$API_ENDPOINT = (terraform output -raw api_endpoint)

# 1. Test welcome endpoint
Write-Host "Testing GET /"
curl "$API_ENDPOINT/"

# 2. Test health check
Write-Host "`nTesting GET /api/health"
curl "$API_ENDPOINT/api/health"

# 3. Test create item
Write-Host "`nTesting POST /api/items/"
curl -X POST "$API_ENDPOINT/api/items/" `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Test Item",
    "description": "Testing Terraform deployment",
    "status": "created"
  }'

# 4. Test get item
Write-Host "`nTesting GET /api/items/1"
curl "$API_ENDPOINT/api/items/1"

# 5. Test AWS info endpoint
Write-Host "`nTesting GET /api/aws-info"
curl "$API_ENDPOINT/api/aws-info"
```

### Verify in AWS Console

1. **AWS Lambda Console**
   - Navigate to Lambda > Functions
   - Find function named `python-api-lambda`
   - View configuration and code

2. **API Gateway Console**
   - Navigate to API Gateway > APIs
   - Find API named `python-api-lambda-api`
   - View routes and integrations

3. **CloudWatch Console**
   - Navigate to CloudWatch > Log Groups
   - Find `/aws/lambda/python-api-lambda`
   - View recent logs

---

## Monitoring

### View CloudWatch Logs

```powershell
# Real-time logs
aws logs tail /aws/lambda/python-api-lambda --follow --region us-east-1

# Last 10 minutes
aws logs tail /aws/lambda/python-api-lambda --since 10m --region us-east-1

# View API Gateway logs
aws logs tail /aws/apigateway/python-api-lambda --region us-east-1
```

### CloudWatch Metrics

```powershell
# Get Lambda invocations
aws cloudwatch get-metric-statistics `
  --namespace AWS/Lambda `
  --metric-name Invocations `
  --dimensions Name=FunctionName,Value=python-api-lambda `
  --start-time $(Get-Date).AddHours(-1).ToUniversalTime().ToString('o') `
  --end-time (Get-Date).ToUniversalTime().ToString('o') `
  --period 300 `
  --statistics Sum `
  --region us-east-1

# Get Lambda errors
aws cloudwatch get-metric-statistics `
  --namespace AWS/Lambda `
  --metric-name Errors `
  --dimensions Name=FunctionName,Value=python-api-lambda `
  --start-time $(Get-Date).AddHours(-1).ToUniversalTime().ToString('o') `
  --end-time (Get-Date).ToUniversalTime().ToString('o') `
  --period 300 `
  --statistics Sum `
  --region us-east-1

# Get Lambda duration
aws cloudwatch get-metric-statistics `
  --namespace AWS/Lambda `
  --metric-name Duration `
  --dimensions Name=FunctionName,Value=python-api-lambda `
  --start-time $(Get-Date).AddHours(-1).ToUniversalTime().ToString('o') `
  --end-time (Get-Date).ToUniversalTime().ToString('o') `
  --period 300 `
  --statistics Average,Maximum `
  --region us-east-1
```

### View CloudWatch Alarms

```powershell
# List all alarms
terraform output lambda_errors_alarm_name
terraform output lambda_duration_alarm_name

# View alarm history
aws cloudwatch describe-alarm-history `
  --alarm-name python-api-lambda-errors `
  --region us-east-1

aws cloudwatch describe-alarm-history `
  --alarm-name python-api-lambda-high-duration `
  --region us-east-1
```

---

## Troubleshooting

### Issue: `terraform init` fails

**Problem**: "Failed to download plugin for provider registry.terraform.io/hashicorp/aws"

**Solution**:
```powershell
# Clear Terraform cache
Remove-Item -Recurse -Force .terraform

# Reinitialize
terraform init

# If still fails, check internet connection and firewall
```

### Issue: `terraform apply` fails with permission errors

**Problem**: "User: arn:aws:iam::... is not authorized to perform: lambda:CreateFunction"

**Solution**:
```powershell
# Verify AWS credentials
aws sts get-caller-identity

# Ensure your IAM user/role has permissions:
# - lambda:CreateFunction
# - lambda:DeleteFunction
# - apigatewayv2:CreateApi
# - iam:CreateRole
# - cloudwatch:CreateLogGroup
```

### Issue: Lambda function is not receiving requests

**Problem**: API returns 500 error or function doesn't execute

**Solution**:
```powershell
# Check API Gateway integration
aws apigatewayv2 get-integration `
  --api-id $(terraform output -raw api_id) `
  --integration-id $(aws apigatewayv2 get-integrations --api-id $(terraform output -raw api_id) --region us-east-1 --query 'Items[0].IntegrationId' --output text) `
  --region us-east-1

# Check Lambda logs
aws logs tail /aws/lambda/python-api-lambda --follow --region us-east-1

# Verify Lambda execution role
aws iam get-role --role-name python-api-lambda-role --region us-east-1
```

### Issue: Changes to code not reflecting

**Problem**: Deployed Lambda doesn't have latest code

**Solution**:
```powershell
# Rebuild and redeploy
terraform apply -replace="aws_lambda_function.salesforce_api"

# Or manual repackage
Remove-Item .lambda_build -Recurse -Force
terraform apply
```

### Issue: Dependencies not available in Lambda

**Problem**: Lambda fails with "ModuleNotFoundError"

**Solution**:
1. Ensure `requirements.txt` is in `src/` directory
2. All dependencies listed in `src/requirements.txt`
3. Redeploy:
```powershell
terraform apply -replace="aws_lambda_function.salesforce_api"
```

---

## Cleanup

### Destroy All AWS Resources

```powershell
cd terraform

# Preview what will be destroyed
terraform plan -destroy

# Destroy everything
terraform destroy

# When prompted, type: yes
```

### Partial Cleanup

```powershell
# Remove only Lambda function (keep API Gateway)
terraform destroy -target=aws_lambda_function.salesforce_api

# Remove only API Gateway (keep Lambda)
terraform destroy -target=aws_apigatewayv2_api.salesforce_api
```

### Clean Local Terraform State

```powershell
# Remove local state files
Remove-Item terraform.tfstate
Remove-Item terraform.tfstate.backup
Remove-Item -Recurse .terraform

# Start fresh
terraform init
```

---

## Advanced Configuration

### Use S3 Backend for State

For production, store Terraform state in S3:

```hcl
# In main.tf
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "python-api/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

Create S3 bucket first:
```powershell
aws s3api create-bucket --bucket your-terraform-state-bucket --region us-east-1
aws s3api put-bucket-versioning --bucket your-terraform-state-bucket --versioning-configuration Status=Enabled
```

### Production Deployment

Create `prod.tfvars`:

```hcl
aws_region         = "us-east-1"
environment        = "prod"
function_name      = "python-api-prod"
api_stage_name     = "prod"
lambda_memory      = 1024
lambda_timeout     = 60
log_retention_days = 30
error_threshold    = 3
duration_threshold = 20000

cors_allow_origins = [
  "https://yourdomain.com",
  "https://app.yourdomain.com"
]
```

Deploy with:
```powershell
terraform apply -var-file=prod.tfvars
```

### Multiple Environments

```powershell
# Dev environment
terraform workspace new dev
terraform apply -var-file=dev.tfvars

# Staging environment
terraform workspace new staging
terraform apply -var-file=staging.tfvars

# Prod environment
terraform workspace new prod
terraform apply -var-file=prod.tfvars

# List workspaces
terraform workspace list

# Switch workspaces
terraform workspace select dev
```

---

## Useful Commands Reference

```powershell
# Planning and Deployment
terraform init                          # Initialize Terraform
terraform plan                          # Show planned changes
terraform apply                         # Apply changes
terraform destroy                       # Delete all resources
terraform refresh                       # Update state from AWS

# State Management
terraform state list                    # List resources in state
terraform state show aws_lambda_function.salesforce_api
terraform state rm <resource>           # Remove from state
terraform import <resource> <aws-id>    # Import existing resource

# Inspection
terraform output                        # Display outputs
terraform output -json                  # Output as JSON
terraform show                          # Display current state
terraform console                       # Interactive console

# Validation
terraform validate                      # Check syntax
terraform fmt                           # Format HCL files
terraform fmt -recursive               # Format all HCL files

# Debugging
terraform plan -out=tfplan              # Save plan to file
terraform apply tfplan                  # Apply saved plan
TF_LOG=DEBUG terraform apply            # Enable debug logging
```

---

## Summary

Your FastAPI application is now deployed to AWS Lambda with:

✅ **Lambda Function** - Running Python 3.11 with your FastAPI code
✅ **API Gateway** - HTTP API with automatic integration
✅ **CloudWatch Logs** - Automatic logging of all requests and errors
✅ **CloudWatch Alarms** - Error and duration monitoring
✅ **CORS Enabled** - Cross-origin requests supported
✅ **Environment Variables** - Easily configure without code changes

Your API is accessible at the endpoint shown in `terraform output api_endpoint`.

For more information:
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
