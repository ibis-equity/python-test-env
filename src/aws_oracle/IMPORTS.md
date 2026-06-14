# Importing from src.aws_oracle

All Oracle integration modules have been organized into the `src/aws_oracle` package.

## Import Examples

### From Python Code
```python
# Import individual components
from src.aws_oracle import (
    get_pool,
    OracleDataAccess,
    OracleQueryBuilder,
    AccountRepository,
    OpportunityRepository,
    Account,
    Opportunity,
    OpportunityStage,
    app  # FastAPI application
)

# Or import the module itself
from src import aws_oracle

pool = aws_oracle.get_pool()
repo = aws_oracle.AccountRepository(...)
```

### Running Tests
```bash
# Run all tests in the aws_oracle package
pytest src/aws_oracle/test_oracle_components.py -v

# Run specific test class
pytest src/aws_oracle/test_oracle_components.py::TestOracleModels -v

# Run with coverage
pytest src/aws_oracle/ --cov=src.aws_oracle
```

### Running FastAPI Locally
```bash
# Run the FastAPI app from the new location
uvicorn src.aws_oracle.oracle_fastapi:app --reload --port 8000
```

### AWS Lambda Configuration
```
Handler: src.aws_oracle.oracle_lambda.handler
Runtime: Python 3.11
```

## Package Structure

```
src/aws_oracle/
├── __init__.py                    # Package exports
├── oracle_integration.py          # Connection pool, query builder
├── oracle_models.py              # Pydantic models, validation
├── oracle_repository.py          # Repository pattern, CRUD
├── oracle_fastapi.py             # REST API endpoints
├── oracle_lambda.py              # AWS Lambda handler
└── test_oracle_components.py     # Comprehensive tests
```

## What's Exported from __init__.py

The package's `__init__.py` re-exports all public APIs:

```python
from src.aws_oracle import (
    # Integration components
    OracleConfig,
    OracleConnectionPool,
    OracleQueryBuilder,
    OracleDataAccess,
    OracleException,
    get_pool,
    close_pool,
    
    # Models
    Account,
    AccountCreate,
    Opportunity,
    OpportunityCreate,
    OpportunityStage,
    
    # Repository
    AccountRepository,
    OpportunityRepository,
    
    # FastAPI app
    app,
)
```

## Relative Imports Within the Package

All modules within `src/aws_oracle` use relative imports:

```python
# In oracle_repository.py
from .oracle_integration import OracleDataAccess
from .oracle_models import Account

# In oracle_fastapi.py
from .oracle_integration import get_pool
from .oracle_repository import AccountRepository
from .oracle_models import Account
```

This makes the package self-contained and portable.
