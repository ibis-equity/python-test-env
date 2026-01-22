import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from salesforce_api import (
    SalesforceClient,
    SalesforceAccount,
    SalesforceContact,
    SalesforceOpportunity,
    SalesforceApiResponse,
    get_accounts_by_industry,
    get_contacts_by_account,
    get_opportunities_by_stage,
)


@pytest.fixture
def salesforce_client():
    """Create a mock Salesforce client for testing."""
    client = SalesforceClient(
        instance_url="https://test.salesforce.com",
        access_token="mock_token_12345",
    )
    return client


@pytest.mark.asyncio
async def test_authenticate_success():
    """Test successful Salesforce authentication."""
    client = SalesforceClient()

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_token_12345",
            "token_type": "Bearer",
        }
        mock_response.raise_for_status = MagicMock()

        mock_post.return_value.__aenter__.return_value = mock_response

        result = await client.authenticate()

        assert result is True
        assert client.access_token == "new_token_12345"


@pytest.mark.asyncio
async def test_create_account_success(salesforce_client):
    """Test successful account creation."""
    account = SalesforceAccount(
        Name="Test Company",
        Phone="555-0100",
        Website="https://testcompany.com",
        Industry="Technology",
        BillingCity="San Francisco",
        BillingCountry="USA",
    )

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "001xx000003DHP1",
            "success": True,
            "created": True,
        }
        mock_response.raise_for_status = MagicMock()

        mock_post.return_value.__aenter__.return_value = mock_response

        result = await salesforce_client.create_account(account)

        assert result.success is True
        assert result.record_id == "001xx000003DHP1"


@pytest.mark.asyncio
async def test_create_contact_success(salesforce_client):
    """Test successful contact creation."""
    contact = SalesforceContact(
        FirstName="John",
        LastName="Doe",
        Email="john.doe@example.com",
        Phone="555-0101",
        AccountId="001xx000003DHP1",
    )

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "003xx000004TMZ1",
            "success": True,
            "created": True,
        }
        mock_response.raise_for_status = MagicMock()

        mock_post.return_value.__aenter__.return_value = mock_response

        result = await salesforce_client.create_contact(contact)

        assert result.success is True
        assert result.record_id == "003xx000004TMZ1"


@pytest.mark.asyncio
async def test_create_opportunity_success(salesforce_client):
    """Test successful opportunity creation."""
    opportunity = SalesforceOpportunity(
        Name="Enterprise Deal",
        Amount=250000.0,
        StageName="Negotiation/Review",
        CloseDate="2024-12-31",
        AccountId="001xx000003DHP1",
    )

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "006xx000007MZF1",
            "success": True,
            "created": True,
        }
        mock_response.raise_for_status = MagicMock()

        mock_post.return_value.__aenter__.return_value = mock_response

        result = await salesforce_client.create_opportunity(opportunity)

        assert result.success is True
        assert result.record_id == "006xx000007MZF1"


@pytest.mark.asyncio
async def test_get_account_success(salesforce_client):
    """Test successful account retrieval."""
    account_id = "001xx000003DHP1"

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Id": account_id,
            "Name": "Test Company",
            "Phone": "555-0100",
            "Website": "https://testcompany.com",
        }
        mock_response.raise_for_status = MagicMock()

        mock_get.return_value.__aenter__.return_value = mock_response

        result = await salesforce_client.get_account(account_id)

        assert result.success is True
        assert result.data["Name"] == "Test Company"


@pytest.mark.asyncio
async def test_update_account_success(salesforce_client):
    """Test successful account update."""
    account_id = "001xx000003DHP1"
    account = SalesforceAccount(Name="Updated Company")

    with patch("httpx.AsyncClient.patch") as mock_patch:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_patch.return_value.__aenter__.return_value = mock_response

        result = await salesforce_client.update_account(account_id, account)

        assert result.success is True
        assert result.record_id == account_id


@pytest.mark.asyncio
async def test_delete_account_success(salesforce_client):
    """Test successful account deletion."""
    account_id = "001xx000003DHP1"

    with patch("httpx.AsyncClient.delete") as mock_delete:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_delete.return_value.__aenter__.return_value = mock_response

        result = await salesforce_client.delete_account(account_id)

        assert result.success is True
        assert result.record_id == account_id


@pytest.mark.asyncio
async def test_query_success(salesforce_client):
    """Test successful SOQL query."""
    soql = "SELECT Id, Name FROM Account WHERE Industry = 'Technology'"

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "totalSize": 2,
            "done": True,
            "records": [
                {"Id": "001xx000003DHP1", "Name": "Test Company 1"},
                {"Id": "001xx000003DHP2", "Name": "Test Company 2"},
            ],
        }
        mock_response.raise_for_status = MagicMock()

        mock_get.return_value.__aenter__.return_value = mock_response

        result = await salesforce_client.query(soql)

        assert result.totalSize == 2
        assert result.done is True
        assert len(result.records) == 2


@pytest.mark.asyncio
async def test_get_accounts_by_industry():
    """Test querying accounts by industry."""
    with patch("salesforce_api.get_salesforce_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.query.return_value.records = [
            {"Id": "001xx000003DHP1", "Name": "Tech Corp", "Industry": "Technology"}
        ]

        mock_get_client.return_value = mock_client

        result = await get_accounts_by_industry("Technology")

        assert len(result) == 1
        assert result[0]["Name"] == "Tech Corp"


@pytest.mark.asyncio
async def test_get_contacts_by_account():
    """Test querying contacts for an account."""
    with patch("salesforce_api.get_salesforce_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.query.return_value.records = [
            {
                "Id": "003xx000004TMZ1",
                "FirstName": "John",
                "LastName": "Doe",
                "Email": "john@example.com",
            }
        ]

        mock_get_client.return_value = mock_client

        result = await get_contacts_by_account("001xx000003DHP1")

        assert len(result) == 1
        assert result[0]["FirstName"] == "John"


@pytest.mark.asyncio
async def test_get_opportunities_by_stage():
    """Test querying opportunities by stage."""
    with patch("salesforce_api.get_salesforce_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.query.return_value.records = [
            {"Id": "006xx000007MZF1", "Name": "Enterprise Deal", "StageName": "Closed Won"}
        ]

        mock_get_client.return_value = mock_client

        result = await get_opportunities_by_stage("Closed Won")

        assert len(result) == 1
        assert result[0]["Name"] == "Enterprise Deal"


@pytest.mark.asyncio
async def test_create_account_failure(salesforce_client):
    """Test account creation failure."""
    account = SalesforceAccount(Name="Test Company")

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = Exception("Connection error")

        result = await salesforce_client.create_account(account)

        assert result.success is False
        assert result.error is not None


@pytest.mark.asyncio
async def test_get_headers(salesforce_client):
    """Test get_headers method."""
    headers = salesforce_client._get_headers()

    assert "Authorization" in headers
    assert headers["Authorization"] == "Bearer mock_token_12345"
    assert headers["Content-Type"] == "application/json"


class TestSalesforceModels:
    """Test Pydantic models for Salesforce objects."""

    def test_account_model_creation(self):
        """Test SalesforceAccount model."""
        account = SalesforceAccount(
            Name="Test Company",
            Phone="555-0100",
        )

        assert account.Name == "Test Company"
        assert account.Phone == "555-0100"
        assert account.Id is None

    def test_contact_model_creation(self):
        """Test SalesforceContact model."""
        contact = SalesforceContact(
            FirstName="John",
            LastName="Doe",
            Email="john@example.com",
        )

        assert contact.FirstName == "John"
        assert contact.LastName == "Doe"
        assert contact.Email == "john@example.com"

    def test_opportunity_model_creation(self):
        """Test SalesforceOpportunity model."""
        opportunity = SalesforceOpportunity(
            Name="Test Deal",
            Amount=100000.0,
            AccountId="001xx000003DHP1",
        )

        assert opportunity.Name == "Test Deal"
        assert opportunity.Amount == 100000.0
        assert opportunity.StageName == "Prospecting"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
