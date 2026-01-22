import os
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Pydantic Models ====================

class SalesforceAuthRequest(BaseModel):
    """Salesforce authentication credentials."""
    client_id: str = Field(..., description="Salesforce OAuth client ID")
    client_secret: str = Field(..., description="Salesforce OAuth client secret")
    username: str = Field(..., description="Salesforce username")
    password: str = Field(..., description="Salesforce password")
    security_token: str = Field(default="", description="Salesforce security token")


class SalesforceAccount(BaseModel):
    """Salesforce Account object model."""
    Id: Optional[str] = Field(None, description="Account record ID")
    Name: str = Field(..., description="Account name")
    Phone: Optional[str] = Field(None, description="Phone number")
    Website: Optional[str] = Field(None, description="Website URL")
    Industry: Optional[str] = Field(None, description="Industry type")
    BillingCity: Optional[str] = Field(None, description="Billing city")
    BillingCountry: Optional[str] = Field(None, description="Billing country")


class SalesforceContact(BaseModel):
    """Salesforce Contact object model."""
    Id: Optional[str] = Field(None, description="Contact record ID")
    FirstName: str = Field(..., description="Contact first name")
    LastName: str = Field(..., description="Contact last name")
    Email: Optional[str] = Field(None, description="Email address")
    Phone: Optional[str] = Field(None, description="Phone number")
    AccountId: Optional[str] = Field(None, description="Associated account ID")


class SalesforceOpportunity(BaseModel):
    """Salesforce Opportunity object model."""
    Id: Optional[str] = Field(None, description="Opportunity record ID")
    Name: str = Field(..., description="Opportunity name")
    Amount: Optional[float] = Field(None, description="Opportunity amount")
    StageName: str = Field("Prospecting", description="Sales stage")
    CloseDate: Optional[str] = Field(None, description="Expected close date")
    AccountId: str = Field(..., description="Associated account ID")


class SalesforceQueryResponse(BaseModel):
    """Response model for Salesforce queries."""
    totalSize: int = Field(..., description="Total number of records")
    done: bool = Field(..., description="Whether query is complete")
    records: List[Dict[str, Any]] = Field(..., description="Query results")


class SalesforceApiResponse(BaseModel):
    """Generic Salesforce API response."""
    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    record_id: Optional[str] = Field(None, description="Created/updated record ID")


# ==================== Salesforce API Client ====================

class SalesforceClient:
    """Salesforce API client for authentication and CRUD operations."""

    def __init__(
        self,
        instance_url: Optional[str] = None,
        access_token: Optional[str] = None,
    ):
        """
        Initialize Salesforce client.

        Args:
            instance_url: Salesforce instance URL (e.g., https://na1.salesforce.com)
            access_token: OAuth access token
        """
        self.instance_url = instance_url or os.getenv("SALESFORCE_INSTANCE_URL")
        self.access_token = access_token
        self.client_id = os.getenv("SALESFORCE_CLIENT_ID")
        self.client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
        self.username = os.getenv("SALESFORCE_USERNAME")
        self.password = os.getenv("SALESFORCE_PASSWORD")
        self.security_token = os.getenv("SALESFORCE_SECURITY_TOKEN", "")
        self.api_version = "v60.0"

    async def authenticate(self) -> bool:
        """
        Authenticate with Salesforce OAuth 2.0.

        Returns:
            bool: True if authentication successful
        """
        try:
            auth_url = f"{self.instance_url}/services/oauth2/token"
            payload = {
                "grant_type": "password",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "username": self.username,
                "password": f"{self.password}{self.security_token}",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(auth_url, data=payload)
                response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]
            logger.info("Successfully authenticated with Salesforce")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def query(self, soql: str) -> SalesforceQueryResponse:
        """
        Execute SOQL query.

        Args:
            soql: SOQL query string

        Returns:
            SalesforceQueryResponse with query results
        """
        try:
            query_url = f"{self.instance_url}/services/data/{self.api_version}/query"
            params = {"q": soql}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    query_url, headers=self._get_headers(), params=params
                )
                response.raise_for_status()

            return SalesforceQueryResponse(**response.json())

        except httpx.HTTPError as e:
            logger.error(f"Query failed: {str(e)}")
            raise

    async def create_account(self, account: SalesforceAccount) -> SalesforceApiResponse:
        """
        Create a new Salesforce Account.

        Args:
            account: Account data

        Returns:
            SalesforceApiResponse with created account ID
        """
        return await self._create_record("Account", account.model_dump(exclude_none=True))

    async def create_contact(self, contact: SalesforceContact) -> SalesforceApiResponse:
        """
        Create a new Salesforce Contact.

        Args:
            contact: Contact data

        Returns:
            SalesforceApiResponse with created contact ID
        """
        return await self._create_record("Contact", contact.model_dump(exclude_none=True))

    async def create_opportunity(
        self, opportunity: SalesforceOpportunity
    ) -> SalesforceApiResponse:
        """
        Create a new Salesforce Opportunity.

        Args:
            opportunity: Opportunity data

        Returns:
            SalesforceApiResponse with created opportunity ID
        """
        return await self._create_record(
            "Opportunity", opportunity.model_dump(exclude_none=True)
        )

    async def _create_record(self, sobject_type: str, data: Dict[str, Any]) -> SalesforceApiResponse:
        """
        Create a record in Salesforce.

        Args:
            sobject_type: Salesforce object type (Account, Contact, etc.)
            data: Record data

        Returns:
            SalesforceApiResponse with result
        """
        try:
            create_url = (
                f"{self.instance_url}/services/data/{self.api_version}/sobjects/{sobject_type}"
            )

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    create_url, headers=self._get_headers(), json=data
                )
                response.raise_for_status()

            result = response.json()
            return SalesforceApiResponse(
                success=result.get("success", True),
                record_id=result.get("id"),
                data=result,
            )

        except httpx.HTTPError as e:
            logger.error(f"Create record failed: {str(e)}")
            return SalesforceApiResponse(
                success=False, error=str(e), data={"status": response.status_code}
            )

    async def get_record(self, sobject_type: str, record_id: str) -> SalesforceApiResponse:
        """
        Retrieve a specific Salesforce record.

        Args:
            sobject_type: Salesforce object type (Account, Contact, etc.)
            record_id: Record ID to retrieve

        Returns:
            SalesforceApiResponse with record data
        """
        try:
            get_url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/{sobject_type}/{record_id}"

            async with httpx.AsyncClient() as client:
                response = await client.get(get_url, headers=self._get_headers())
                response.raise_for_status()

            return SalesforceApiResponse(success=True, data=response.json())

        except httpx.HTTPError as e:
            logger.error(f"Get record failed: {str(e)}")
            return SalesforceApiResponse(success=False, error=str(e))

    async def update_record(
        self, sobject_type: str, record_id: str, data: Dict[str, Any]
    ) -> SalesforceApiResponse:
        """
        Update a Salesforce record.

        Args:
            sobject_type: Salesforce object type
            record_id: Record ID to update
            data: Fields to update

        Returns:
            SalesforceApiResponse with update result
        """
        try:
            update_url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/{sobject_type}/{record_id}"

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    update_url, headers=self._get_headers(), json=data
                )
                response.raise_for_status()

            return SalesforceApiResponse(
                success=True, record_id=record_id, data={"status": "updated"}
            )

        except httpx.HTTPError as e:
            logger.error(f"Update record failed: {str(e)}")
            return SalesforceApiResponse(success=False, error=str(e))

    async def delete_record(self, sobject_type: str, record_id: str) -> SalesforceApiResponse:
        """
        Delete a Salesforce record.

        Args:
            sobject_type: Salesforce object type
            record_id: Record ID to delete

        Returns:
            SalesforceApiResponse with delete result
        """
        try:
            delete_url = f"{self.instance_url}/services/data/{self.api_version}/sobjects/{sobject_type}/{record_id}"

            async with httpx.AsyncClient() as client:
                response = await client.delete(delete_url, headers=self._get_headers())
                response.raise_for_status()

            return SalesforceApiResponse(
                success=True, record_id=record_id, data={"status": "deleted"}
            )

        except httpx.HTTPError as e:
            logger.error(f"Delete record failed: {str(e)}")
            return SalesforceApiResponse(success=False, error=str(e))

    async def get_account(self, account_id: str) -> SalesforceApiResponse:
        """Get a specific account by ID."""
        return await self.get_record("Account", account_id)

    async def get_contact(self, contact_id: str) -> SalesforceApiResponse:
        """Get a specific contact by ID."""
        return await self.get_record("Contact", contact_id)

    async def get_opportunity(self, opportunity_id: str) -> SalesforceApiResponse:
        """Get a specific opportunity by ID."""
        return await self.get_record("Opportunity", opportunity_id)

    async def update_account(
        self, account_id: str, account: SalesforceAccount
    ) -> SalesforceApiResponse:
        """Update an account."""
        return await self.update_record(
            "Account", account_id, account.model_dump(exclude_none=True, exclude={"Id"})
        )

    async def update_contact(
        self, contact_id: str, contact: SalesforceContact
    ) -> SalesforceApiResponse:
        """Update a contact."""
        return await self.update_record(
            "Contact", contact_id, contact.model_dump(exclude_none=True, exclude={"Id"})
        )

    async def update_opportunity(
        self, opportunity_id: str, opportunity: SalesforceOpportunity
    ) -> SalesforceApiResponse:
        """Update an opportunity."""
        return await self.update_record(
            "Opportunity", opportunity_id, opportunity.model_dump(exclude_none=True, exclude={"Id"})
        )

    async def delete_account(self, account_id: str) -> SalesforceApiResponse:
        """Delete an account."""
        return await self.delete_record("Account", account_id)

    async def delete_contact(self, contact_id: str) -> SalesforceApiResponse:
        """Delete a contact."""
        return await self.delete_record("Contact", contact_id)

    async def delete_opportunity(self, opportunity_id: str) -> SalesforceApiResponse:
        """Delete an opportunity."""
        return await self.delete_record("Opportunity", opportunity_id)


# ==================== Utility Functions ====================

async def get_salesforce_client() -> SalesforceClient:
    """Factory function to create and authenticate Salesforce client."""
    client = SalesforceClient()
    await client.authenticate()
    return client


async def get_accounts_by_industry(industry: str) -> Optional[List[Dict[str, Any]]]:
    """
    Query all accounts by industry.

    Args:
        industry: Industry name to filter by

    Returns:
        List of accounts or None if error
    """
    try:
        client = await get_salesforce_client()
        soql = f"SELECT Id, Name, Phone, Website, Industry FROM Account WHERE Industry = '{industry}'"
        result = await client.query(soql)
        return result.records
    except Exception as e:
        logger.error(f"Failed to get accounts by industry: {str(e)}")
        return None


async def get_contacts_by_account(account_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Query all contacts for a specific account.

    Args:
        account_id: Account ID to filter by

    Returns:
        List of contacts or None if error
    """
    try:
        client = await get_salesforce_client()
        soql = f"SELECT Id, FirstName, LastName, Email, Phone FROM Contact WHERE AccountId = '{account_id}'"
        result = await client.query(soql)
        return result.records
    except Exception as e:
        logger.error(f"Failed to get contacts: {str(e)}")
        return None


async def get_opportunities_by_stage(stage: str) -> Optional[List[Dict[str, Any]]]:
    """
    Query all opportunities by sales stage.

    Args:
        stage: Sales stage to filter by

    Returns:
        List of opportunities or None if error
    """
    try:
        client = await get_salesforce_client()
        soql = f"SELECT Id, Name, Amount, StageName, CloseDate FROM Opportunity WHERE StageName = '{stage}'"
        result = await client.query(soql)
        return result.records
    except Exception as e:
        logger.error(f"Failed to get opportunities: {str(e)}")
        return None
