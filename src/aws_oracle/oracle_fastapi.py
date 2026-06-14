"""
FastAPI Endpoints - AWS + Oracle Integration

Senior-level patterns:
- RESTful API design
- Error handling and logging
- Request/response validation
- Pagination and filtering
- Authentication (AWS Lambda IAM)
- CORS and security headers
- Health checks and metrics
"""

from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import List, Optional, Any
from datetime import datetime
import logging
import os

try:
    from .oracle_integration import get_pool, close_pool, OracleDataAccess, OracleException
    from .oracle_repository import AccountRepository, OpportunityRepository
    from .oracle_models import (
        Account, AccountCreate, AccountUpdate,
        Opportunity, OpportunityCreate, OpportunityUpdate,
        OpportunitySummary, OpportunityFilter,
        Contact, ContactCreate,
        QueryResult, BatchOpportunityCreate, BatchOperationResult
    )
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False

import structlog

# Configure logging
logger = structlog.get_logger(__name__)

# API Configuration
API_TITLE = "AWS + Oracle Integration API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
Senior-level FastAPI application integrating with:
- AWS Lambda (serverless compute)
- Oracle Database (persistent storage)
- Advanced patterns (connection pooling, query building, transactions)

Endpoints:
- Accounts: CRUD operations on sales accounts
- Opportunities: Sales pipeline management
- Contacts: Contact information management
- Reports: Aggregated views and analytics
"""

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    try:
        if ORACLE_AVAILABLE:
            pool = get_pool()
            pool.initialize()
            logger.info("oracle_pool_initialized_on_startup")
            
            # Perform health check
            health = pool.health_check()
            logger.info("oracle_health_check", status=health['status'])
    except Exception as e:
        logger.error("oracle_initialization_failed", error=str(e), exc_info=True)
    
    yield
    
    # Shutdown
    try:
        if ORACLE_AVAILABLE:
            close_pool()
            logger.info("oracle_pool_closed_on_shutdown")
    except Exception as e:
        logger.error("oracle_shutdown_error", error=str(e))


# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    lifespan=lifespan
)

# Dependency injection for repositories
def get_data_access() -> OracleDataAccess:
    """Get data access layer"""
    if not ORACLE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Oracle integration not available")
    
    pool = get_pool()
    return OracleDataAccess(pool)


def get_account_repository(da: OracleDataAccess = Depends(get_data_access)) -> AccountRepository:
    """Get account repository"""
    return AccountRepository(da)


def get_opportunity_repository(da: OracleDataAccess = Depends(get_data_access)) -> OpportunityRepository:
    """Get opportunity repository"""
    account_repo = AccountRepository(da)
    return OpportunityRepository(da, account_repo)


def get_current_user(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract user from request headers (from AWS Lambda context)"""
    return x_user_id or "system"


# Health and Info Endpoints
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API welcome"""
    return {
        "message": "Welcome to AWS + Oracle Integration API",
        "version": API_VERSION,
        "endpoints": {
            "health": "/health",
            "accounts": "/api/accounts",
            "opportunities": "/api/opportunities",
            "reports": "/api/reports"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        if not ORACLE_AVAILABLE:
            return {
                "status": "degraded",
                "oracle": "not_available"
            }
        
        pool = get_pool()
        oracle_health = pool.health_check()
        
        return {
            "status": "healthy" if oracle_health['status'] == 'healthy' else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "oracle": oracle_health,
            "version": API_VERSION
        }
    
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


# Account Endpoints
@app.get("/api/accounts", response_model=List[Account], tags=["Accounts"])
async def list_accounts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=10000, description="Number of records to return"),
    repo: AccountRepository = Depends(get_account_repository)
):
    """List all accounts with pagination"""
    try:
        accounts = repo.get_all(limit=limit, offset=skip)
        return accounts
    
    except OracleException as e:
        logger.error("accounts_list_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list accounts")


@app.get("/api/accounts/{account_id}", response_model=Account, tags=["Accounts"])
async def get_account(
    account_id: int,
    repo: AccountRepository = Depends(get_account_repository)
):
    """Get account by ID"""
    try:
        account = repo.get_by_id(account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return account
    
    except OracleException as e:
        logger.error("get_account_error", account_id=account_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get account")


@app.post("/api/accounts", response_model=Account, status_code=201, tags=["Accounts"])
async def create_account(
    account: AccountCreate,
    repo: AccountRepository = Depends(get_account_repository),
    user: str = Depends(get_current_user)
):
    """Create new account"""
    try:
        created = repo.create(account, created_by=user)
        logger.info("account_created", account_id=created.id, user=user)
        return created
    
    except OracleException as e:
        logger.error("create_account_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create account")


@app.put("/api/accounts/{account_id}", response_model=bool, tags=["Accounts"])
async def update_account(
    account_id: int,
    update: AccountUpdate,
    repo: AccountRepository = Depends(get_account_repository),
    user: str = Depends(get_current_user)
):
    """Update account"""
    try:
        success = repo.update(account_id, update, modified_by=user)
        
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")
        
        logger.info("account_updated", account_id=account_id, user=user)
        return success
    
    except OracleException as e:
        logger.error("update_account_error", account_id=account_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update account")


@app.delete("/api/accounts/{account_id}", response_model=bool, tags=["Accounts"])
async def delete_account(
    account_id: int,
    repo: AccountRepository = Depends(get_account_repository),
    user: str = Depends(get_current_user)
):
    """Delete account (soft delete)"""
    try:
        success = repo.delete(account_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")
        
        logger.info("account_deleted", account_id=account_id, user=user)
        return success
    
    except OracleException as e:
        logger.error("delete_account_error", account_id=account_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete account")


# Opportunity Endpoints
@app.get("/api/opportunities", response_model=List[Opportunity], tags=["Opportunities"])
async def list_opportunities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=10000),
    repo: OpportunityRepository = Depends(get_opportunity_repository)
):
    """List all opportunities"""
    try:
        opportunities = repo.get_all(limit=limit, offset=skip)
        return opportunities
    
    except OracleException as e:
        logger.error("opportunities_list_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list opportunities")


@app.get("/api/opportunities/filter", response_model=List[Opportunity], tags=["Opportunities"])
async def filter_opportunities(
    stage: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    account_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    repo: OpportunityRepository = Depends(get_opportunity_repository)
):
    """Filter opportunities by criteria"""
    try:
        filter_query = OpportunityFilter(
            stage=stage,
            min_amount=min_amount,
            max_amount=max_amount,
            account_id=account_id,
            limit=limit,
            offset=offset
        )
        
        opportunities = repo.filter(filter_query)
        return opportunities
    
    except Exception as e:
        logger.error("filter_opportunities_error", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid filter parameters")


@app.get("/api/opportunities/{opportunity_id}", response_model=Opportunity, tags=["Opportunities"])
async def get_opportunity(
    opportunity_id: int,
    repo: OpportunityRepository = Depends(get_opportunity_repository)
):
    """Get opportunity by ID"""
    try:
        opportunity = repo.get_by_id(opportunity_id)
        
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        return opportunity
    
    except OracleException as e:
        logger.error("get_opportunity_error", opportunity_id=opportunity_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get opportunity")


@app.post("/api/opportunities", response_model=Opportunity, status_code=201, tags=["Opportunities"])
async def create_opportunity(
    opportunity: OpportunityCreate,
    repo: OpportunityRepository = Depends(get_opportunity_repository),
    user: str = Depends(get_current_user)
):
    """Create new opportunity"""
    try:
        created = repo.create(opportunity, created_by=user)
        logger.info("opportunity_created", opportunity_id=created.id, user=user)
        return created
    
    except OracleException as e:
        logger.error("create_opportunity_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create opportunity")


@app.post("/api/opportunities/batch", response_model=BatchOperationResult, tags=["Opportunities"])
async def batch_create_opportunities(
    batch: BatchOpportunityCreate,
    repo: OpportunityRepository = Depends(get_opportunity_repository),
    user: str = Depends(get_current_user)
):
    """Create multiple opportunities in one operation"""
    try:
        batch.created_by = user
        result = repo.batch_create(batch)
        logger.info("batch_opportunity_created", successful=result.successful, failed=result.failed)
        return result
    
    except OracleException as e:
        logger.error("batch_create_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create batch opportunities")


@app.put("/api/opportunities/{opportunity_id}", response_model=bool, tags=["Opportunities"])
async def update_opportunity(
    opportunity_id: int,
    update: OpportunityUpdate,
    repo: OpportunityRepository = Depends(get_opportunity_repository),
    user: str = Depends(get_current_user)
):
    """Update opportunity"""
    try:
        success = repo.update(opportunity_id, update, modified_by=user)
        
        if not success:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        logger.info("opportunity_updated", opportunity_id=opportunity_id, user=user)
        return success
    
    except OracleException as e:
        logger.error("update_opportunity_error", opportunity_id=opportunity_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update opportunity")


# Report Endpoints
@app.get("/api/reports/opportunities-summary", response_model=OpportunitySummary, tags=["Reports"])
async def get_opportunity_summary(
    repo: OpportunityRepository = Depends(get_opportunity_repository)
):
    """Get opportunity pipeline summary"""
    try:
        summary = repo.get_summary()
        return summary
    
    except OracleException as e:
        logger.error("summary_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate summary")


@app.get("/api/reports/account/{account_id}/opportunities", response_model=List[Opportunity], tags=["Reports"])
async def get_account_opportunities(
    account_id: int,
    repo: OpportunityRepository = Depends(get_opportunity_repository)
):
    """Get all opportunities for an account"""
    try:
        opportunities = repo.get_by_account(account_id)
        return opportunities
    
    except OracleException as e:
        logger.error("account_opportunities_error", account_id=account_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get account opportunities")


# Error Handlers
@app.exception_handler(OracleException)
async def oracle_exception_handler(request, exc):
    """Handle Oracle exceptions"""
    logger.error("oracle_exception", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error("unhandled_exception", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    
    # For local testing
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
