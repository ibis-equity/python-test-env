"""
AWS + Oracle Integration Package

Provides complete integration for Oracle database operations with AWS Lambda/FastAPI.

Modules:
  - oracle_integration: Connection pool, query builder, data access layer
  - oracle_models: Pydantic data models with validation
  - oracle_repository: Repository pattern for data abstraction
  - oracle_fastapi: FastAPI application with REST endpoints
  - oracle_lambda: AWS Lambda handler with Mangum

Example:
    from src.aws_oracle import get_pool, OracleDataAccess, AccountRepository
    
    pool = get_pool()
    da = OracleDataAccess(pool)
    repo = AccountRepository(da)
"""

from .oracle_integration import (
    OracleConfig,
    OracleConnectionPool,
    OracleQueryBuilder,
    OracleDataAccess,
    OracleException,
    OracleQueryError,
    OracleProcedureError,
    OracleTransactionError,
    get_pool,
    close_pool,
)

from .oracle_models import (
    Account,
    AccountCreate,
    AccountUpdate,
    Contact,
    ContactCreate,
    Opportunity,
    OpportunityCreate,
    OpportunityUpdate,
    OpportunityFilter,
    OpportunitySummary,
    BatchOpportunityCreate,
    OpportunityStage,
    AccountType,
    RecordStatus,
)

from .oracle_repository import (
    BaseRepository,
    AccountRepository,
    OpportunityRepository,
)

from .oracle_fastapi import app

__all__ = [
    # Integration
    "OracleConfig",
    "OracleConnectionPool",
    "OracleQueryBuilder",
    "OracleDataAccess",
    "OracleException",
    "OracleQueryError",
    "OracleProcedureError",
    "OracleTransactionError",
    "get_pool",
    "close_pool",
    # Models
    "Account",
    "AccountCreate",
    "AccountUpdate",
    "Contact",
    "ContactCreate",
    "Opportunity",
    "OpportunityCreate",
    "OpportunityUpdate",
    "OpportunityFilter",
    "OpportunitySummary",
    "BatchOpportunityCreate",
    "OpportunityStage",
    "AccountType",
    "RecordStatus",
    # Repository
    "BaseRepository",
    "AccountRepository",
    "OpportunityRepository",
    # FastAPI
    "app",
]

__version__ = "1.0.0"
__author__ = "Enterprise Development Team"
__description__ = "AWS + Oracle + Python Integration Example"
