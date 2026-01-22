# Terraform Module: AWS Salesforce Lambda API

Complete Terraform module to deploy the Salesforce API Lambda function and API Gateway on AWS.

## Overview

This Terraform module automates the deployment of:
- **AWS Lambda Function** - Salesforce API handler
- **API Gateway (HTTP API)** - RESTful API endpoints
- **IAM Roles & Policies** - Proper permissions
- **CloudWatch Logs** - Logging and monitoring
- **CloudWatch Alarms** - Error and performance monitoring

## Architecture

```
Internet
   ↓
API Gateway (HTTP API)
   ↓
Lambda Function
   ↓
Salesforce API
```

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.0
- AWS CLI configured with credentials
- Python source files (salesforce_api.py, aws_salesforce_lambda.py)
- Salesforce credentials (Instance URL, Client ID/Secret, Username, Password)

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Create Configuration

Copy and configure the variables:

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 3. Review Plan

```bash
terraform plan
```

### 4. Deploy

```bash
terraform apply
```

### 5. Get Outputs

```bash
terraform output
# or for specific output:
terraform output api_endpoint
```

## Configuration

### Basic Setup (terraform.tfvars)

```hcl
aws_region         = "us-east-1"
environment        = "dev"
function_name      = "salesforce-api"
lambda_memory      = 512
api_stage_name     = "dev"

environment_variables = {
  SALESFORCE_INSTANCE_URL  = "https://your-instance.salesforce.com"
  SALESFORCE_CLIENT_ID     = "your_client_id"
  SALESFORCE_CLIENT_SECRET = "your_client_secret"
  SALESFORCE_USERNAME      = "your_username@example.com"
  SALESFORCE_PASSWORD      = "your_password"
}
```

### Security Best Practices

**DO NOT** commit actual credentials to version control. Instead:

#### Option 1: AWS Secrets Manager

```hcl
# Store credentials in Secrets Manager
aws secretsmanager create-secret \
  --name salesforce/api-credentials \
  --secret-string '{
    "instance_url": "...",
    "client_id": "...",
    "client_secret": "...",
    "username": "...",
    "password": "..."
  }'
```

Then update the Lambda to retrieve from Secrets Manager:

```hcl
environment_variables = {
  SALESFORCE_CREDENTIALS_SECRET = "salesforce/api-credentials"
}
```

#### Option 2: Environment Variables

```bash
export TF_VAR_environment_variables='{"SALESFORCE_INSTANCE_URL":"...","SALESFORCE_CLIENT_ID":"...",...}'
```

#### Option 3: Encrypted .tfvars

```bash
# Use Terraform Cloud/Enterprise for encrypted variables
```

## Deployment

### Deploy to Development

```bash
terraform apply -var-file=dev.tfvars
```

### Deploy to Production

```bash
terraform apply -var-file=prod.tfvars
```

### Destroy Resources

```bash
terraform destroy
```

## Outputs

After deployment, important outputs are:

| Output | Description |
|--------|-------------|
| `api_endpoint` | API Gateway URL |
| `lambda_function_name` | Lambda function name |
| `health_check_url` | Health check endpoint |
| `lambda_logs_group_name` | CloudWatch logs group |

### Example Outputs

```
api_endpoint = "https://abc123.execute-api.us-east-1.amazonaws.com/dev"
health_check_url = "https://abc123.execute-api.us-east-1.amazonaws.com/dev/health"
lambda_function_name = "salesforce-api"
```

## API Endpoints

All endpoints are automatically created and available at the `api_endpoint`:

### Accounts
- `POST /accounts` - Create account
- `GET /accounts/{account_id}` - Get account
- `PATCH /accounts/{account_id}` - Update account
- `DELETE /accounts/{account_id}` - Delete account

### Contacts
- `POST /contacts` - Create contact
- `GET /contacts/{contact_id}` - Get contact
- `PATCH /contacts/{contact_id}` - Update contact
- `DELETE /contacts/{contact_id}` - Delete contact

### Opportunities
- `POST /opportunities` - Create opportunity
- `GET /opportunities/{opportunity_id}` - Get opportunity
- `PATCH /opportunities/{opportunity_id}` - Update opportunity
- `DELETE /opportunities/{opportunity_id}` - Delete opportunity

### Advanced
- `POST /query` - Execute SOQL query
- `POST /batch/accounts` - Batch create accounts
- `GET /health` - Health check

## Testing Deployment

### Health Check

```bash
curl https://YOUR_API_ENDPOINT/health
```

### Create Account

```bash
curl -X POST https://YOUR_API_ENDPOINT/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "Name": "Test Company",
    "Phone": "555-1234",
    "Industry": "Technology"
  }'
```

### Query Opportunities

```bash
curl -X POST https://YOUR_API_ENDPOINT/query \
  -H "Content-Type: application/json" \
  -d '{
    "soql": "SELECT Id, Name FROM Account LIMIT 5"
  }'
```

## Monitoring

### CloudWatch Logs

View Lambda logs:
```bash
aws logs tail /aws/lambda/salesforce-api --follow
```

View API Gateway logs:
```bash
aws logs tail /aws/apigateway/salesforce-api --follow
```

### CloudWatch Alarms

Alarms are automatically created for:
- Lambda errors (threshold: 5 errors in 5 minutes)
- Lambda duration (threshold: 25 seconds)

View alarms:
```bash
aws cloudwatch describe-alarms --alarm-names salesforce-api-errors
```

## Scaling

### Increase Memory/Timeout

```hcl
lambda_memory = 1024  # Up to 10240
lambda_timeout = 60   # Up to 900 seconds
```

### Enable Reserved Concurrency

Add to `main.tf`:
```hcl
resource "aws_lambda_reservation_concurrent_executions" "salesforce" {
  function_name             = aws_lambda_function.salesforce_api.function_name
  reserved_concurrent_executions = 100
}
```

## Troubleshooting

### Lambda Not Being Invoked

Check:
1. Lambda permissions: `aws lambda get-policy --function-name salesforce-api`
2. API Gateway integration: Check routes in AWS Console
3. CloudWatch logs: `aws logs tail /aws/lambda/salesforce-api`

### Salesforce Authentication Fails

Check:
1. Credentials in environment variables
2. Salesforce instance URL format
3. OAuth app configuration in Salesforce
4. Network connectivity from Lambda

### High Lambda Duration

Check:
1. Salesforce API response times
2. Network latency
3. Lambda memory (increase for more CPU)
4. Salesforce query complexity

### CORS Issues

Adjust in `variables.tf`:
```hcl
cors_allow_origins = ["https://your-domain.com"]
```

## Advanced Configuration

### S3 Backend for State

Uncomment in `main.tf`:
```hcl
backend "s3" {
  bucket         = "your-terraform-state-bucket"
  key            = "salesforce-lambda/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-locks"
}
```

### Custom Domain

```hcl
# Add to main.tf
resource "aws_apigatewayv2_domain_name" "custom" {
  domain_name = "api.example.com"
  
  domain_name_configurations {
    certificate_arn = aws_acm_certificate.example.arn
    endpoint_type   = "REGIONAL"
  }
}
```

### Environment-Specific Deployment

Create separate tfvars files:
```
terraform.tfvars.dev
terraform.tfvars.staging
terraform.tfvars.prod
```

Deploy to specific environment:
```bash
terraform apply -var-file=terraform.tfvars.prod
```

## Cost Estimation

```bash
terraform plan -out=tfplan
# Estimate shown in plan output
```

Typical costs:
- **Lambda**: $0.20 per 1M requests + compute time
- **API Gateway**: $0.35 per 1M requests
- **CloudWatch Logs**: $0.50 per GB ingested
- **CloudWatch Alarms**: $0.10 per alarm

## Version Management

### Upgrade Terraform

```bash
terraform version
# Update to latest or specific version
```

### Update AWS Provider

```bash
terraform init -upgrade
```

## Cleanup

### Destroy All Resources

```bash
terraform destroy
```

### Destroy Specific Resource

```bash
terraform destroy -target=aws_lambda_function.salesforce_api
```

## Module Customization

### Add Lambda Layer

```hcl
lambda_layers = [
  "arn:aws:lambda:us-east-1:123456789012:layer:python-deps:1"
]
```

### Custom IAM Policies

Add to `main.tf`:
```hcl
resource "aws_iam_role_policy" "custom_policy" {
  name   = "custom-policy"
  role   = aws_iam_role.lambda_role.id
  policy = jsonencode({...})
}
```

### Enable VPC

Add to `main.tf` for Lambda:
```hcl
vpc_config {
  subnet_ids         = var.subnet_ids
  security_group_ids = var.security_group_ids
}
```

## Support & Documentation

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Salesforce REST API](https://developer.salesforce.com/docs/api/rest/)

## License

This Terraform module is provided as-is for use with AWS and Salesforce.
