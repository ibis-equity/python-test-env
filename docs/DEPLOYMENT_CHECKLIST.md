# AWS Terraform Deployment Checklist

## Pre-Deployment

### Environment Setup
- [ ] **Terraform installed** (`terraform version`)
- [ ] **AWS CLI installed** (`aws --version`)
- [ ] **AWS credentials configured** (`aws sts get-caller-identity`)
- [ ] **Python 3.11+** available
- [ ] **Git** configured (optional)

### Code Verification
- [ ] **All tests passing** - `pytest src/test_*.py`
- [ ] **Code coverage adequate** - 85%+ coverage
- [ ] **requirements.txt updated** - All dependencies listed
- [ ] **Lambda handler correct** - `fast_api.lambda_handler`
- [ ] **No hardcoded credentials** in code
- [ ] **Environment variables configured** properly

### AWS Account Setup
- [ ] **IAM user/role has permissions**:
  - [ ] `lambda:*` (Lambda full access)
  - [ ] `apigatewayv2:*` (API Gateway v2 access)
  - [ ] `iam:CreateRole`, `iam:PutRolePolicy`
  - [ ] `cloudwatch:*` (CloudWatch access)
  - [ ] `logs:*` (CloudWatch Logs access)
- [ ] **AWS region selected** (default: us-east-1)
- [ ] **S3 bucket available** (for state, if using S3 backend)

### Configuration Files
- [ ] **terraform.tfvars created** from example
  ```powershell
  cp terraform.tfvars.example terraform.tfvars
  ```
- [ ] **terraform.tfvars reviewed** and customized:
  - [ ] `aws_region` correct
  - [ ] `function_name` appropriate
  - [ ] `lambda_memory` sufficient (512 MB recommended)
  - [ ] `api_stage_name` set
  - [ ] `environment_variables` configured if needed
  - [ ] `tags` updated with your info

### Pre-Flight Checks
- [ ] **Workspace clean** - No uncommitted changes
  ```powershell
  git status  # Should show nothing modified
  ```
- [ ] **Terraform workspace correct** - Not on production by accident
  ```powershell
  terraform workspace show
  ```
- [ ] **Backup of current state** (if redeploying)
  ```powershell
  Copy-Item terraform.tfstate terraform.tfstate.backup
  ```

---

## Deployment

### Initialize Terraform
```powershell
cd terraform
terraform init
```
- [ ] **Initialization successful** - Should show "Terraform has been successfully initialized"
- [ ] **.terraform directory created**
- [ ] **Backend configured** correctly

### Validate Configuration
```powershell
terraform validate
terraform fmt -recursive
```
- [ ] **Validation passes** - No errors reported
- [ ] **All files formatted** - HCL style consistent

### Plan Deployment
```powershell
terraform plan -out=tfplan
```
- [ ] **Plan generated** successfully
- [ ] **Review resources** being created:
  - [ ] 1x Lambda Function
  - [ ] 1x API Gateway HTTP API
  - [ ] 1x IAM Role
  - [ ] 1x IAM Policy (Secrets Manager)
  - [ ] 1x CloudWatch Log Group (Lambda)
  - [ ] 1x CloudWatch Log Group (API Gateway)
  - [ ] 1x Lambda Permission
  - [ ] 2x CloudWatch Alarms (Errors, Duration)
  - [ ] Multiple API Routes
- [ ] **No unexpected changes** - Review additions/modifications
- [ ] **Function name** matches expectations
- [ ] **API Gateway stage** correct

### Apply Configuration
```powershell
terraform apply tfplan
```
- [ ] **Apply completes** without errors
- [ ] **Progress shown** - Resources being created
- [ ] **No permission errors** - IAM role has sufficient access
- [ ] **Completion message** appears - "Apply complete! Resources: X added, 0 changed, 0 destroyed"

### Verify Outputs
```powershell
terraform output
```
- [ ] **lambda_function_name** displayed
- [ ] **api_endpoint** shows valid HTTPS URL
- [ ] **api_id** present
- [ ] **lambda_role_arn** shown
- [ ] **All outputs** look correct

---

## Post-Deployment Verification

### Verify AWS Resources Created

#### Lambda Function
```powershell
aws lambda list-functions --region us-east-1
aws lambda get-function --function-name python-api-lambda --region us-east-1
```
- [ ] **Function exists** in AWS console
- [ ] **Runtime** is `python3.11`
- [ ] **Handler** is `fast_api.lambda_handler`
- [ ] **Memory** is 512 MB
- [ ] **Timeout** is 30 seconds
- [ ] **Environment variables** set correctly
- [ ] **Code size** > 0

#### API Gateway
```powershell
aws apigatewayv2 get-apis --region us-east-1
aws apigatewayv2 get-routes --api-id <API_ID> --region us-east-1
```
- [ ] **API exists** with correct name
- [ ] **Protocol type** is HTTP
- [ ] **All routes created**:
  - [ ] GET /
  - [ ] GET /api/health
  - [ ] GET /api/items/{item_id}
  - [ ] POST /api/items/
  - [ ] GET /api/aws-info
  - [ ] $default (catch-all)
- [ ] **Stage created** with name "dev" (or your stage name)

#### CloudWatch
```powershell
aws logs describe-log-groups --region us-east-1 | grep python-api
```
- [ ] **Lambda log group** created (`/aws/lambda/python-api-lambda`)
- [ ] **API Gateway log group** created (`/aws/apigateway/python-api-lambda`)
- [ ] **Retention set** to 7 days (or configured value)

#### IAM
```powershell
aws iam get-role --role-name python-api-lambda-role
aws iam list-role-policies --role-name python-api-lambda-role
```
- [ ] **IAM role created** with correct name
- [ ] **Assume role policy** allows Lambda service
- [ ] **Policies attached**:
  - [ ] AWSLambdaBasicExecutionRole
  - [ ] Custom policy for Secrets Manager (if needed)

### API Testing

#### Get API Endpoint
```powershell
$API_ENDPOINT = (terraform output -raw api_endpoint)
Write-Host $API_ENDPOINT
```

#### Test Welcome Endpoint
```powershell
curl "$API_ENDPOINT/"
```
- [ ] **Response 200 OK**
- [ ] **JSON response** with message and endpoints
- [ ] **Example response:**
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

#### Test Health Check
```powershell
curl "$API_ENDPOINT/api/health"
```
- [ ] **Response 200 OK**
- [ ] **Status is "healthy"**
- [ ] **Version displayed**
- [ ] **Example response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

#### Test Create Item
```powershell
curl -X POST "$API_ENDPOINT/api/items/" `
  -H "Content-Type: application/json" `
  -d '{"name":"Test Item","description":"Testing Terraform deployment"}'
```
- [ ] **Response 201 Created**
- [ ] **Item data in response**
- [ ] **Status is "created"**

#### Test Get Item
```powershell
curl "$API_ENDPOINT/api/items/1"
```
- [ ] **Response 200 OK**
- [ ] **Item data returned**
- [ ] **Item ID matches request**

#### Test AWS Info
```powershell
curl "$API_ENDPOINT/api/aws-info"
```
- [ ] **Response 200 OK**
- [ ] **Lambda function name** displayed
- [ ] **AWS region** correct
- [ ] **Environment** shows as "aws"
- [ ] **Example response:**
```json
{
  "lambda_function_name": "python-api-lambda",
  "aws_region": "us-east-1",
  "environment": "aws",
  "lambda_version": "1"
}
```

### Check CloudWatch Logs
```powershell
aws logs tail /aws/lambda/python-api-lambda --region us-east-1
```
- [ ] **Logs appearing** for Lambda invocations
- [ ] **No errors** in logs
- [ ] **Timestamps** recent
- [ ] **Log entries** for each API call

### Verify CloudWatch Alarms
```powershell
aws cloudwatch describe-alarms --region us-east-1 | Select-String "python-api-lambda"
```
- [ ] **Error alarm created** (`python-api-lambda-errors`)
- [ ] **Duration alarm created** (`python-api-lambda-high-duration`)
- [ ] **Alarms in OK state** (not alarming)
- [ ] **Can be viewed** in AWS CloudWatch console

---

## Performance Verification

### Check Lambda Metrics
```powershell
aws cloudwatch get-metric-statistics `
  --namespace AWS/Lambda `
  --metric-name Invocations `
  --dimensions Name=FunctionName,Value=python-api-lambda `
  --start-time (Get-Date).AddHours(-1).ToUniversalTime().ToString('o') `
  --end-time (Get-Date).ToUniversalTime().ToString('o') `
  --period 300 `
  --statistics Sum `
  --region us-east-1
```
- [ ] **Invocation count** > 0
- [ ] **No errors** in metrics
- [ ] **Duration** reasonable (typically < 1000ms)

### Check API Gateway Metrics
```powershell
aws cloudwatch get-metric-statistics `
  --namespace AWS/ApiGateway `
  --metric-name Count `
  --dimensions Name=ApiId,Value=<API_ID> `
  --start-time (Get-Date).AddHours(-1).ToUniversalTime().ToString('o') `
  --end-time (Get-Date).ToUniversalTime().ToString('o') `
  --period 300 `
  --statistics Sum `
  --region us-east-1
```
- [ ] **Request count** > 0
- [ ] **4XX errors** minimal
- [ ] **5XX errors** zero

---

## Documentation & Handoff

### Documentation Complete
- [ ] **Deployment Guide** - TERRAFORM_DEPLOYMENT_GUIDE.md
- [ ] **API Documentation** - SWAGGER_OPENAPI.md
- [ ] **Access Guide** - SWAGGER_ACCESS_GUIDE.md
- [ ] **Function Reference** - COMPLETE_FUNCTION_REFERENCE.md
- [ ] **Terraform Output** saved
  ```powershell
  terraform output > deployment_output.txt
  terraform output -json > deployment_output.json
  ```

### Deployment Info Recorded
- [ ] **API Endpoint URL** - Noted and shared
- [ ] **Function Name** - Recorded
- [ ] **Log Group Names** - Documented
- [ ] **Alarm Names** - Listed
- [ ] **Deployment Date/Time** - Recorded

### Team Communication
- [ ] **Team notified** of deployment
- [ ] **API endpoint shared** with stakeholders
- [ ] **Documentation links** provided
- [ ] **Support contact** identified
- [ ] **Runbook created** for operations

---

## Post-Deployment Tasks

### First 24 Hours
- [ ] **Monitor logs** for errors
- [ ] **Check CloudWatch dashboards**
- [ ] **Verify performance** metrics
- [ ] **Test all endpoints** periodically

### First Week
- [ ] **Setup monitoring dashboard** (optional)
- [ ] **Configure additional alarms** if needed
- [ ] **Load test** (if applicable)
- [ ] **Document any issues** found
- [ ] **Optimize Lambda settings** based on performance

### Ongoing
- [ ] **Weekly log review**
- [ ] **Monthly cost analysis**
- [ ] **Update dependencies** regularly
- [ ] **Security patches** applied
- [ ] **Backup strategy** in place

---

## Troubleshooting

### Deployment Fails
1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify IAM permissions
3. Check terraform.tfvars settings
4. Review Terraform error messages
5. Check AWS CloudTrail for detailed errors

### API Returns 502 Bad Gateway
1. Check Lambda logs: `aws logs tail /aws/lambda/python-api-lambda --follow`
2. Verify Lambda handler name in terraform.tfvars
3. Check if requirements.txt is complete
4. Redeploy Lambda: `terraform apply -replace="aws_lambda_function.salesforce_api"`

### Can't Access API Endpoint
1. Verify API Gateway stage is deployed
2. Check API route configuration
3. Verify API Gateway Integration is pointing to correct Lambda
4. Check Lambda permission for API Gateway

### CloudWatch Alarms Triggering
1. Review Lambda logs for errors
2. Check error rate in CloudWatch metrics
3. Consider increasing Lambda memory or timeout
4. Review code for performance issues

---

## Rollback Procedure

### If Deployment Needs to be Rolled Back

```powershell
cd terraform

# Option 1: Destroy everything
terraform destroy

# Option 2: Restore from state backup
Copy-Item terraform.tfstate.backup terraform.tfstate
terraform apply

# Option 3: Revert code and redeploy
git revert <commit_hash>
terraform apply
```

- [ ] **Rollback completed** successfully
- [ ] **Previous state** restored
- [ ] **APIs responding** normally
- [ ] **Logs reviewed** for rollback impact
- [ ] **Team notified** of rollback

---

## Sign-Off

**Deployment Date:** _______________

**Deployed By:** _______________

**Reviewed By:** _______________

**API Endpoint:** _______________

**Notes:**
```
[Add any deployment notes or issues here]
```

---

**Checklist Complete!** ✅

Your FastAPI application is now deployed to AWS Lambda with Terraform. All endpoints are live and monitored.
