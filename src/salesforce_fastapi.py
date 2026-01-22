from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Optional, List

from salesforce_api import (
    SalesforceClient,
    SalesforceAccount,
    SalesforceContact,
    SalesforceOpportunity,
    SalesforceApiResponse,
    SalesforceQueryResponse,
    get_salesforce_client,
    get_accounts_by_industry,
    get_contacts_by_account,
    get_opportunities_by_stage,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global Salesforce client
sf_client: Optional[SalesforceClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for app startup and shutdown."""
    global sf_client
    try:
        logger.info("Initializing Salesforce client...")
        sf_client = await get_salesforce_client()
        logger.info("Salesforce client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Salesforce client: {str(e)}")
    yield
    logger.info("Shutting down Salesforce integration")


# Initialize FastAPI app
app = FastAPI(
    title="Salesforce Integration API",
    description="""
A comprehensive Salesforce API integration built with FastAPI.

## Features
- OAuth 2.0 authentication with Salesforce
- CRUD operations for Accounts, Contacts, and Opportunities
- SOQL query support
- Async/await for high performance
- Azure and AWS integration ready

## Authentication
Uses Salesforce OAuth 2.0 (configured via environment variables)

## Available Operations
- Create, Read, Update, Delete (CRUD) for key Salesforce objects
- Advanced SOQL queries
- Industry and stage-based filtering
    """,
    version="1.0.0",
    lifespan=lifespan,
)


# ==================== Health & Status Endpoints ====================

@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """Check API health and Salesforce connection status."""
    return JSONResponse(
        {
            "status": "healthy",
            "version": "1.0.0",
            "salesforce_connected": sf_client is not None and sf_client.access_token is not None,
        }
    )


# ==================== Account Endpoints ====================

@app.post("/accounts", response_model=SalesforceApiResponse, tags=["Accounts"])
async def create_account(account: SalesforceAccount) -> SalesforceApiResponse:
    """Create a new Salesforce Account."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.create_account(account)


@app.get("/accounts/{account_id}", response_model=SalesforceApiResponse, tags=["Accounts"])
async def get_account(account_id: str) -> SalesforceApiResponse:
    """Get a specific account by ID."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.get_account(account_id)


@app.patch("/accounts/{account_id}", response_model=SalesforceApiResponse, tags=["Accounts"])
async def update_account(
    account_id: str, account: SalesforceAccount
) -> SalesforceApiResponse:
    """Update a Salesforce Account."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.update_account(account_id, account)


@app.delete("/accounts/{account_id}", response_model=SalesforceApiResponse, tags=["Accounts"])
async def delete_account(account_id: str) -> SalesforceApiResponse:
    """Delete a Salesforce Account."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.delete_account(account_id)


@app.get("/accounts/search/by-industry", tags=["Accounts"])
async def search_accounts_by_industry(industry: str = Query(..., description="Industry name")) -> JSONResponse:
    """Search accounts by industry."""
    records = await get_accounts_by_industry(industry)
    if records is None:
        raise HTTPException(status_code=500, detail="Failed to search accounts")
    return JSONResponse({"total": len(records), "records": records})


# ==================== Contact Endpoints ====================

@app.post("/contacts", response_model=SalesforceApiResponse, tags=["Contacts"])
async def create_contact(contact: SalesforceContact) -> SalesforceApiResponse:
    """Create a new Salesforce Contact."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.create_contact(contact)


@app.get("/contacts/{contact_id}", response_model=SalesforceApiResponse, tags=["Contacts"])
async def get_contact(contact_id: str) -> SalesforceApiResponse:
    """Get a specific contact by ID."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.get_contact(contact_id)


@app.patch("/contacts/{contact_id}", response_model=SalesforceApiResponse, tags=["Contacts"])
async def update_contact(
    contact_id: str, contact: SalesforceContact
) -> SalesforceApiResponse:
    """Update a Salesforce Contact."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.update_contact(contact_id, contact)


@app.delete("/contacts/{contact_id}", response_model=SalesforceApiResponse, tags=["Contacts"])
async def delete_contact(contact_id: str) -> SalesforceApiResponse:
    """Delete a Salesforce Contact."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.delete_contact(contact_id)


@app.get("/contacts/account/{account_id}", tags=["Contacts"])
async def get_account_contacts(account_id: str) -> JSONResponse:
    """Get all contacts for a specific account."""
    records = await get_contacts_by_account(account_id)
    if records is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve contacts")
    return JSONResponse({"total": len(records), "records": records})


# ==================== Opportunity Endpoints ====================

@app.post("/opportunities", response_model=SalesforceApiResponse, tags=["Opportunities"])
async def create_opportunity(
    opportunity: SalesforceOpportunity,
) -> SalesforceApiResponse:
    """Create a new Salesforce Opportunity."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.create_opportunity(opportunity)


@app.get("/opportunities/{opportunity_id}", response_model=SalesforceApiResponse, tags=["Opportunities"])
async def get_opportunity(opportunity_id: str) -> SalesforceApiResponse:
    """Get a specific opportunity by ID."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.get_opportunity(opportunity_id)


@app.patch("/opportunities/{opportunity_id}", response_model=SalesforceApiResponse, tags=["Opportunities"])
async def update_opportunity(
    opportunity_id: str, opportunity: SalesforceOpportunity
) -> SalesforceApiResponse:
    """Update a Salesforce Opportunity."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.update_opportunity(opportunity_id, opportunity)


@app.delete("/opportunities/{opportunity_id}", response_model=SalesforceApiResponse, tags=["Opportunities"])
async def delete_opportunity(opportunity_id: str) -> SalesforceApiResponse:
    """Delete a Salesforce Opportunity."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    return await sf_client.delete_opportunity(opportunity_id)


@app.get("/opportunities/search/by-stage", tags=["Opportunities"])
async def search_opportunities_by_stage(stage: str = Query(..., description="Sales stage")) -> JSONResponse:
    """Search opportunities by sales stage."""
    records = await get_opportunities_by_stage(stage)
    if records is None:
        raise HTTPException(status_code=500, detail="Failed to search opportunities")
    return JSONResponse({"total": len(records), "records": records})


# ==================== Query Endpoints ====================

@app.post("/query", response_model=SalesforceQueryResponse, tags=["Advanced"])
async def execute_soql(soql: str = Body(..., description="SOQL query string")) -> SalesforceQueryResponse:
    """Execute a SOQL (Salesforce Object Query Language) query."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    try:
        return await sf_client.query(soql)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Query failed: {str(e)}")


# ==================== Batch Operations ====================

@app.post("/batch/accounts", response_model=List[SalesforceApiResponse], tags=["Batch Operations"])
async def create_accounts_batch(accounts: List[SalesforceAccount]) -> List[SalesforceApiResponse]:
    """Create multiple accounts in batch."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    results = []
    for account in accounts:
        result = await sf_client.create_account(account)
        results.append(result)
    return results


@app.post("/batch/contacts", response_model=List[SalesforceApiResponse], tags=["Batch Operations"])
async def create_contacts_batch(contacts: List[SalesforceContact]) -> List[SalesforceApiResponse]:
    """Create multiple contacts in batch."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    results = []
    for contact in contacts:
        result = await sf_client.create_contact(contact)
        results.append(result)
    return results


@app.post("/batch/opportunities", response_model=List[SalesforceApiResponse], tags=["Batch Operations"])
async def create_opportunities_batch(
    opportunities: List[SalesforceOpportunity],
) -> List[SalesforceApiResponse]:
    """Create multiple opportunities in batch."""
    if not sf_client:
        raise HTTPException(status_code=503, detail="Salesforce client not initialized")
    results = []
    for opportunity in opportunities:
        result = await sf_client.create_opportunity(opportunity)
        results.append(result)
    return results


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
