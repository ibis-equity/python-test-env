# AWS API Gateway Integration Guide

This guide explains how to integrate FastAPI with AWS API Gateway and Lambda.

## Overview

The FastAPI application can run in two modes:
1. **Local Development**: Standard Uvicorn server on port 8000
2. **AWS Lambda**: Using Mangum ASGI adapter with API Gateway

## Files

- **src/fast_api.py** - FastAPI application with Lambda handler
- **src/aws_gateway_integration.py** - AWS API Gateway utilities
- **terraform/lambda_deployment.tf** - Infrastructure as Code for Lambda deployment
- **sam_template.yaml** - SAM template for deployment

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- Python 3.13+
- Docker (for building Lambda deployment package)

## Installed Packages

```
mangum==0.17.0        # ASGI to Lambda proxy integration adapter
fastapi==0.128.0      # Web framework
pydantic==2.12.5      # Data validation
boto3==1.33.0         # AWS SDK
```

## Local Development

Run the FastAPI application locally:

```bash
cd src
python -m uvicorn fast_api:app --reload --host 0.0.0.0 --port 8000
```

Visit: `http://localhost:8000/docs`

## AWS Lambda Handler

### Handler Configuration

The Lambda handler is defined in `fast_api.py`:

```python
from mangum import Mangum

lambda_handler = Mangum(app, lifespan="off")
```

### Key Components

1. **Mangum Adapter**: Converts API Gateway events to ASGI format
   - Handles REST API format
   - Handles HTTP API format
   - Manages request/response translation

2. **Logging**: Configured for CloudWatch
   ```python
   logger = logging.getLogger()
   logger.setLevel(logging.INFO)
   ```

3. **AWS Environment Detection**: 
   - `/api/aws-info` endpoint returns environment details
   - Detects when running in Lambda vs local

## Deployment Options

### Option 1: Using AWS SAM (Serverless Application Model)

Create `sam_template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2.0
Description: FastAPI Lambda Application

Globals:
  Function:
    Timeout: 30
    MemorySize: 256
    Runtime: python3.11
    Environment:
      Variables:
        PYTHONPATH: /var/task
        AWS_REGION: !Ref AWS::Region

Resources:
  FastAPIFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: fastapi-app
      CodeUri: .
      Handler: src.fast_api.lambda_handler
      Runtime: python3.11
      MemorySize: 512
      Timeout: 60
      Events:
        ApiEvent:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Method: ANY
            Path: /{proxy+}
        RootEvent:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Method: ANY
            Path: /
      Layers:
        - !Ref DependenciesLayer
  
  DependenciesLayer:
    Type: AWS::Serverless::LayerVersion
    Properties:
      LayerName: fastapi-dependencies
      ContentUri: layer/
      CompatibleRuntimes:
        - python3.11
  
  ApiGateway:
    Type: AWS::ApiGateway::RestApi
    Properties:
      Name: fastapi-api
      Description: FastAPI REST API
      EndpointConfiguration:
        Types:
          - REGIONAL

Outputs:
  FunctionArn:
    Description: FastAPI Lambda Function ARN
    Value: !GetAtt FastAPIFunction.Arn
  
  ApiEndpoint:
    Description: API Gateway endpoint URL
    Value: !Sub 'https://${ApiGateway}.execute-api.${AWS::Region}.amazonaws.com/Prod'
```

Deploy with SAM:

```bash
sam build
sam deploy --guided
```

### Option 2: Using AWS CLI

1. **Create deployment package**:

```bash
mkdir lambda_package
cd lambda_package
pip install -r ../requirements.txt -t .
cp -r ../src .
zip -r ../function.zip .
cd ..
```

2. **Create Lambda function**:

```bash
aws lambda create-function \
  --function-name fastapi-app \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-role \
  --handler src.fast_api.lambda_handler \
  --zip-file fileb://function.zip \
  --timeout 60 \
  --memory-size 512
```

3. **Create API Gateway**:

```bash
aws apigateway create-rest-api \
  --name fastapi-api \
  --description "FastAPI REST API"
```

4. **Connect Lambda to API Gateway** (full setup required)

### Option 3: Using Terraform

Create `terraform/lambda_deployment.tf`:

```hcl
# Lambda function
resource "aws_lambda_function" "fastapi" {
  filename      = data.archive_file.function_zip.output_path
  function_name = "fastapi-app"
  role          = aws_iam_role.lambda_role.arn
  handler       = "src.fast_api.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 512

  environment {
    variables = {
      PYTHONPATH = "/var/task"
    }
  }

  source_code_hash = data.archive_file.function_zip.output_base64sha256

  layers = [aws_lambda_layer_version.dependencies.arn]
}

# API Gateway
resource "aws_apigateway_rest_api" "fastapi" {
  name        = "fastapi-api"
  description = "FastAPI REST API"
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# ... additional resources
```

Deploy with Terraform:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Endpoints

### Local (Uvicorn)
- `http://localhost:8000`
- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)

### AWS Lambda/API Gateway
- `https://{API_ID}.execute-api.{REGION}.amazonaws.com/prod`
- `https://{API_ID}.execute-api.{REGION}.amazonaws.com/prod/docs`
- `https://{API_ID}.execute-api.{REGION}.amazonaws.com/prod/redoc`

## API Gateway Integration Utilities

### APIGatewayEvent

Parse and validate API Gateway events:

```python
from aws_gateway_integration import APIGatewayEvent

event = APIGatewayEvent(api_gateway_event)
print(event.method)        # GET
print(event.path)          # /api/items/1
print(event.headers)       # Request headers
print(event.query_params)  # Query parameters
print(event.source_ip)     # Client IP
```

### APIGatewayResponse

Format responses for API Gateway:

```python
from aws_gateway_integration import APIGatewayResponse

# Success response
response = APIGatewayResponse.success(
    status_code=200,
    body={"result": "success"}
)

# Error response
error_response = APIGatewayResponse.error(
    status_code=404,
    message="Not found",
    error_code="ITEM_NOT_FOUND"
)
```

### CORS Helper

Configure CORS for API Gateway:

```python
from aws_gateway_integration import CORSHelper

headers = CORSHelper.get_cors_headers(
    allow_origins=["https://example.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"]
)
```

### Authentication Helper

Handle authentication:

```python
from aws_gateway_integration import AuthenticationHelper

token = AuthenticationHelper.get_authorization_token(headers)
if AuthenticationHelper.is_authorized(headers, expected_token):
    # Process request
    pass
```

## Environment Variables

When running in Lambda, set these environment variables:

```bash
AWS_REGION=us-east-1
AWS_LAMBDA_FUNCTION_NAME=fastapi-app
PYTHONPATH=/var/task
```

Detect environment in code:

```python
import os

def is_lambda():
    return bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

def is_local():
    return not is_lambda()
```

## CloudWatch Logs

View Lambda logs:

```bash
aws logs tail /aws/lambda/fastapi-app --follow
```

## Testing Locally with AWS Lambda Events

Use AWS SAM to test locally:

```bash
sam local start-api
```

Test with curl:

```bash
curl http://localhost:3000/
curl http://localhost:3000/docs
curl http://localhost:3000/api/health
```

## Performance Optimization

### Lambda Configuration

- **Memory**: 512 MB (sufficient for FastAPI)
- **Timeout**: 60 seconds
- **Ephemeral Storage**: 512 MB (default)

### Cold Start Optimization

1. **Use Lambda Layers** for dependencies:
   ```bash
   mkdir -p layer/python/lib/python3.11/site-packages
   pip install -r requirements.txt -t layer/python/lib/python3.11/site-packages/
   ```

2. **Minimize package size**:
   - Use only required dependencies
   - Exclude test files and documentation
   - Consider using Lambda container images for large packages

3. **Configure provisioned concurrency** for predictable traffic

### Cost Optimization

- Start with lower memory (256-512 MB)
- Use API Gateway caching
- Enable CloudWatch Logs retention policies
- Use Reserved Concurrency for predictable workloads

## Troubleshooting

### Issue: Module Not Found

**Solution**: Ensure Python path is correct:
```python
import sys
sys.path.insert(0, '/var/task')
```

### Issue: Timeout

**Solution**: Increase Lambda timeout:
```bash
aws lambda update-function-configuration \
  --function-name fastapi-app \
  --timeout 120
```

### Issue: Memory Issues

**Solution**: Increase Lambda memory:
```bash
aws lambda update-function-configuration \
  --function-name fastapi-app \
  --memory-size 1024
```

### Issue: CORS Errors

**Solution**: Configure API Gateway CORS:
```bash
aws apigateway put-integration-response \
  --rest-api-id {API_ID} \
  --resource-id {RESOURCE_ID} \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters '{"method.response.header.Access-Control-Allow-Headers":"'"'"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"'"'"}'
```

## Next Steps

1. Deploy to AWS using your preferred method
2. Configure custom domain (optional)
3. Set up API Gateway stages (dev, staging, prod)
4. Enable CloudWatch alarms
5. Implement request validation
6. Add authentication/authorization
7. Set up CI/CD pipeline

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Mangum Documentation](https://mangum.io/)
- [AWS Lambda Python Runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [API Gateway Integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-integration.html)
- [AWS SAM](https://aws.amazon.com/serverless/sam/)
