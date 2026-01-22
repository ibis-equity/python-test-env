#!/usr/bin/env python3
"""
Test script for Salesforce API
Demonstrates all major functionality of the Salesforce API client
"""

import asyncio
import os
from dotenv import load_dotenv
from salesforce_api import (
    SalesforceClient,
    SalesforceAccount,
    SalesforceContact,
    SalesforceOpportunity,
)

# Load environment variables
load_dotenv()


async def test_authentication():
    """Test Salesforce authentication"""
    print("\n" + "=" * 60)
    print("TEST 1: Authentication")
    print("=" * 60)
    
    client = SalesforceClient()
    success = await client.authenticate()
    
    if success:
        print("✓ Successfully authenticated with Salesforce")
        print(f"  Instance URL: {client.instance_url}")
        print(f"  API Version: {client.api_version}")
        return client
    else:
        print("✗ Authentication failed")
        print("  Check your .env file with Salesforce credentials")
        return None


async def test_create_account(client: SalesforceClient):
    """Test account creation"""
    print("\n" + "=" * 60)
    print("TEST 2: Create Account")
    print("=" * 60)
    
    account = SalesforceAccount(
        Name="Test Corporation",
        Phone="555-0123",
        Website="https://testcorp.example.com",
        Industry="Technology",
        BillingCity="San Francisco",
        BillingCountry="USA"
    )
    
    print(f"Creating account: {account.Name}")
    result = await client.create_account(account)
    
    if result.success:
        print(f"✓ Account created successfully")
        print(f"  Record ID: {result.record_id}")
        return result.record_id
    else:
        print(f"✗ Failed to create account: {result.error}")
        return None


async def test_get_account(client: SalesforceClient, account_id: str):
    """Test retrieving an account"""
    print("\n" + "=" * 60)
    print("TEST 3: Get Account")
    print("=" * 60)
    
    print(f"Retrieving account: {account_id}")
    result = await client.get_account(account_id)
    
    if result.success:
        print("✓ Account retrieved successfully")
        account = result.data
        print(f"  Name: {account.get('Name')}")
        print(f"  Phone: {account.get('Phone')}")
        print(f"  Industry: {account.get('Industry')}")
    else:
        print(f"✗ Failed to retrieve account: {result.error}")


async def test_update_account(client: SalesforceClient, account_id: str):
    """Test updating an account"""
    print("\n" + "=" * 60)
    print("TEST 4: Update Account")
    print("=" * 60)
    
    updated_account = SalesforceAccount(
        Name="Updated Test Corporation",
        Phone="555-9876"
    )
    
    print(f"Updating account: {account_id}")
    result = await client.update_account(account_id, updated_account)
    
    if result.success:
        print("✓ Account updated successfully")
        print(f"  New name: {updated_account.Name}")
    else:
        print(f"✗ Failed to update account: {result.error}")


async def test_create_contact(client: SalesforceClient, account_id: str):
    """Test contact creation"""
    print("\n" + "=" * 60)
    print("TEST 5: Create Contact")
    print("=" * 60)
    
    contact = SalesforceContact(
        FirstName="John",
        LastName="Smith",
        Email="john.smith@example.com",
        Phone="555-5555",
        AccountId=account_id
    )
    
    print(f"Creating contact: {contact.FirstName} {contact.LastName}")
    result = await client.create_contact(contact)
    
    if result.success:
        print("✓ Contact created successfully")
        print(f"  Record ID: {result.record_id}")
        return result.record_id
    else:
        print(f"✗ Failed to create contact: {result.error}")
        return None


async def test_get_contact(client: SalesforceClient, contact_id: str):
    """Test retrieving a contact"""
    print("\n" + "=" * 60)
    print("TEST 6: Get Contact")
    print("=" * 60)
    
    print(f"Retrieving contact: {contact_id}")
    result = await client.get_contact(contact_id)
    
    if result.success:
        print("✓ Contact retrieved successfully")
        contact = result.data
        print(f"  Name: {contact.get('FirstName')} {contact.get('LastName')}")
        print(f"  Email: {contact.get('Email')}")
        print(f"  Phone: {contact.get('Phone')}")
    else:
        print(f"✗ Failed to retrieve contact: {result.error}")


async def test_create_opportunity(client: SalesforceClient, account_id: str):
    """Test opportunity creation"""
    print("\n" + "=" * 60)
    print("TEST 7: Create Opportunity")
    print("=" * 60)
    
    opportunity = SalesforceOpportunity(
        Name="Enterprise Software Deal",
        Amount=250000.0,
        StageName="Proposal/Price Quote",
        CloseDate="2025-12-31",
        AccountId=account_id
    )
    
    print(f"Creating opportunity: {opportunity.Name}")
    result = await client.create_opportunity(opportunity)
    
    if result.success:
        print("✓ Opportunity created successfully")
        print(f"  Record ID: {result.record_id}")
        print(f"  Amount: ${opportunity.Amount:,.2f}")
        print(f"  Close Date: {opportunity.CloseDate}")
        return result.record_id
    else:
        print(f"✗ Failed to create opportunity: {result.error}")
        return None


async def test_query(client: SalesforceClient):
    """Test SOQL query"""
    print("\n" + "=" * 60)
    print("TEST 8: SOQL Query")
    print("=" * 60)
    
    soql = "SELECT Id, Name, Phone FROM Account WHERE Industry = 'Technology' LIMIT 5"
    print(f"Executing query: {soql}")
    
    try:
        result = await client.query(soql)
        print(f"✓ Query executed successfully")
        print(f"  Total records: {result.totalSize}")
        print(f"  Query complete: {result.done}")
        if result.records:
            print(f"  Records returned: {len(result.records)}")
            for i, record in enumerate(result.records[:3], 1):
                print(f"    {i}. {record.get('Name', 'N/A')}")
    except Exception as e:
        print(f"✗ Query failed: {str(e)}")


async def test_delete_contact(client: SalesforceClient, contact_id: str):
    """Test contact deletion"""
    print("\n" + "=" * 60)
    print("TEST 9: Delete Contact")
    print("=" * 60)
    
    print(f"Deleting contact: {contact_id}")
    result = await client.delete_contact(contact_id)
    
    if result.success:
        print("✓ Contact deleted successfully")
    else:
        print(f"✗ Failed to delete contact: {result.error}")


async def test_delete_opportunity(client: SalesforceClient, opportunity_id: str):
    """Test opportunity deletion"""
    print("\n" + "=" * 60)
    print("TEST 10: Delete Opportunity")
    print("=" * 60)
    
    print(f"Deleting opportunity: {opportunity_id}")
    result = await client.delete_opportunity(opportunity_id)
    
    if result.success:
        print("✓ Opportunity deleted successfully")
    else:
        print(f"✗ Failed to delete opportunity: {result.error}")


async def test_delete_account(client: SalesforceClient, account_id: str):
    """Test account deletion"""
    print("\n" + "=" * 60)
    print("TEST 11: Delete Account")
    print("=" * 60)
    
    print(f"Deleting account: {account_id}")
    result = await client.delete_account(account_id)
    
    if result.success:
        print("✓ Account deleted successfully")
    else:
        print(f"✗ Failed to delete account: {result.error}")


async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  SALESFORCE API TEST SUITE".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    # Check for environment variables
    required_vars = [
        "SALESFORCE_INSTANCE_URL",
        "SALESFORCE_CLIENT_ID",
        "SALESFORCE_CLIENT_SECRET",
        "SALESFORCE_USERNAME",
        "SALESFORCE_PASSWORD"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("\n⚠️  Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n✓ Create a .env file with these variables to run tests")
        return
    
    # Run tests
    client = await test_authentication()
    
    if not client:
        return
    
    try:
        # Test CRUD operations
        account_id = await test_create_account(client)
        
        if account_id:
            await test_get_account(client, account_id)
            await test_update_account(client, account_id)
            
            contact_id = await test_create_contact(client, account_id)
            if contact_id:
                await test_get_contact(client, contact_id)
            
            opportunity_id = await test_create_opportunity(client, account_id)
            
            await test_query(client)
            
            # Test deletions
            if contact_id:
                await test_delete_contact(client, contact_id)
            
            if opportunity_id:
                await test_delete_opportunity(client, opportunity_id)
            
            await test_delete_account(client, account_id)
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✓ All tests completed!")
        print("✓ Check above for any failures or errors")
        
    except Exception as e:
        print(f"\n✗ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
