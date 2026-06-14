# AWS + Oracle + Python Example Application

**Senior-Level Architecture Pattern**

Complete production-ready integration combining AWS Lambda, Oracle Database, and FastAPI with enterprise-grade patterns.

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Components](#components)
3. [Setup & Installation](#setup--installation)
4. [Usage Examples](#usage-examples)
5. [Design Patterns](#design-patterns)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                      │
│                    (Web, Mobile, Desktop)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      AWS API Gateway                            │
│              (Authentication, Rate Limiting)                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Lambda Function                          │
│              (FastAPI ASGI Handler via Mangum)                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               FastAPI Application                        │  │
│  │                                                          │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │            Route Handlers                        │  │  │
│  │  │  - GET /api/accounts                            │  │  │
│  │  │  - POST /api/opportunities                      │  │  │
│  │  │  - GET /api/reports/summary                     │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  │                      ↓                                   │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │        Repository Layer (Data Access)            │  │  │
│  │  │  - AccountRepository                            │  │  │
│  │  │  - OpportunityRepository                        │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  │                      ↓                                   │  │
│  │  ┌───────────────────────────────────────────────────┐  │  │
│  │  │       Oracle Integration Module                  │  │  │
│  │  │  - Connection Pool                             │  │  │
│  │  │  - Query Builder                               │  │  │
│  │  │  - Error Handling                              │  │  │
│  │  └───────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ JDBC
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│            AWS RDS Oracle Database Instance                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Tables (Accounts, Contacts, Opps)           │  │
│  │            Indexes (for performance)                    │  │
│  │            Stored Procedures (optional)                 │  │
│  │            Audit Logs (Activities)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│               Monitoring & Logging (CloudWatch)                 │
│     - Lambda execution logs                                     │
│     - Oracle connection metrics                                 │
│     - API response times                                        │
│     - Error tracking                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. **oracle_integration.py** - Connection & Query Management
Handles low-level Oracle database operations with production-grade patterns:

**Key Classes:**
- `OracleConfig` - Configuration management with environment variables
- `OracleConnectionPool` - Thread-safe connection pooling with health checks
- `OracleQueryBuilder` - Parameterized SQL queries (prevents SQL injection)
- `OracleDataAccess` - Execute queries with error handling and metrics

**Features:**
- Automatic connection pooling (min/max connections)
- Connection health verification
- Parameterized queries for security
- Comprehensive error handling
- Structured logging with metrics

**Example:**
```python
from oracle_integration import get_pool, OracleDataAccess, OracleQueryBuilder

# Get connection pool (singleton)
pool = get_pool()

# Create data access layer
da = OracleDataAccess(pool)

# Build parameterized query
query = (OracleQueryBuilder()
         .select('ID', 'NAME', 'AMOUNT')
         .from_table('OPPORTUNITIES')
         .where('STAGE', '=', 'Proposal')
         .where('AMOUNT', '>', 100000)
         .order_by('AMOUNT', 'DESC')
         .limit(10))

sql, params = query.build()

# Execute safely
results = da.execute_query(sql, params)
```

### 2. **oracle_models.py** - Data Models & Validation
Pydantic models with Oracle table definitions:

**Key Models:**
- `Account`, `AccountCreate`, `AccountUpdate`
- `Contact`, `ContactCreate`
- `Opportunity`, `OpportunityCreate`, `OpportunityUpdate`
- `OpportunityFilter`, `OpportunitySummary`
- Enums: `OpportunityStage`, `AccountType`, `RecordStatus`

**Features:**
- Field validation with constraints
- Automatic serialization/deserialization
- JSON schema generation
- Oracle DDL definitions included

**Example:**
```python
from oracle_models import OpportunityCreate, OpportunityStage
from datetime import date

opp = OpportunityCreate(
    name="Enterprise License Deal",
    account_id=1,
    amount=250_000,
    stage=OpportunityStage.PROPOSAL,
    probability=75,
    close_date=date(2026, 3, 31)
)
# Automatically validates fields
```

### 3. **oracle_repository.py** - Data Access Layer
Repository pattern for clean data access abstraction:

**Key Classes:**
- `BaseRepository` - Abstract base with CRUD interface
- `AccountRepository` - Account CRUD + filtering
- `OpportunityRepository` - Pipeline management + aggregations

**Features:**
- CRUD operations (Create, Read, Update, Delete)
- Advanced filtering and pagination
- Aggregations (summaries, reports)
- Batch operations
- Transaction support
- Comprehensive logging

**Example:**
```python
from oracle_repository import OpportunityRepository
from oracle_models import OpportunityFilter

# Get repository
repo = OpportunityRepository(da, account_repo)

# Filter opportunities
filter_query = OpportunityFilter(
    stage=OpportunityStage.PROPOSAL,
    min_amount=100_000,
    limit=50
)
opportunities = repo.filter(filter_query)

# Get pipeline summary
summary = repo.get_summary()
print(f"Total pipeline: ${summary.total_value}")
```

### 4. **oracle_fastapi.py** - REST API Endpoints
FastAPI application with dependency injection and error handling:

**Endpoints:**
- `GET /` - Welcome/documentation
- `GET /health` - Health check with Oracle status
- `GET /api/accounts` - List accounts
- `POST /api/accounts` - Create account
- `GET /api/opportunities` - List opportunities
- `POST /api/opportunities/batch` - Batch create
- `GET /api/reports/opportunities-summary` - Pipeline summary

**Features:**
- RESTful design
- Request/response validation
- Dependency injection (repositories)
- Authentication headers (x-user-id)
- Comprehensive error handling
- Structured logging
- CORS enabled

---

## Setup & Installation

### Prerequisites
```
- Python 3.11+
- Oracle Database 19c+ (or AWS RDS Oracle)
- pip or conda
- AWS account (for Lambda deployment)
```

### Local Development

**1. Install Oracle client (Windows):**
```powershell
# Download Oracle Instant Client from:
# https://www.oracle.com/database/technologies/instant-client/downloads.html

# Or use Python package
pip install oracledb
```

**2. Install dependencies:**
```powershell
cd c:\Users\desha\Python Projects\python-test-env
.\.venv\Scripts\Activate.ps1
pip install -r src/requirements.txt
pip install oracledb structlog  # Oracle-specific
```

**3. Configure environment variables:**
```powershell
# .env or environment variables
$env:ORACLE_HOST = "oracle.example.com"
$env:ORACLE_PORT = "1521"
$env:ORACLE_SERVICE_NAME = "ORCL"
$env:ORACLE_USER = "app_user"
$env:ORACLE_PASSWORD = "secure_password"
$env:ORACLE_POOL_MIN = "2"
$env:ORACLE_POOL_MAX = "10"
```

**4. Create Oracle tables:**
```sql
-- Connect to Oracle
sqlplus app_user@ORCL

-- Run DDL from oracle_models.py
@create_tables.sql  -- See OracleTableDefinition class
```

**5. Run locally:**
```powershell
uvicorn src.oracle_fastapi:app --reload --port 8000
```

Visit http://localhost:8000/docs for interactive documentation.

### AWS RDS Oracle Setup

**1. Create RDS instance (Terraform/Console):**
```bash
aws rds create-db-instance \
  --db-instance-identifier oracle-prod \
  --db-instance-class db.t3.medium \
  --engine oracle-se2 \
  --master-username admin \
  --master-user-password YourSecurePassword123!
```

**2. Configure security group:**
```bash
# Allow inbound on port 1521 from Lambda security group
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 1521 \
  --source-security-group-id sg-lambda
```

**3. Create IAM secret for credentials:**
```bash
aws secretsmanager create-secret \
  --name oracle/prod/credentials \
  --secret-string '{
    "host": "oracle-prod.xxxxx.rds.amazonaws.com",
    "port": 1521,
    "service_name": "ORCL",
    "user": "app_user",
    "password": "SecurePassword123!"
  }'
```

---

## Usage Examples

### Example 1: Create an Account

**Python:**
```python
from oracle_repository import AccountRepository
from oracle_models import AccountCreate, AccountType

repo = AccountRepository(da)

account = AccountCreate(
    name="Acme Corporation",
    industry="Technology",
    account_type=AccountType.CUSTOMER,
    employee_count=1500,
    annual_revenue=500_000_000
)

created = repo.create(account, created_by="john.doe@company.com")
print(f"Created account {created.id}: {created.name}")
```

**API Request:**
```bash
curl -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -H "X-User-Id: john.doe@company.com" \
  -d '{
    "name": "Acme Corporation",
    "industry": "Technology",
    "account_type": "Customer",
    "employee_count": 1500,
    "annual_revenue": 500000000
  }'
```

### Example 2: Create Sales Opportunity

**Python:**
```python
from oracle_models import OpportunityCreate, OpportunityStage
from datetime import date

repo = OpportunityRepository(da, account_repo)

opp = OpportunityCreate(
    name="Enterprise License - Year 2",
    account_id=1,
    amount=350_000,
    stage=OpportunityStage.PROPOSAL,
    probability=80,
    close_date=date(2026, 6, 30),
    description="Expansion deal for additional 500 users"
)

created = repo.create(opp, created_by="sales@company.com")
print(f"Created opportunity: {created.name}")
```

**API Request:**
```bash
curl -X POST http://localhost:8000/api/opportunities \
  -H "Content-Type: application/json" \
  -H "X-User-Id: sales@company.com" \
  -d '{
    "name": "Enterprise License - Year 2",
    "account_id": 1,
    "amount": 350000,
    "stage": "Proposal",
    "probability": 80,
    "close_date": "2026-06-30",
    "description": "Expansion deal for additional 500 users"
  }'
```

### Example 3: Pipeline Summary Report

**Python:**
```python
repo = OpportunityRepository(da, account_repo)

summary = repo.get_summary()
print(f"Total Opportunities: {summary.total_opportunities}")
print(f"Total Pipeline Value: ${summary.total_value:,.2f}")
print(f"Average Deal Size: ${summary.average_deal_size:,.2f}")

for stage, data in summary.by_stage.items():
    print(f"  {stage}: {data['count']} deals, ${data['value']:,.0f}")
```

**API Request:**
```bash
curl http://localhost:8000/api/reports/opportunities-summary
```

**Response:**
```json
{
  "total_opportunities": 45,
  "total_value": 15750000,
  "by_stage": {
    "Qualification": { "count": 15, "value": 3000000 },
    "Proposal": { "count": 20, "value": 7500000 },
    "Negotiation": { "count": 10, "value": 5250000 }
  },
  "average_deal_size": 350000,
  "win_probability_weighted": 65
}
```

### Example 4: Filter & Batch Operations

**Batch Create:**
```python
from oracle_models import BatchOpportunityCreate

batch = BatchOpportunityCreate(
    opportunities=[
        OpportunityCreate(...),
        OpportunityCreate(...),
        OpportunityCreate(...)
    ],
    created_by="bulk_import@company.com"
)

result = repo.batch_create(batch)
print(f"Created {result.successful} opportunities")
print(f"Failed: {result.failed}")
```

---

## Design Patterns

### 1. **Connection Pool Pattern**
```python
# Singleton pattern with lazy initialization
pool = get_pool()  # First call initializes
pool.initialize()

# Context manager for safe connection handling
with pool.get_connection() as conn:
    cursor = conn.cursor()
    # Use connection
    # Automatic cleanup on exit
```

**Benefits:**
- Reuse connections instead of creating new ones
- Automatic connection lifecycle management
- Health checks and recovery
- Thread-safe operations

### 2. **Repository Pattern**
```python
class BaseRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Model]:
        pass
    
    @abstractmethod
    def create(self, obj: CreateModel) -> Model:
        pass

# Concrete implementation
class AccountRepository(BaseRepository):
    def get_by_id(self, id: int) -> Optional[Account]:
        # Implementation
        pass
```

**Benefits:**
- Separation of concerns (business logic ↔ data access)
- Easy testing with mock repositories
- Flexible storage (swap Oracle for PostgreSQL, etc.)
- Consistent CRUD interface

### 3. **Query Builder Pattern**
```python
# Prevents SQL injection through parameterization
query = (OracleQueryBuilder()
         .select('ID', 'NAME')
         .from_table('ACCOUNTS')
         .where('INDUSTRY', '=', user_input)  # SAFE!
         .limit(10))

sql, params = query.build()
# sql: "SELECT ID, NAME FROM ACCOUNTS WHERE INDUSTRY = :0 LIMIT 10"
# params: {'0': user_input}
```

**Benefits:**
- SQL injection prevention
- Readable query construction
- Type-safe parameters
- Automatic escaping

### 4. **Dependency Injection Pattern**
```python
from fastapi import Depends

def get_data_access() -> OracleDataAccess:
    pool = get_pool()
    return OracleDataAccess(pool)

@app.get("/api/accounts")
async def list_accounts(
    repo: AccountRepository = Depends(get_account_repository)
):
    # FastAPI automatically injects repository
    return repo.get_all()
```

**Benefits:**
- Easy testing (inject mocks)
- Loose coupling
- Dependency management
- Clear interfaces

### 5. **Error Handling & Logging**
```python
import structlog

logger = structlog.get_logger(__name__)

try:
    result = repo.create(account, created_by=user)
    logger.info("account_created", account_id=result.id)
except OracleException as e:
    logger.error("create_failed", error=str(e), exc_info=True)
    raise HTTPException(status_code=500)
```

**Benefits:**
- Structured logging (JSON format)
- Traceable errors with context
- Production-ready debugging
- Performance metrics

---

## Testing

### Unit Tests

**Test models and validation:**
```python
from oracle_models import OpportunityCreate, OpportunityStage
from datetime import date

def test_opportunity_validation():
    # Valid opportunity
    opp = OpportunityCreate(
        name="Deal",
        account_id=1,
        amount=100_000,
        stage=OpportunityStage.PROPOSAL,
        probability=75,
        close_date=date(2026, 3, 31)
    )
    assert opp.name == "Deal"
    
    # Invalid: probability out of range
    with pytest.raises(ValidationError):
        OpportunityCreate(
            name="Deal",
            account_id=1,
            amount=100_000,
            stage=OpportunityStage.PROPOSAL,
            probability=150,  # Invalid!
            close_date=date(2026, 3, 31)
        )
```

### Integration Tests

**Test with mock Oracle:**
```python
from unittest.mock import Mock, patch

def test_repository_get_all():
    # Mock data access
    mock_da = Mock(spec=OracleDataAccess)
    mock_da.execute_query.return_value = [
        {'ID': 1, 'NAME': 'Acme', 'INDUSTRY': 'Tech', ...},
        {'ID': 2, 'NAME': 'Beta Inc', 'INDUSTRY': 'Finance', ...}
    ]
    
    repo = AccountRepository(mock_da)
    accounts = repo.get_all()
    
    assert len(accounts) == 2
    assert accounts[0].name == 'Acme'
    mock_da.execute_query.assert_called_once()
```

### End-to-End Tests

**Test complete flow:**
```python
def test_complete_sales_flow():
    # 1. Create account
    account = repo_account.create(
        AccountCreate(name="TestCorp", industry="Tech"),
        created_by="test"
    )
    
    # 2. Create contact
    contact = repo_contact.create(
        ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@testcorp.com",
            account_id=account.id
        ),
        created_by="test"
    )
    
    # 3. Create opportunity
    opp = repo_opp.create(
        OpportunityCreate(
            name="Test Deal",
            account_id=account.id,
            amount=100_000,
            stage=OpportunityStage.QUALIFICATION,
            probability=25,
            close_date=date(2026, 6, 30)
        ),
        created_by="test"
    )
    
    # 4. Verify
    assert opp.account_id == account.id
    assert repo_opp.get_by_id(opp.id) is not None
```

**Run tests:**
```powershell
# All tests
pytest src/ -v --cov=src

# Specific test file
pytest src/test_oracle_models.py -v

# With Oracle mock
pytest src/test_oracle_repository.py -v
```

---

## Deployment

### AWS Lambda Deployment

**1. Create Lambda function:**
```bash
# Package application
cd c:\Users\desha\Python Projects\python-test-env
zip -r lambda_deployment.zip src/ .venv/lib/python3.11/site-packages/

# Upload to Lambda
aws lambda create-function \
  --function-name oracle-api \
  --runtime python3.11 \
  --handler src.oracle_fastapi.app \
  --zip-file fileb://lambda_deployment.zip \
  --timeout 60 \
  --memory-size 512 \
  --environment Variables='{
    "ORACLE_HOST": "oracle.xxxxx.rds.amazonaws.com",
    "ORACLE_USER": "app_user"
  }' \
  --vpc-config SubnetIds=subnet-xxxxx,SecurityGroupIds=sg-xxxxx
```

**2. Create API Gateway:**
```bash
aws apigateway create-rest-api \
  --name oracle-api \
  --description "AWS + Oracle Integration API"

# Configure routes and integrations
# (See terraform/ for complete configuration)
```

**3. Use Terraform (recommended):**
```bash
cd terraform

# Configure variables
cp oracle_deployment.tfvars.example oracle_deployment.tfvars
# Edit with your values

# Deploy
terraform init
terraform plan -var-file=oracle_deployment.tfvars
terraform apply -var-file=oracle_deployment.tfvars

# Get outputs
terraform output api_endpoint
```

### Environment Variables (Secrets Manager)
```bash
# Store in AWS Secrets Manager
aws secretsmanager create-secret \
  --name oracle-app-secrets \
  --secret-string '{
    "ORACLE_HOST": "oracle.xxxxx.rds.amazonaws.com",
    "ORACLE_USER": "app_user",
    "ORACLE_PASSWORD": "SecurePassword123!"
  }'

# Lambda IAM policy allows reading secret
```

---

## Troubleshooting

### Issue: Connection Timeout

**Symptom:**
```
OracleException: Connection timeout to oracle.example.com:1521
```

**Solutions:**
1. Verify Oracle host/port in environment variables
2. Check security group allows inbound on port 1521
3. Verify database is running: `sqlplus app_user@ORCL`
4. Increase connection timeout: `ORACLE_CONNECTION_TIMEOUT=60`

### Issue: SQL Injection Attempts

**Symptom:**
```
Parameterized query received unexpected value type
```

**Solution:**
Always use QueryBuilder with parameterized queries:
```python
# ❌ WRONG - vulnerable to injection
sql = f"SELECT * FROM ACCOUNTS WHERE NAME = '{user_input}'"

# ✅ CORRECT - safe
query = OracleQueryBuilder().from_table('ACCOUNTS').where('NAME', '=', user_input)
sql, params = query.build()
```

### Issue: Performance Degradation

**Symptoms:**
- Slow queries
- High connection count
- Memory usage increasing

**Solutions:**
```python
# 1. Check query performance
logger.info("query_executed", elapsed_ms=elapsed, query=sql[:100])

# 2. Verify indexes exist
CREATE INDEX IDX_OPPORTUNITIES_STAGE ON OPPORTUNITIES(STAGE);

# 3. Tune pool size
ORACLE_POOL_MIN = 2
ORACLE_POOL_MAX = 20  # Adjust based on workload

# 4. Use EXPLAIN PLAN
EXPLAIN PLAN FOR SELECT * FROM OPPORTUNITIES WHERE STAGE = 'Proposal';
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY);
```

### Issue: Batch Operations Failing

**Solution:**
```python
# Check individual records
for opp in batch.opportunities:
    try:
        repo.create(opp, created_by=user)
    except Exception as e:
        logger.error("record_failed", opp_name=opp.name, error=str(e))
        # Continue with next record
```

---

## Best Practices

### 1. **Always use parameterized queries**
```python
# ✅ GOOD
query.where('AMOUNT', '>', user_amount)

# ❌ BAD
query.where(f'AMOUNT > {user_amount}')
```

### 2. **Handle errors gracefully**
```python
try:
    account = repo.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404)
except OracleException as e:
    logger.error("db_error", error=str(e))
    raise HTTPException(status_code=500)
```

### 3. **Use transactions for related operations**
```python
operations = [
    (create_account_sql, account_params),
    (create_contact_sql, contact_params),
    (create_opp_sql, opp_params)
]
da.execute_transaction(operations)
```

### 4. **Log all significant operations**
```python
logger.info("account_created", 
           account_id=account.id,
           name=account.name,
           user=created_by)

logger.error("account_creation_failed",
            error=str(e),
            exc_info=True)
```

### 5. **Monitor connection pool health**
```python
health = pool.health_check()
logger.info("pool_health", 
           status=health['status'],
           metrics=health['metrics'])
```

### 6. **Validate all inputs**
```python
# Pydantic models validate automatically
try:
    opp = OpportunityCreate(**user_input)
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

### 7. **Use pagination for large result sets**
```python
# Don't return all 1M records at once
accounts = repo.get_all(limit=100, offset=skip)
```

### 8. **Implement soft deletes**
```python
# Update STATUS to 'Inactive' instead of DELETE
repo.delete(account_id)  # Sets STATUS='Inactive'
```

---

## Performance Characteristics

**Typical Response Times (AWS Lambda + RDS Oracle):**
- Simple SELECT (indexed): 10-50ms
- CREATE with validation: 30-100ms
- Complex JOIN query: 50-200ms
- Batch create (100 records): 500-2000ms

**Scaling:**
- Lambda: Automatic (up to account limits)
- RDS Oracle: db.t3.small for dev, db.m5.large for prod
- Connection pool: 2-20 connections based on load

---

## Next Steps

1. **Local Testing**
   ```powershell
   .\run-tests-docker.ps1 -TestType integration
   ```

2. **Deploy to AWS**
   ```bash
   cd terraform
   terraform apply
   ```

3. **Production Monitoring**
   - Set up CloudWatch alarms
   - Monitor Lambda duration and errors
   - Track database connection count

4. **Advanced Features**
   - Add authentication (OAuth2)
   - Implement caching (ElastiCache)
   - Add event notifications (SNS/SQS)

---

**For questions or issues, see:** DOCKER_TESTING_README.md, TERRAFORM_DEPLOYMENT_GUIDE.md
