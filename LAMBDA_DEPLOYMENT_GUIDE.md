# Lambda Deployment Guide

Complete guide for deploying FastAPI to AWS Lambda with API Gateway integration.

## Quick Start

### 1. Prerequisites

```bash
# Install AWS CLI
aws --version  # Must be v2+

# Configure AWS credentials
aws configure

# Install SAM CLI
sam --version  # Or follow: https://aws.amazon.com/serverless/sam/
```

### 2. Build Lambda Package

#### Method A: Using SAM (Recommended)

```bash
# Build the application
sam build

# Deploy guided (first time)
sam deploy --guided

# Subsequent deployments
sam deploy
```

#### Method B: Manual Packaging

```bash
# Create package directory
mkdir -p lambda_package/python

# Install dependencies
pip install -r requirements.txt -t lambda_package/python/

# Copy source code
cp -r src lambda_package/

# Create ZIP
cd lambda_package
zip -r ../lambda_function.zip .
cd ..
```

#### Method C: Using Docker (for consistency)

```dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt -t "${LAMBDA_TASK_ROOT}"

# Copy app
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Set handler
CMD ["src.fast_api.lambda_handler"]
```

Build and push:

```bash
docker build -t fastapi-lambda:latest .
docker tag fastapi-lambda:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/fastapi-lambda:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/fastapi-lambda:latest
```

### 3. Deploy Using SAM

#### First Time Deployment

```bash
# Build
sam build

# Deploy with guided setup
sam deploy --guided

# Follow prompts:
# - Stack Name: fastapi-stack
# - Region: us-east-1
# - StageName: prod
# - Confirm changes before deploy: Y
# - Allow SAM CLI to create IAM roles: Y
```

#### Subsequent Deployments

```bash
sam build
sam deploy
```

#### View Deployment Progress

```bash
# Check CloudFormation events
aws cloudformation describe-stack-events \
  --stack-name fastapi-stack \
  --query 'StackEvents[*].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
  --output table
```

### 4. Deploy Using AWS CLI

```bash
# Create IAM role
aws iam create-role \
  --role-name lambda-fastapi-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policy
aws iam attach-role-policy \
  --role-name lambda-fastapi-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create function
aws lambda create-function \
  --function-name fastapi-app \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-fastapi-role \
  --handler src.fast_api.lambda_handler \
  --zip-file fileb://lambda_function.zip \
  --timeout 60 \
  --memory-size 512 \
  --layers arn:aws:lambda:REGION:ACCOUNT_ID:layer:fastapi-dependencies-layer:1

# Update function (after changes)
aws lambda update-function-code \
  --function-name fastapi-app \
  --zip-file fileb://lambda_function.zip

# Publish version
aws lambda publish-version \
  --function-name fastapi-app \
  --description "Production version"
```

### 5. Create API Gateway Integration

#### Using SAM (Automatic in sam_template.yaml)

The template automatically creates:
- REST API
- Integration with Lambda
- Proxy resource for all paths
- Deployment to production stage

#### Using AWS CLI (Manual)

```bash
# Create REST API
API_ID=$(aws apigateway create-rest-api \
  --name fastapi-api \
  --description "FastAPI REST API" \
  --query 'id' --output text)

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' --output text)

# Create proxy resource
RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part '{proxy+}' \
  --query 'id' --output text)

# Create method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method ANY \
  --authorization-type NONE

# Create Lambda integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method ANY \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:fastapi-app/invocations

# Grant API Gateway permission to call Lambda
aws lambda add-permission \
  --function-name fastapi-app \
  --statement-id apigateway-access \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:YOUR_ACCOUNT_ID:$API_ID/*"

# Deploy API
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod
```

### 6. Test Deployment

#### Using AWS CLI

```bash
# Get endpoint
ENDPOINT=$(aws cloudformation describe-stacks \
  --stack-name fastapi-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' \
  --output text)

# Test root endpoint
curl $ENDPOINT/

# Test health check
curl $ENDPOINT/api/health

# Test items endpoint
curl $ENDPOINT/api/items/1?q=test

# Create item
curl -X POST $ENDPOINT/api/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "A test item"}'

# View API docs
echo "$ENDPOINT/docs"  # Open in browser
```

#### Using Postman

Import the API endpoint into Postman:

```
POST {{endpoint}}/api/items/
GET {{endpoint}}/api/items/{item_id}
GET {{endpoint}}/api/health
GET {{endpoint}}/api/aws-info
```

### 7. View Logs

#### CloudWatch Logs (via AWS CLI)

```bash
# View recent logs
aws logs tail /aws/lambda/fastapi-app --follow

# View specific time range
aws logs filter-log-events \
  --log-group-name /aws/lambda/fastapi-app \
  --start-time $(date -d '1 hour ago' +%s)000

# View error logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/fastapi-app \
  --filter-pattern "ERROR"
```

#### CloudWatch Logs (via AWS Console)

1. Go to CloudWatch → Logs
2. Select `/aws/lambda/fastapi-app`
3. View log streams

### 8. Monitor Performance

#### CloudWatch Metrics

```bash
# Get invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=fastapi-app \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-01T01:00:00Z \
  --period 300 \
  --statistics Sum,Average
```

#### View Dashboard

```bash
# CloudWatch dashboard created by SAM
# Check AWS console: CloudWatch → Dashboards → fastapi-monitoring
```

### 9. Update Function Code

#### Using SAM

```bash
# Make code changes
vim src/fast_api.py

# Build
sam build

# Deploy
sam deploy

# No changes to infrastructure, just code update
```

#### Using AWS CLI

```bash
# Create new package
zip -r lambda_function.zip .

# Update function
aws lambda update-function-code \
  --function-name fastapi-app \
  --zip-file fileb://lambda_function.zip

# Update configuration
aws lambda update-function-configuration \
  --function-name fastapi-app \
  --timeout 120 \
  --memory-size 1024
```

### 10. Troubleshooting

#### Issue: "Module not found" error

**Solution**: Ensure layers are configured or dependencies are in ZIP:

```bash
# Recreate layer
mkdir -p layer/python/lib/python3.11/site-packages
pip install -r requirements.txt -t layer/python/lib/python3.11/site-packages/

# Create layer ZIP
cd layer && zip -r ../layer.zip . && cd ..

# Upload to AWS
aws lambda publish-layer-version \
  --layer-name fastapi-dependencies \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```

#### Issue: Timeout errors

**Solution**: Increase timeout:

```bash
aws lambda update-function-configuration \
  --function-name fastapi-app \
  --timeout 120
```

#### Issue: Out of memory

**Solution**: Increase memory:

```bash
aws lambda update-function-configuration \
  --function-name fastapi-app \
  --memory-size 1024
```

#### Issue: CORS errors

**Solution**: API Gateway CORS needs to be enabled:

```bash
# In SAM template, add MethodResponses and IntegrationResponses
# Or enable CORS in AWS Console:
# API Gateway → Resource → Enable CORS
```

#### Issue: Cold start times

**Solution**: 

1. Use Lambda Layers to reduce package size
2. Enable Provisioned Concurrency:

```bash
aws lambda put-provisioned-concurrency-config \
  --function-name fastapi-app \
  --provisioned-concurrent-executions 5 \
  --qualifier LIVE
```

3. Use Lambda SnapStart (Java only, not applicable here)
4. Optimize imports in code

### 11. Cleanup

#### Delete Stack (via SAM/CloudFormation)

```bash
# Delete all resources
aws cloudformation delete-stack --stack-name fastapi-stack

# Wait for deletion
aws cloudformation wait stack-delete-complete --stack-name fastapi-stack
```

#### Delete Individual Resources

```bash
# Delete Lambda function
aws lambda delete-function --function-name fastapi-app

# Delete API Gateway
aws apigateway delete-rest-api --rest-api-id YOUR_API_ID

# Delete Lambda layer
aws lambda delete-layer-version \
  --layer-name fastapi-dependencies \
  --version-number 1

# Delete IAM role
aws iam delete-role --role-name lambda-fastapi-role

# Delete CloudWatch logs
aws logs delete-log-group --log-group-name /aws/lambda/fastapi-app
```

## Advanced Configurations

### Custom Domain

```bash
# Create certificate (if not exists)
aws acm request-certificate \
  --domain-name api.example.com \
  --validation-method DNS

# Wait for validation, then:
aws apigateway create-domain-name \
  --domain-name api.example.com \
  --certificate-arn arn:aws:acm:...

# Create base path mapping
aws apigateway create-base-path-mapping \
  --domain-name api.example.com \
  --rest-api-id YOUR_API_ID \
  --stage prod
```

### Authorization/Authentication

#### API Key

```yaml
# Add to sam_template.yaml
ApiKeyParam:
  Type: AWS::ApiGateway::ApiKey
  Properties:
    Enabled: true
    Name: fastapi-api-key

UsagePlan:
  Type: AWS::ApiGateway::UsagePlan
  Properties:
    UsagePlanName: fastapi-usage-plan
    ApiStages:
      - ApiId: !Ref ApiGateway
        Stage: prod
    ApiKeyIds:
      - !Ref ApiKeyParam
    Quota:
      Limit: 10000
      Period: DAY
    Throttle:
      RateLimit: 100
      BurstLimit: 200
```

#### Lambda Authorizer

Create `src/authorizer.py`:

```python
def lambda_handler(event, context):
    token = event.get("authorizationToken", "")
    
    if token == "valid-token":
        return {
            "principalId": "user",
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": "Allow",
                        "Resource": event["methodArn"]
                    }
                ]
            }
        }
    else:
        raise Exception("Unauthorized")
```

## Cost Estimation

Typical monthly costs for FastAPI Lambda:

- **Lambda**: ~$0.20 (1M requests, 512 MB, 100ms avg)
- **API Gateway**: ~$3.50 (1M requests)
- **CloudWatch Logs**: ~$0.50 (small logs)
- **Data Transfer**: ~$0 (< 1 GB/month)

**Total**: ~$4-5/month for typical usage

## Monitoring Checklist

- [ ] CloudWatch alarms configured
- [ ] Log retention set to 7-30 days
- [ ] Lambda reserved concurrency configured
- [ ] API Gateway throttling limits set
- [ ] X-Ray tracing enabled
- [ ] API documentation accessible
- [ ] Health check endpoint monitored
- [ ] Error logs reviewed regularly
