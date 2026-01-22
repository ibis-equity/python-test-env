"""
AWS Lambda function for Salesforce API integration
Provides handlers for various Salesforce operations via Lambda events
"""

import json
import asyncio
import logging
import os
from typing import Dict, Any, Coroutine
from datetime import datetime
from salesforce_api import (
    SalesforceClient,
    SalesforceAccount,
    SalesforceContact,
    SalesforceOpportunity,
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LambdaResponse:
    """Helper class for Lambda response formatting"""

    @staticmethod
    def success(data: Any, status_code: int = 200) -> Dict[str, Any]:
        """Return success response"""
        return {
            "statusCode": status_code,
            "body": json.dumps({
                "success": True,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }

    @staticmethod
    def error(message: str, status_code: int = 400, error_code: str = "ERROR") -> Dict[str, Any]:
        """Return error response"""
        return {
            "statusCode": status_code,
            "body": json.dumps({
                "success": False,
                "error": message,
                "error_code": error_code,
                "timestamp": datetime.utcnow().isoformat()
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }


def run_async(coro: Coroutine) -> Any:
    """Helper to run async functions in Lambda"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


async def get_client() -> SalesforceClient:
    """Get authenticated Salesforce client"""
    client = SalesforceClient()
    success = await client.authenticate()
    if not success:
        raise Exception("Failed to authenticate with Salesforce")
    return client


# ==================== Account Handlers ====================

def create_account_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to create Salesforce account
    
    Event body:
    {
        "Name": "Company Name",
        "Phone": "555-1234",
        "Website": "https://example.com",
        "Industry": "Technology",
        "BillingCity": "San Francisco",
        "BillingCountry": "USA"
    }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        
        account = SalesforceAccount(
            Name=body.get("Name"),
            Phone=body.get("Phone"),
            Website=body.get("Website"),
            Industry=body.get("Industry"),
            BillingCity=body.get("BillingCity"),
            BillingCountry=body.get("BillingCountry")
        )
        
        client = run_async(get_client())
        result = run_async(client.create_account(account))
        
        if result.success:
            logger.info(f"Created account: {result.record_id}")
            return LambdaResponse.success({
                "record_id": result.record_id,
                "account_name": account.Name
            }, 201)
        else:
            logger.error(f"Failed to create account: {result.error}")
            return LambdaResponse.error(result.error or "Failed to create account", 400)
            
    except Exception as e:
        logger.error(f"Error creating account: {str(e)}")
        return LambdaResponse.error(str(e), 500)


def get_account_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to retrieve Salesforce account
    
    Path parameter: account_id
    """
    try:
        account_id = event.get("pathParameters", {}).get("account_id")
        
        if not account_id:
            return LambdaResponse.error("Missing account_id parameter", 400)
        
        client = run_async(get_client())
        result = run_async(client.get_account(account_id))
        
        if result.success:
            logger.info(f"Retrieved account: {account_id}")
            return LambdaResponse.success(result.data)
        else:
            logger.error(f"Failed to get account: {result.error}")
            return LambdaResponse.error(result.error or "Account not found", 404)
            
    except Exception as e:
        logger.error(f"Error getting account: {str(e)}")
        return LambdaResponse.error(str(e), 500)


def update_account_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to update Salesforce account
    
    Path parameter: account_id
    Event body: Updated account fields
    """
    try:
        account_id = event.get("pathParameters", {}).get("account_id")
        body = json.loads(event.get("body", "{}"))
        
        if not account_id:
            return LambdaResponse.error("Missing account_id parameter", 400)
        
        account = SalesforceAccount(
            Name=body.get("Name"),
            Phone=body.get("Phone"),
            Website=body.get("Website"),
            Industry=body.get("Industry"),
            BillingCity=body.get("BillingCity"),
            BillingCountry=body.get("BillingCountry")
        )
        
        client = run_async(get_client())
        result = run_async(client.update_account(account_id, account))
        
        if result.success:
            logger.info(f"Updated account: {account_id}")
            return LambdaResponse.success({
                "record_id": account_id,
                "status": "updated"
            })
        else:
            logger.error(f"Failed to update account: {result.error}")
            return LambdaResponse.error(result.error or "Failed to update account", 400)
            
    except Exception as e:
        logger.error(f"Error updating account: {str(e)}")
        return LambdaResponse.error(str(e), 500)


def delete_account_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to delete Salesforce account
    
    Path parameter: account_id
    """
    try:
        account_id = event.get("pathParameters", {}).get("account_id")
        
        if not account_id:
            return LambdaResponse.error("Missing account_id parameter", 400)
        
        client = run_async(get_client())
        result = run_async(client.delete_account(account_id))
        
        if result.success:
            logger.info(f"Deleted account: {account_id}")
            return LambdaResponse.success({
                "record_id": account_id,
                "status": "deleted"
            })
        else:
            logger.error(f"Failed to delete account: {result.error}")
            return LambdaResponse.error(result.error or "Failed to delete account", 400)
            
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        return LambdaResponse.error(str(e), 500)


# ==================== Contact Handlers ====================

def create_contact_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to create Salesforce contact
    
    Event body:
    {
        "FirstName": "John",
        "LastName": "Doe",
        "Email": "john@example.com",
        "Phone": "555-1234",
        "AccountId": "001xx000003DHP1"
    }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        
        contact = SalesforceContact(
            FirstName=body.get("FirstName"),
            LastName=body.get("LastName"),
            Email=body.get("Email"),
            Phone=body.get("Phone"),
            AccountId=body.get("AccountId")
        )
        
        client = run_async(get_client())
        result = run_async(client.create_contact(contact))
        
        if result.success:
            logger.info(f"Created contact: {result.record_id}")
            return LambdaResponse.success({
                "record_id": result.record_id,
                "contact_name": f"{contact.FirstName} {contact.LastName}"
            }, 201)
        else:
            logger.error(f"Failed to create contact: {result.error}")
            return LambdaResponse.error(result.error or "Failed to create contact", 400)
            
    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}")
        return LambdaResponse.error(str(e), 500)


def get_contact_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to retrieve Salesforce contact
    
    Path parameter: contact_id
    """
    try:
        contact_id = event.get("pathParameters", {}).get("contact_id")
        
        if not contact_id:
            return LambdaResponse.error("Missing contact_id parameter", 400)
        
        client = run_async(get_client())
        result = run_async(client.get_contact(contact_id))
        
        if result.success:
            logger.info(f"Retrieved contact: {contact_id}")
            return LambdaResponse.success(result.data)
        else:
            logger.error(f"Failed to get contact: {result.error}")
            return LambdaResponse.error(result.error or "Contact not found", 404)
            
    except Exception as e:
        logger.error(f"Error getting contact: {str(e)}")
        return LambdaResponse.error(str(e), 500)


def update_contact_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to update Salesforce contact
    
    Path parameter: contact_id
    Event body: Updated contact fields
    """
    try:
        contact_id = event.get("pathParameters", {}).get("contact_id")
        body = json.loads(event.get("body", "{}"))
        
        if not contact_id:
            return LambdaResponse.error("Missing contact_id parameter", 400)
        
        contact = SalesforceContact(
            FirstName=body.get("FirstName"),
            LastName=body.get("LastName"),
            Email=body.get("Email"),
            Phone=body.get("Phone")
        )
        
        client = run_async(get_client())
        result = run_async(client.update_contact(contact_id, contact))
        
        if result.success:
            logger.info(f"Updated contact: {contact_id}")
            return LambdaResponse.success({
                "record_id": contact_id,
                "status": "updated"
            })
        else:
            logger.error(f"Failed to update contact: {result.error}")
            return LambdaResponse.error(result.error or "Failed to update contact", 400)
            
    except Exception as e:
        logger.error(f"Error updating contact: {str(e)}")
        return LambdaResponse.error(str(e), 500)


def delete_contact_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to delete Salesforce contact
    
    Path parameter: contact_id
    """
    try:
        contact_id = event.get("pathParameters", {}).get("contact_id")
        
        if not contact_id:
            return LambdaResponse.error("Missing contact_id parameter", 400)
        
        client = run_async(get_client())
        result = run_async(client.delete_contact(contact_id))
        
        if result.success:
            logger.info(f"Deleted contact: {contact_id}")
            return LambdaResponse.success({
                "record_id": contact_id,
                "status": "deleted"
            })
        else:
            logger.error(f"Failed to delete contact: {result.error}")
            return LambdaResponse.error(result.error or "Failed to delete contact", 400)
            
    except Exception as e:
        logger.error(f"Error deleting contact: {str(e)}")
        return LambdaResponse.error(str(e), 500)


# ==================== Opportunity Handlers ====================

def create_opportunity_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to create Salesforce opportunity
    
    Event body:
    {
        "Name": "Deal Name",
        "Amount": 100000.0,
        "StageName": "Prospecting",
        "CloseDate": "2025-12-31",
        "AccountId": "001xx000003DHP1"
    }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        
        opportunity = SalesforceOpportunity(
            Name=body.get("Name"),
            Amount=body.get("Amount"),
            StageName=body.get("StageName", "Prospecting"),
            CloseDate=body.get("CloseDate"),
            AccountId=body.get("AccountId")
        )
        
        client = run_async(get_client())
        result = run_async(client.create_opportunity(opportunity))
        
        if result.success:
            logger.info(f"Created opportunity: {result.record_id}")
            return LambdaResponse.success({
                "record_id": result.record_id,
                "opportunity_name": opportunity.Name,
                "amount": opportunity.Amount
            }, 201)
        else:
            logger.error(f"Failed to create opportunity: {result.error}")
            return LambdaResponse.error(result.error or "Failed to create opportunity", 400)
            
    except Exception as e:
        logger.error(f"Error creating opportunity: {str(e)}")
        return LambdaResponse.error(str(e), 500)


def get_opportunity_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to retrieve Salesforce opportunity
    
    Path parameter: opportunity_id
    """
    try:
        opportunity_id = event.get("pathParameters", {}).get("opportunity_id")
        
        if not opportunity_id:
            return LambdaResponse.error("Missing opportunity_id parameter", 400)
        
        client = run_async(get_client())
        result = run_async(client.get_opportunity(opportunity_id))
        
        if result.success:
            logger.info(f"Retrieved opportunity: {opportunity_id}")
            return LambdaResponse.success(result.data)
        else:
            logger.error(f"Failed to get opportunity: {result.error}")
            return LambdaResponse.error(result.error or "Opportunity not found", 404)
            
    except Exception as e:
        logger.error(f"Error getting opportunity: {str(e)}")
        return LambdaResponse.error(str(e), 500)


def update_opportunity_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to update Salesforce opportunity
    
    Path parameter: opportunity_id
    Event body: Updated opportunity fields
    """
    try:
        opportunity_id = event.get("pathParameters", {}).get("opportunity_id")
        body = json.loads(event.get("body", "{}"))
        
        if not opportunity_id:
            return LambdaResponse.error("Missing opportunity_id parameter", 400)
        
        opportunity = SalesforceOpportunity(
            Name=body.get("Name"),
            Amount=body.get("Amount"),
            StageName=body.get("StageName"),
            CloseDate=body.get("CloseDate"),
            AccountId=body.get("AccountId", "")
        )
        
        client = run_async(get_client())
        result = run_async(client.update_opportunity(opportunity_id, opportunity))
        
        if result.success:
            logger.info(f"Updated opportunity: {opportunity_id}")
            return LambdaResponse.success({
                "record_id": opportunity_id,
                "status": "updated"
            })
        else:
            logger.error(f"Failed to update opportunity: {result.error}")
            return LambdaResponse.error(result.error or "Failed to update opportunity", 400)
            
    except Exception as e:
        logger.error(f"Error updating opportunity: {str(e)}")
        return LambdaResponse.error(str(e), 500)


def delete_opportunity_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to delete Salesforce opportunity
    
    Path parameter: opportunity_id
    """
    try:
        opportunity_id = event.get("pathParameters", {}).get("opportunity_id")
        
        if not opportunity_id:
            return LambdaResponse.error("Missing opportunity_id parameter", 400)
        
        client = run_async(get_client())
        result = run_async(client.delete_opportunity(opportunity_id))
        
        if result.success:
            logger.info(f"Deleted opportunity: {opportunity_id}")
            return LambdaResponse.success({
                "record_id": opportunity_id,
                "status": "deleted"
            })
        else:
            logger.error(f"Failed to delete opportunity: {result.error}")
            return LambdaResponse.error(result.error or "Failed to delete opportunity", 400)
            
    except Exception as e:
        logger.error(f"Error deleting opportunity: {str(e)}")
        return LambdaResponse.error(str(e), 500)


# ==================== Query Handler ====================

def query_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to execute SOQL query
    
    Event body:
    {
        "soql": "SELECT Id, Name FROM Account WHERE Industry = 'Technology'"
    }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        soql = body.get("soql")
        
        if not soql:
            return LambdaResponse.error("Missing SOQL query in request body", 400)
        
        client = run_async(get_client())
        result = run_async(client.query(soql))
        
        logger.info(f"Query executed: {result.totalSize} records found")
        return LambdaResponse.success({
            "total_size": result.totalSize,
            "done": result.done,
            "records": result.records
        })
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        return LambdaResponse.error(str(e), 400, "QUERY_ERROR")


# ==================== Batch Handler ====================

def batch_create_accounts_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler to create multiple accounts
    
    Event body:
    [
        {"Name": "Company 1", "Phone": "555-0001"},
        {"Name": "Company 2", "Phone": "555-0002"}
    ]
    """
    try:
        body = json.loads(event.get("body", "[]"))
        
        if not isinstance(body, list):
            return LambdaResponse.error("Request body must be an array of accounts", 400)
        
        client = run_async(get_client())
        results = []
        
        for account_data in body:
            account = SalesforceAccount(
                Name=account_data.get("Name"),
                Phone=account_data.get("Phone"),
                Website=account_data.get("Website"),
                Industry=account_data.get("Industry"),
                BillingCity=account_data.get("BillingCity"),
                BillingCountry=account_data.get("BillingCountry")
            )
            result = run_async(client.create_account(account))
            results.append({
                "success": result.success,
                "record_id": result.record_id,
                "error": result.error
            })
        
        successful = sum(1 for r in results if r["success"])
        logger.info(f"Batch created {successful}/{len(results)} accounts")
        
        return LambdaResponse.success({
            "total": len(results),
            "successful": successful,
            "failed": len(results) - successful,
            "results": results
        }, 201)
        
    except Exception as e:
        logger.error(f"Error in batch create: {str(e)}")
        return LambdaResponse.error(str(e), 500)


# ==================== Health Check ====================

def health_check_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for health check"""
    try:
        client = run_async(get_client())
        logger.info("Health check: Salesforce connection successful")
        return LambdaResponse.success({
            "status": "healthy",
            "salesforce_connected": True,
            "function": "aws_salesforce_lambda",
            "version": "1.0.0"
        })
    except Exception as e:
        logger.warning(f"Health check: Salesforce connection failed: {str(e)}")
        return LambdaResponse.success({
            "status": "degraded",
            "salesforce_connected": False,
            "error": str(e)
        })


# ==================== Router ====================

HANDLERS = {
    # Accounts
    "POST /accounts": create_account_handler,
    "GET /accounts/{account_id}": get_account_handler,
    "PATCH /accounts/{account_id}": update_account_handler,
    "DELETE /accounts/{account_id}": delete_account_handler,
    
    # Contacts
    "POST /contacts": create_contact_handler,
    "GET /contacts/{contact_id}": get_contact_handler,
    "PATCH /contacts/{contact_id}": update_contact_handler,
    "DELETE /contacts/{contact_id}": delete_contact_handler,
    
    # Opportunities
    "POST /opportunities": create_opportunity_handler,
    "GET /opportunities/{opportunity_id}": get_opportunity_handler,
    "PATCH /opportunities/{opportunity_id}": update_opportunity_handler,
    "DELETE /opportunities/{opportunity_id}": delete_opportunity_handler,
    
    # Advanced
    "POST /query": query_handler,
    "POST /batch/accounts": batch_create_accounts_handler,
    
    # Health
    "GET /health": health_check_handler,
}


def router(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API Gateway router that dispatches to appropriate handler
    
    Use with API Gateway Lambda integration:
    - httpMethod: GET, POST, PATCH, DELETE, etc.
    - path: /accounts, /contacts, /opportunities, /query, /health
    - pathParameters: for {id} values
    - body: JSON request body
    """
    try:
        http_method = event.get("httpMethod", "GET")
        path = event.get("path", "/")
        
        # Build handler key
        handler_key = f"{http_method} {path}"
        
        # Try exact match first
        if handler_key in HANDLERS:
            return HANDLERS[handler_key](event, context)
        
        # Try pattern matching for path parameters
        for pattern, handler in HANDLERS.items():
            if pattern.startswith(f"{http_method} "):
                pattern_path = pattern.split(" ", 1)[1]
                # Simple pattern matching for {param}
                if "{" in pattern_path:
                    import re
                    regex_pattern = re.escape(pattern_path).replace(r"\{[^}]+\}", "[^/]+")
                    if re.match(f"^{regex_pattern}$", path):
                        return handler(event, context)
        
        logger.error(f"No handler found for {handler_key}")
        return LambdaResponse.error(f"Not found: {handler_key}", 404, "NOT_FOUND")
        
    except Exception as e:
        logger.error(f"Router error: {str(e)}")
        return LambdaResponse.error(str(e), 500, "INTERNAL_ERROR")
