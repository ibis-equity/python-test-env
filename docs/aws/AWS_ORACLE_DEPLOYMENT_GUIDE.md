# AWS + Oracle + Python: Senior-Level Implementation Guide

## Quick Start

### Local Development (5 minutes)

```powershell
# 1. Activate virtual environment
cd c:\Users\desha\Python Projects\python-test-env
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r src/requirements.txt
pip install oracledb structlog mangum

# 3. Set environment variables
$env:ORACLE_HOST = "localhost"
$env:ORACLE_PORT = "1521"
$env:ORACLE_SERVICE_NAME = "XE"
$env:ORACLE_USER = "app_user"
$env:ORACLE_PASSWORD = "password"

# 4. Run locally
uvicorn src.oracle_fastapi:app --reload --port 8000

# 5. Test API
curl http://localhost:8000/api/accounts
curl http://localhost:8000/docs  # Interactive documentation
```

### AWS Deployment (30 minutes)

```bash
# 1. Create RDS Oracle instance
aws rds create-db-instance \
  --db-instance-identifier oracle-prod \
  --db-instance-class db.t3.medium \
  --engine oracle-se2 \
  --master-username admin \
  --allocated-storage 20

# 2. Create IAM secret
aws secretsmanager create-secret \
  --name oracle/prod/credentials \
  --secret-string '{"host":"...", "user":"app_user", "password":"..."}'

# 3. Deploy Terraform
cd terraform
terraform init
terraform apply -auto-approve

# 4. Get API endpoint
terraform output api_endpoint
```

---

## Architecture Decision Records (ADRs)

### ADR 1: Connection Pool Pattern

**Decision**: Use thread-safe connection pooling with health checks

**Rationale**:
- Oracle connections are expensive to create (~500ms each)
- Connection pooling reuses established connections
- Health checks detect stale connections automatically
- Thread-safe for Lambda concurrent invocations

**Implementation**:
```python
# Singleton pattern ensures one pool per Lambda container
pool = get_pool()  # First call initializes
pool = get_pool()  # Subsequent calls reuse same pool

# Health checks verify connection validity
health = pool.health_check()
if health['status'] != 'healthy':
    # Recover or alert
    pass
```

**Trade-offs**:
- ✅ Performance (connection reuse)
- ✅ Resource efficiency (bounded connections)
- ❌ Slightly higher memory usage
- ❌ Requires timeout management

---

### ADR 2: Query Builder for SQL Injection Prevention

**Decision**: Use parameterized query builder instead of string concatenation

**Rationale**:
- SQL injection is preventable through parameterization
- Query builder provides fluent, readable API
- Parameters automatically escaped by Oracle driver
- Type-safe parameter passing

**Implementation**:
```python
# Safe: Parameters in dict, not SQL string
query = (OracleQueryBuilder()
         .select('ID', 'NAME')
         .from_table('ACCOUNTS')
         .where('INDUSTRY', '=', user_input))

sql, params = query.build()
# sql: "SELECT ID, NAME FROM ACCOUNTS WHERE INDUSTRY = :0"
# params: {'0': user_input}

# Oracle JDBC driver handles escaping
```

**Trade-offs**:
- ✅ Security (prevents injection)
- ✅ Readability (fluent API)
- ✅ Performance (native parameterization)
- ❌ Can't use dynamic column names (rare need)

---

### ADR 3: Repository Pattern for Data Abstraction

**Decision**: Use repository pattern instead of exposing raw SQL queries

**Rationale**:
- Separates business logic from data access
- Enables testing with mock repositories
- Allows future storage backend swaps
- Provides consistent CRUD interface

**Implementation**:
```python
class BaseRepository(ABC):
    """Abstract interface all repositories implement"""
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Model]: pass
    @abstractmethod
    def create(self, obj: CreateModel) -> Model: pass

class AccountRepository(BaseRepository):
    """Concrete Account implementation"""
    def get_by_id(self, id: int) -> Optional[Account]:
        query = OracleQueryBuilder()...
        return Account(**result)
```

**Trade-offs**:
- ✅ Testability (mock repositories)
- ✅ Flexibility (swap backends)
- ✅ Maintainability (consistent interface)
- ❌ Extra abstraction layer (minor performance cost)

---

### ADR 4: Dependency Injection with FastAPI

**Decision**: Use FastAPI's Depends for dependency injection

**Rationale**:
- Built-in to FastAPI (no extra libraries)
- Automatic type inference for injected objects
- Seamless with async/await
- Test-friendly (easy to override Depends)

**Implementation**:
```python
def get_account_repository() -> AccountRepository:
    """Factory function for repository"""
    da = OracleDataAccess(get_pool())
    return AccountRepository(da)

@app.get("/api/accounts")
async def list_accounts(
    repo: AccountRepository = Depends(get_account_repository)
):
    """FastAPI automatically injects repository"""
    return repo.get_all()
```

**Trade-offs**:
- ✅ Testability (override in tests)
- ✅ Clean code (explicit dependencies)
- ✅ FastAPI integration (standard pattern)
- ❌ Requires understanding FastAPI Depends

---

### ADR 5: Structured Logging with Structlog

**Decision**: Use structlog for JSON structured logging

**Rationale**:
- JSON output integrates with CloudWatch Logs
- Key-value pairs enable log querying and analysis
- Performance metrics captured automatically
- Request tracing through context

**Implementation**:
```python
logger.info(
    "account_created",
    account_id=account.id,
    name=account.name,
    created_by=user,
    elapsed_ms=elapsed
)
# Output: {"event": "account_created", "account_id": 1, "name": "Acme", ...}
```

**CloudWatch Insights Query**:
```
fields @timestamp, account_id, elapsed_ms
| filter event = "account_created"
| stats avg(elapsed_ms), max(elapsed_ms), pct(elapsed_ms, 95)
```

**Trade-offs**:
- ✅ Queryability (CloudWatch Insights)
- ✅ Performance insights (timing data)
- ✅ Debugging (full context in logs)
- ❌ Human readability (less readable raw logs)

---

## Performance Tuning

### 1. Connection Pool Sizing

**Formula**:
```
pool_max = (concurrency × avg_query_time_seconds) / timeout_seconds
```

**Examples**:
```
# Development
concurrency = 10, query_time = 0.1s, timeout = 30s
pool_max = (10 × 0.1) / 30 = 0.3 → min 2

# Production
concurrency = 100, query_time = 0.2s, timeout = 60s
pool_max = (100 × 0.2) / 60 = 0.3 → min 10
```

**Configuration**:
```python
OracleConfig(
    pool_min=2,      # Minimum connections to keep open
    pool_max=20,     # Maximum connections allowed
    pool_increment=5 # Grow by 5 at a time
)
```

### 2. Query Optimization

**Index Strategy**:
```sql
-- Create indexes on frequently filtered columns
CREATE INDEX IDX_OPP_STAGE ON OPPORTUNITIES(STAGE);
CREATE INDEX IDX_OPP_ACCOUNT ON OPPORTUNITIES(ACCOUNT_ID);
CREATE INDEX IDX_OPP_AMOUNT ON OPPORTUNITIES(AMOUNT);

-- Composite index for common filter combinations
CREATE INDEX IDX_OPP_STAGE_AMOUNT ON OPPORTUNITIES(STAGE, AMOUNT DESC);

-- Analyze table for query optimizer
ANALYZE TABLE OPPORTUNITIES COMPUTE STATISTICS;
```

**Query Performance Analysis**:
```sql
-- Enable EXPLAIN PLAN
EXPLAIN PLAN FOR
SELECT * FROM OPPORTUNITIES 
WHERE STAGE = 'Proposal' 
  AND AMOUNT > 100000 
  AND PROBABILITY > 50;

-- View execution plan
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
```

### 3. Lambda Optimization

**Memory & Duration Relationship**:
```
More memory → Faster CPU → Faster execution → Lower overall cost
```

**Recommended Settings**:
```
Development:     256 MB,  30 second timeout
Staging:         512 MB,  60 second timeout
Production:      1024 MB, 60 second timeout
```

**CloudWatch Metric**:
```
Billed Duration = Max(actual_duration, 100ms)
Cost = (memory_mb / 1024) × (billed_duration_ms / 1000) × price_per_gb_second
```

### 4. Cold Start Mitigation

**Techniques**:

**A. Pre-warm connections on module load**:
```python
@lru_cache(maxsize=1)
def get_database_pool():
    pool = get_pool()  # Initialize on first invocation
    pool.health_check()  # Verify connectivity
    return pool
```

**B. Provisioned Concurrency (AWS)**:
```bash
# Reserve concurrent Lambda instances
aws lambda put-provisioned-concurrency-config \
  --function-name oracle-api \
  --provisioned-concurrent-executions 10
```

**C. Lambda@Edge for API caching**:
```
CloudFront edge locations cache responses
→ Reduces origin hits
→ Reduces cold starts
```

---

## Security Best Practices

### 1. Secrets Management

**Use AWS Secrets Manager (not environment variables)**:

```python
import json
import boto3

def get_db_credentials():
    """Retrieve credentials from Secrets Manager."""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    
    response = client.get_secret_value(SecretId='oracle/prod/credentials')
    secret = json.loads(response['SecretString'])
    
    return OracleConfig(
        host=secret['host'],
        port=secret['port'],
        service_name=secret['service_name'],
        user=secret['user'],
        password=secret['password']
    )
```

**Terraform Configuration**:
```hcl
# Create secret
resource "aws_secretsmanager_secret" "oracle_credentials" {
  name = "oracle/prod/credentials"
  
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "oracle_credentials" {
  secret_id = aws_secretsmanager_secret.oracle_credentials.id
  
  secret_string = jsonencode({
    host          = aws_db_instance.oracle.address
    port          = aws_db_instance.oracle.port
    service_name  = "ORCL"
    user          = "app_user"
    password      = random_password.oracle_password.result
  })
}

# Lambda IAM policy
resource "aws_iam_policy" "lambda_secrets_access" {
  name = "lambda-secrets-access"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = aws_secretsmanager_secret.oracle_credentials.arn
    }]
  })
}
```

### 2. Network Security

**Use VPC with Private Subnets**:
```hcl
# Lambda in private subnet
resource "aws_lambda_function" "oracle_api" {
  function_name = "oracle-api"
  vpc_config {
    subnet_ids         = [aws_subnet.private.id]
    security_group_ids = [aws_security_group.lambda.id]
  }
}

# RDS Oracle in private subnet
resource "aws_db_instance" "oracle" {
  db_subnet_group_name   = aws_db_subnet_group.private.name
  publicly_accessible    = false  # Never public
  skip_final_snapshot    = false
  final_snapshot_identifier = "oracle-prod-final"
}

# Security group allows Lambda → Oracle only
resource "aws_security_group_rule" "lambda_to_oracle" {
  type                     = "ingress"
  from_port                = 1521
  to_port                  = 1521
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.lambda.id
  security_group_id        = aws_security_group.oracle.id
}
```

### 3. API Authentication

**Use API Gateway Authorization**:
```hcl
# OAuth 2.0 authorizer
resource "aws_api_gateway_authorizer" "oauth" {
  name            = "oauth-authorizer"
  identity_source = "method.request.header.Authorization"
  
  authorizer_uri = aws_lambda_function.authorizer.invoke_arn
  
  authorizer_result_ttl_in_seconds = 300
}

# Protect endpoints
resource "aws_api_gateway_integration" "account_list" {
  http_method             = "GET"
  resource_id             = aws_api_gateway_resource.accounts.id"
  authorization_type      = "CUSTOM"
  authorizer_id           = aws_api_gateway_authorizer.oauth.id
}
```

### 4. Audit Logging

**Enable CloudTrail and VPC Flow Logs**:
```bash
# CloudTrail for API calls
aws cloudtrail create-trail \
  --name oracle-api-audit \
  --s3-bucket-name oracle-audit-logs

# VPC Flow Logs for network traffic
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-xxxxx \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs
```

---

## Monitoring & Alerting

### CloudWatch Dashboards

**Create comprehensive dashboard**:
```hcl
resource "aws_cloudwatch_dashboard" "oracle_api" {
  dashboard_name = "oracle-api-prod"
  
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", { stat = "Average" }],
            ["AWS/Lambda", "Errors", { stat = "Sum" }],
            ["AWS/Lambda", "Throttles", { stat = "Sum" }],
            ["AWS/RDS", "DatabaseConnections"],
            ["AWS/RDS", "CPUUtilization"],
            ["AWS/RDS", "FreeableMemory"]
          ]
          period = 300
          stat   = "Average"
          region = "us-east-1"
        }
      }
    ]
  })
}
```

### CloudWatch Alarms

```hcl
# Lambda duration alarm
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "oracle-api-lambda-duration-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Average"
  threshold           = "5000"  # 5 seconds
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# Lambda error alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "oracle-api-lambda-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# RDS CPU alarm
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "oracle-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}
```

### Log Analysis

**CloudWatch Insights Queries**:

```
# P95 response time by endpoint
fields @timestamp, path, duration_ms
| filter ispresent(duration_ms)
| stats pct(duration_ms, 95) as p95, pct(duration_ms, 99) as p99 by path

# Error rate by endpoint
fields @timestamp, path, status_code
| stats count() as total, sum(status_code >= 500) as errors by path
| fields path, errors, total, round(errors/total*100, 2) as error_rate_pct

# Database connection pool health
fields @timestamp, active_connections, idle_connections
| stats max(active_connections) as max_active, avg(idle_connections) as avg_idle

# Slow queries
fields @timestamp, query_type, elapsed_ms
| filter elapsed_ms > 1000
| stats count() as slow_queries, avg(elapsed_ms) as avg_time
```

---

## Disaster Recovery

### Backup Strategy

**RDS Automated Backups**:
```hcl
resource "aws_db_instance" "oracle" {
  backup_retention_period = 30  # Keep 30-day backups
  backup_window          = "03:00-04:00"  # Off-peak
  multi_az               = true  # High availability
  skip_final_snapshot    = false
  final_snapshot_identifier = "oracle-prod-final-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
}
```

**Point-in-Time Recovery**:
```bash
# Restore to specific point in time
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier oracle-prod \
  --target-db-instance-identifier oracle-restored \
  --restore-time 2026-01-28T14:30:00Z
```

**Cross-Region Replication**:
```hcl
provider "aws" {
  alias  = "replica_region"
  region = "us-west-2"
}

resource "aws_db_instance" "oracle_replica" {
  provider                  = aws.replica_region
  identifier                = "oracle-prod-replica"
  replicate_source_db       = aws_db_instance.oracle.identifier
  publicly_accessible       = false
  skip_final_snapshot       = true
  auto_minor_version_upgrade = true
}
```

---

## Cost Optimization

### Estimated Monthly Costs (US East)

```
RDS Oracle (db.t3.medium):
  - Instance:        ~$0.30/hour = $219/month
  - Storage (20GB):  ~$2.30/month
  - Backup:          ~$5/month
  - Data transfer:   ~$10/month
  Total:             ~$237/month

Lambda (100K requests):
  - Compute:         ~$0.00002 × 100K × 1GB = $2/month
  - Storage:         ~$0.20/month
  Total:             ~$2.20/month

API Gateway:
  - Requests:        ~$0.000035 × 100K = $3.50/month
  - Cache:           ~$0.02/hour = $15/month
  Total:             ~$18.50/month

CloudWatch:
  - Logs:            ~$0.50 per GB ingested = ~$20/month
  - Metrics:         ~$0.30 per metric = ~$10/month
  Total:             ~$30/month

TOTAL MONTHLY:      ~$288/month (~$3,500/year)
```

### Cost Reduction Strategies

1. **Use Reserved Instances (RDS)**:
   - 1-year reservation: ~40% discount
   - 3-year reservation: ~60% discount

2. **Use Savings Plans (Lambda)**:
   - 1-year commitment: ~17% discount
   - 3-year commitment: ~33% discount

3. **Optimize data transfer**:
   - Keep Lambda and RDS in same AZ (no cross-AZ charges)
   - Use VPC endpoints to avoid NAT gateway costs

4. **Compress logs**:
   - Use Lambda function to compress old logs
   - Move to S3 Glacier for archival

---

## Deployment Checklist

### Pre-Deployment (Dev/Staging)

- [ ] All unit tests pass (100% coverage)
- [ ] Integration tests pass with mock Oracle
- [ ] Docker image builds successfully
- [ ] Code passes linting (flake8, pylint)
- [ ] Security scan passes (bandit)
- [ ] Dependency versions pinned in requirements.txt
- [ ] Environment variables documented
- [ ] Error handling tested for all paths

### Deployment to AWS

- [ ] RDS Oracle instance created and healthy
- [ ] Secret created in Secrets Manager
- [ ] IAM roles and policies configured
- [ ] VPC and security groups configured
- [ ] CloudWatch log groups created
- [ ] Lambda function deployed
- [ ] API Gateway endpoints configured
- [ ] SSL certificate configured
- [ ] DNS records updated

### Post-Deployment

- [ ] Smoke tests pass against production
- [ ] Logs flowing to CloudWatch
- [ ] CloudWatch alarms activated
- [ ] Database replication verified
- [ ] Monitoring dashboard populated
- [ ] Alert recipients configured
- [ ] Runbook documented
- [ ] On-call handoff complete

---

## Troubleshooting Runbook

### Symptom: Slow API responses (P95 > 5s)

**Investigation**:
```bash
# 1. Check Lambda duration
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=oracle-api \
  --start-time 2026-01-28T00:00:00Z \
  --end-time 2026-01-28T23:59:59Z \
  --period 300 \
  --statistics Average,Maximum

# 2. Check Oracle CPU
aws rds describe-db-instances \
  --db-instance-identifier oracle-prod \
  --query 'DBInstances[0].[DBInstanceStatus, PendingModifiedValues]'

# 3. Check CloudWatch Logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/oracle-api \
  --filter-pattern "elapsed_ms > 5000"
```

**Resolution**:
1. Check query execution plans
2. Add database indexes if needed
3. Increase Lambda memory allocation
4. Check connection pool saturation
5. Consider RDS read replicas

---

## Conclusion

This senior-level implementation provides:

✅ **Production-ready code** with best practices
✅ **Comprehensive testing** with mocks and fixtures
✅ **Secure deployment** using AWS best practices
✅ **Monitoring & alerting** for operational visibility
✅ **Performance optimization** strategies documented
✅ **Disaster recovery** with automated backups
✅ **Cost optimization** through reserved capacity

**Next Steps**:
1. Deploy to AWS using provided Terraform
2. Monitor CloudWatch metrics and logs
3. Implement automated testing in CI/CD
4. Establish on-call rotations and runbooks
5. Plan for scaling as load increases

