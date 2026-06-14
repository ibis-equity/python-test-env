"""
Oracle Data Models and Schemas

Senior-level Pydantic models with validation, serialization, and documentation
Includes Oracle table definitions and mapping
"""

from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
import json


# Enums for opportunity stages and account types
class OpportunityStage(str, Enum):
    """Sales opportunity stages"""
    QUALIFICATION = "Qualification"
    PROPOSAL = "Proposal"
    NEGOTIATION = "Negotiation"
    CLOSED_WON = "Closed Won"
    CLOSED_LOST = "Closed Lost"


class AccountType(str, Enum):
    """Account types"""
    CUSTOMER = "Customer"
    PROSPECT = "Prospect"
    PARTNER = "Partner"


class RecordStatus(str, Enum):
    """Record status"""
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    ARCHIVED = "Archived"


# Base models for Oracle operations
class OracleBaseModel(BaseModel):
    """Base model with Oracle-specific configurations"""
    
    class Config:
        # Allow population by field name
        allow_population_by_field_name = True
        # Validate on assignment
        validate_assignment = True
        # Use enum values
        use_enum_values = True
        # JSON schema extra
        json_schema_extra = {
            "example": "See specific model"
        }


# Account Models
class AccountBase(OracleBaseModel):
    """Account base model"""
    name: str = Field(..., min_length=1, max_length=255, description="Account name")
    industry: str = Field(..., max_length=100, description="Industry type")
    account_type: AccountType = Field(default=AccountType.PROSPECT, description="Account type")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    website: Optional[str] = Field(None, max_length=500, description="Website URL")
    employee_count: Optional[int] = Field(None, ge=0, description="Number of employees")
    annual_revenue: Optional[float] = Field(None, ge=0, description="Annual revenue in USD")
    status: RecordStatus = Field(default=RecordStatus.ACTIVE, description="Record status")
    
    @validator('annual_revenue')
    def validate_revenue(cls, v):
        """Validate revenue is reasonable"""
        if v is not None and v > 1_000_000_000_000:  # 1 trillion
            raise ValueError('Revenue exceeds reasonable limit')
        return v


class Account(AccountBase):
    """Account with database fields"""
    id: int = Field(..., description="Account ID")
    created_date: datetime = Field(..., description="Creation timestamp")
    modified_date: Optional[datetime] = Field(None, description="Last modification timestamp")
    created_by: str = Field(..., max_length=100, description="Created by user")
    modified_by: Optional[str] = Field(None, max_length=100, description="Modified by user")


class AccountCreate(AccountBase):
    """Account creation request"""
    pass


class AccountUpdate(OracleBaseModel):
    """Account update request (all fields optional)"""
    name: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    account_type: Optional[AccountType] = None
    phone: Optional[str] = Field(None, max_length=20)
    website: Optional[str] = Field(None, max_length=500)
    employee_count: Optional[int] = Field(None, ge=0)
    annual_revenue: Optional[float] = Field(None, ge=0)
    status: Optional[RecordStatus] = None


# Contact Models
class ContactBase(OracleBaseModel):
    """Contact base model"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    title: Optional[str] = Field(None, max_length=100, description="Job title")
    account_id: int = Field(..., gt=0, description="Associated account ID")
    status: RecordStatus = Field(default=RecordStatus.ACTIVE)
    
    @validator('email')
    def validate_email(cls, v):
        """Simple email validation"""
        if '@' not in v or '.' not in v:
            raise ValueError('Invalid email format')
        return v.lower()


class Contact(ContactBase):
    """Contact with database fields"""
    id: int
    created_date: datetime
    modified_date: Optional[datetime] = None
    created_by: str
    modified_by: Optional[str] = None


class ContactCreate(ContactBase):
    """Contact creation request"""
    pass


class ContactUpdate(OracleBaseModel):
    """Contact update request"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    title: Optional[str] = Field(None, max_length=100)
    status: Optional[RecordStatus] = None


# Opportunity Models
class OpportunityBase(OracleBaseModel):
    """Opportunity base model"""
    name: str = Field(..., min_length=1, max_length=255, description="Deal name")
    account_id: int = Field(..., gt=0, description="Associated account ID")
    amount: float = Field(..., gt=0, description="Deal amount in USD")
    currency: str = Field(default="USD", max_length=3)
    stage: OpportunityStage = Field(..., description="Deal stage")
    probability: int = Field(..., ge=0, le=100, description="Win probability 0-100")
    close_date: date = Field(..., description="Expected close date")
    description: Optional[str] = Field(None, max_length=4000)
    status: RecordStatus = Field(default=RecordStatus.ACTIVE)
    
    @validator('close_date')
    def validate_close_date(cls, v):
        """Close date should be in future"""
        if v < date.today():
            raise ValueError('Close date must be in the future')
        return v
    
    @validator('probability')
    def validate_probability(cls, v, values):
        """Probability should match stage"""
        stage = values.get('stage')
        if stage == OpportunityStage.QUALIFICATION and v > 50:
            raise ValueError('Qualification stage should have <50% probability')
        elif stage == OpportunityStage.CLOSED_WON and v != 100:
            raise ValueError('Closed Won should have 100% probability')
        elif stage == OpportunityStage.CLOSED_LOST and v != 0:
            raise ValueError('Closed Lost should have 0% probability')
        return v


class Opportunity(OpportunityBase):
    """Opportunity with database fields"""
    id: int
    primary_contact_id: Optional[int] = None
    created_date: datetime
    modified_date: Optional[datetime] = None
    created_by: str
    modified_by: Optional[str] = None
    fiscal_quarter: Optional[str] = Field(None, max_length=10)
    forecast_category: Optional[str] = Field(None, max_length=50)


class OpportunityCreate(OpportunityBase):
    """Opportunity creation request"""
    pass


class OpportunityUpdate(OracleBaseModel):
    """Opportunity update request"""
    name: Optional[str] = Field(None, max_length=255)
    amount: Optional[float] = Field(None, gt=0)
    stage: Optional[OpportunityStage] = None
    probability: Optional[int] = Field(None, ge=0, le=100)
    close_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=4000)
    status: Optional[RecordStatus] = None


class OpportunitySummary(OracleBaseModel):
    """Aggregated opportunity summary"""
    total_opportunities: int = Field(..., ge=0)
    total_value: float = Field(..., ge=0, description="Total opportunity value")
    by_stage: dict = Field(default_factory=dict, description="Count and value by stage")
    by_account: dict = Field(default_factory=dict, description="Top accounts by value")
    average_deal_size: float = Field(default=0)
    win_probability_weighted: float = Field(default=0, ge=0, le=100)


# Activity/Audit Models
class Activity(OracleBaseModel):
    """Activity audit log"""
    id: int
    entity_type: str = Field(..., max_length=50, description="Entity type (Account, Contact, etc)")
    entity_id: int = Field(..., description="Entity ID")
    activity_type: str = Field(..., max_length=50, description="Create, Update, Delete")
    changes: Optional[dict] = Field(None, description="Field changes as JSON")
    created_by: str = Field(..., max_length=100)
    created_date: datetime


class ActivityCreate(OracleBaseModel):
    """Activity creation"""
    entity_type: str = Field(..., max_length=50)
    entity_id: int
    activity_type: str = Field(..., max_length=50)
    changes: Optional[dict] = None
    created_by: str = Field(..., max_length=100)


# Batch Operation Models
class BatchOpportunityCreate(OracleBaseModel):
    """Batch create opportunities"""
    opportunities: List[OpportunityCreate] = Field(..., min_items=1, max_items=1000)
    created_by: str = Field(..., max_length=100)


class BatchOperationResult(OracleBaseModel):
    """Result of batch operation"""
    total: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Items created/updated successfully")
    failed: int = Field(..., description="Failed items")
    errors: List[dict] = Field(default_factory=list, description="Error details")


# Report/Query Models
class OpportunityFilter(OracleBaseModel):
    """Filter for opportunity queries"""
    stage: Optional[OpportunityStage] = None
    min_amount: Optional[float] = Field(None, gt=0)
    max_amount: Optional[float] = Field(None, gt=0)
    min_probability: Optional[int] = Field(None, ge=0, le=100)
    max_probability: Optional[int] = Field(None, ge=0, le=100)
    account_id: Optional[int] = None
    status: Optional[RecordStatus] = None
    close_date_from: Optional[date] = None
    close_date_to: Optional[date] = None
    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class QueryResult(OracleBaseModel):
    """Generic query result"""
    total_count: int = Field(..., description="Total records matching query")
    limit: int = Field(..., description="Limit applied")
    offset: int = Field(..., description="Offset applied")
    records: List[dict] = Field(default_factory=list, description="Retrieved records")


# Oracle Table Definitions (for reference and DDL generation)
class OracleTableDefinition:
    """Oracle table DDL definitions"""
    
    ACCOUNTS_TABLE = """
    CREATE TABLE ACCOUNTS (
        ID NUMBER PRIMARY KEY,
        NAME VARCHAR2(255) NOT NULL,
        INDUSTRY VARCHAR2(100),
        ACCOUNT_TYPE VARCHAR2(50) DEFAULT 'Prospect',
        PHONE VARCHAR2(20),
        WEBSITE VARCHAR2(500),
        EMPLOYEE_COUNT NUMBER,
        ANNUAL_REVENUE NUMBER(15,2),
        STATUS VARCHAR2(50) DEFAULT 'Active',
        CREATED_DATE TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
        MODIFIED_DATE TIMESTAMP,
        CREATED_BY VARCHAR2(100) NOT NULL,
        MODIFIED_BY VARCHAR2(100)
    );
    
    CREATE SEQUENCE ACCOUNTS_SEQ START WITH 1 INCREMENT BY 1;
    CREATE INDEX IDX_ACCOUNTS_STATUS ON ACCOUNTS(STATUS);
    CREATE INDEX IDX_ACCOUNTS_TYPE ON ACCOUNTS(ACCOUNT_TYPE);
    """
    
    CONTACTS_TABLE = """
    CREATE TABLE CONTACTS (
        ID NUMBER PRIMARY KEY,
        FIRST_NAME VARCHAR2(100) NOT NULL,
        LAST_NAME VARCHAR2(100) NOT NULL,
        EMAIL VARCHAR2(255) NOT NULL,
        PHONE VARCHAR2(20),
        TITLE VARCHAR2(100),
        ACCOUNT_ID NUMBER NOT NULL,
        STATUS VARCHAR2(50) DEFAULT 'Active',
        CREATED_DATE TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
        MODIFIED_DATE TIMESTAMP,
        CREATED_BY VARCHAR2(100) NOT NULL,
        MODIFIED_BY VARCHAR2(100),
        CONSTRAINT FK_CONTACTS_ACCOUNTS FOREIGN KEY (ACCOUNT_ID) REFERENCES ACCOUNTS(ID)
    );
    
    CREATE SEQUENCE CONTACTS_SEQ START WITH 1 INCREMENT BY 1;
    CREATE INDEX IDX_CONTACTS_ACCOUNT ON CONTACTS(ACCOUNT_ID);
    CREATE INDEX IDX_CONTACTS_EMAIL ON CONTACTS(EMAIL);
    """
    
    OPPORTUNITIES_TABLE = """
    CREATE TABLE OPPORTUNITIES (
        ID NUMBER PRIMARY KEY,
        NAME VARCHAR2(255) NOT NULL,
        ACCOUNT_ID NUMBER NOT NULL,
        AMOUNT NUMBER(15,2) NOT NULL,
        CURRENCY VARCHAR2(3) DEFAULT 'USD',
        STAGE VARCHAR2(50) NOT NULL,
        PROBABILITY NUMBER(3,0) DEFAULT 50,
        CLOSE_DATE DATE NOT NULL,
        DESCRIPTION VARCHAR2(4000),
        PRIMARY_CONTACT_ID NUMBER,
        STATUS VARCHAR2(50) DEFAULT 'Active',
        FISCAL_QUARTER VARCHAR2(10),
        FORECAST_CATEGORY VARCHAR2(50),
        CREATED_DATE TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
        MODIFIED_DATE TIMESTAMP,
        CREATED_BY VARCHAR2(100) NOT NULL,
        MODIFIED_BY VARCHAR2(100),
        CONSTRAINT FK_OPPS_ACCOUNTS FOREIGN KEY (ACCOUNT_ID) REFERENCES ACCOUNTS(ID),
        CONSTRAINT FK_OPPS_CONTACTS FOREIGN KEY (PRIMARY_CONTACT_ID) REFERENCES CONTACTS(ID)
    );
    
    CREATE SEQUENCE OPPORTUNITIES_SEQ START WITH 1 INCREMENT BY 1;
    CREATE INDEX IDX_OPPS_ACCOUNT ON OPPORTUNITIES(ACCOUNT_ID);
    CREATE INDEX IDX_OPPS_STAGE ON OPPORTUNITIES(STAGE);
    CREATE INDEX IDX_OPPS_CLOSE_DATE ON OPPORTUNITIES(CLOSE_DATE);
    """
    
    ACTIVITIES_TABLE = """
    CREATE TABLE ACTIVITIES (
        ID NUMBER PRIMARY KEY,
        ENTITY_TYPE VARCHAR2(50) NOT NULL,
        ENTITY_ID NUMBER NOT NULL,
        ACTIVITY_TYPE VARCHAR2(50) NOT NULL,
        CHANGES CLOB,
        CREATED_BY VARCHAR2(100) NOT NULL,
        CREATED_DATE TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
    );
    
    CREATE SEQUENCE ACTIVITIES_SEQ START WITH 1 INCREMENT BY 1;
    CREATE INDEX IDX_ACTIVITIES_ENTITY ON ACTIVITIES(ENTITY_TYPE, ENTITY_ID);
    CREATE INDEX IDX_ACTIVITIES_DATE ON ACTIVITIES(CREATED_DATE);
    """


if __name__ == "__main__":
    # Example usage
    print("Oracle Data Models - Senior-Level Patterns")
    print("=" * 60)
    
    # Example 1: Create account
    account = AccountCreate(
        name="Acme Corporation",
        industry="Technology",
        account_type=AccountType.PROSPECT,
        employee_count=500,
        annual_revenue=50_000_000
    )
    print("\n1. Account Creation:")
    print(account.json(indent=2))
    
    # Example 2: Create opportunity
    opportunity = OpportunityCreate(
        name="Enterprise License Deal",
        account_id=1,
        amount=250_000,
        stage=OpportunityStage.PROPOSAL,
        probability=75,
        close_date=date(2026, 3, 31),
        description="Annual enterprise license for 500+ employees"
    )
    print("\n2. Opportunity Creation:")
    print(opportunity.json(indent=2))
    
    # Example 3: Filter opportunities
    filter_query = OpportunityFilter(
        stage=OpportunityStage.PROPOSAL,
        min_amount=100_000,
        min_probability=50,
        limit=50
    )
    print("\n3. Opportunity Filter:")
    print(filter_query.json(indent=2))
    
    # Example 4: Table definitions
    print("\n4. Oracle Table Definitions:")
    print(f"Accounts Table:\n{OracleTableDefinition.ACCOUNTS_TABLE}")
    
    print("\n" + "=" * 60)
    print("Models are ready for FastAPI endpoints and Oracle storage")
