"""
Azure Integration Module

This module provides integration with various Azure services:
- Azure Blob Storage
- Azure Cosmos DB
- Azure Key Vault
- Azure Application Insights
- Azure Managed Identity

Usage:
    from azure_integration import (
        get_blob_client,
        get_cosmos_client,
        get_key_vault_client
    )
"""

import os
import logging
from typing import Optional, BinaryIO, List, Dict, Any
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.cosmos import CosmosClient, PartitionKey
from azure.keyvault.secrets import SecretClient
from azure.monitor.opentelemetry import configure_azure_monitor
import json

# Setup logging
logger = logging.getLogger(__name__)

# Azure Configuration
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_ACCOUNT_URL = f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
AZURE_COSMOS_ENDPOINT = os.getenv("AZURE_COSMOS_ENDPOINT")
AZURE_COSMOS_KEY = os.getenv("AZURE_COSMOS_KEY")
AZURE_COSMOS_DATABASE = os.getenv("AZURE_COSMOS_DATABASE", "python-api")
AZURE_KEY_VAULT_URL = os.getenv("AZURE_KEY_VAULT_URL")
AZURE_APPINSIGHTS_INSTRUMENTATION_KEY = os.getenv("AZURE_APPINSIGHTS_INSTRUMENTATION_KEY")

# Credential setup
try:
    # Try Managed Identity first (for Azure App Service, Container Apps)
    credential = ManagedIdentityCredential()
    logger.info("Using Managed Identity for Azure authentication")
except Exception:
    # Fall back to DefaultAzureCredential (local development)
    credential = DefaultAzureCredential()
    logger.info("Using DefaultAzureCredential for Azure authentication")


def get_blob_client(container_name: str, blob_name: str) -> Optional[BlobClient]:
    """
    Get an Azure Blob Storage client for a specific blob.
    
    Args:
        container_name: Name of the blob container
        blob_name: Name of the blob
    
    Returns:
        BlobClient or None if initialization fails
    
    Example:
        ```python
        blob_client = get_blob_client("data", "file.txt")
        with open("local_file.txt", "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        ```
    """
    try:
        if not AZURE_STORAGE_ACCOUNT_NAME:
            logger.error("AZURE_STORAGE_ACCOUNT_NAME not configured")
            return None
        
        blob_service_client = BlobServiceClient(
            account_url=AZURE_STORAGE_ACCOUNT_URL,
            credential=credential
        )
        
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        logger.info(f"Blob client created: {container_name}/{blob_name}")
        return blob_client
    
    except Exception as e:
        logger.error(f"Error creating blob client: {str(e)}")
        return None


def upload_blob(
    container_name: str,
    blob_name: str,
    data: BinaryIO,
    overwrite: bool = True
) -> bool:
    """
    Upload data to Azure Blob Storage.
    
    Args:
        container_name: Name of the blob container
        blob_name: Name of the blob to create
        data: Binary data to upload
        overwrite: Whether to overwrite existing blob
    
    Returns:
        True if successful, False otherwise
    
    Example:
        ```python
        with open("file.txt", "rb") as f:
            success = upload_blob("data", "file.txt", f)
        ```
    """
    try:
        blob_client = get_blob_client(container_name, blob_name)
        if not blob_client:
            return False
        
        blob_client.upload_blob(data, overwrite=overwrite)
        logger.info(f"Uploaded blob: {container_name}/{blob_name}")
        return True
    
    except Exception as e:
        logger.error(f"Error uploading blob: {str(e)}")
        return False


def download_blob(container_name: str, blob_name: str) -> Optional[bytes]:
    """
    Download blob data from Azure Blob Storage.
    
    Args:
        container_name: Name of the blob container
        blob_name: Name of the blob
    
    Returns:
        Blob data as bytes or None if failed
    
    Example:
        ```python
        data = download_blob("data", "file.txt")
        ```
    """
    try:
        blob_client = get_blob_client(container_name, blob_name)
        if not blob_client:
            return None
        
        download_stream = blob_client.download_blob()
        data = download_stream.readall()
        logger.info(f"Downloaded blob: {container_name}/{blob_name}")
        return data
    
    except Exception as e:
        logger.error(f"Error downloading blob: {str(e)}")
        return None


def list_blobs(container_name: str, prefix: str = "") -> Optional[List[str]]:
    """
    List blobs in a container.
    
    Args:
        container_name: Name of the blob container
        prefix: Optional prefix to filter blobs
    
    Returns:
        List of blob names or None if failed
    
    Example:
        ```python
        blobs = list_blobs("data", prefix="logs/")
        ```
    """
    try:
        if not AZURE_STORAGE_ACCOUNT_NAME:
            logger.error("AZURE_STORAGE_ACCOUNT_NAME not configured")
            return None
        
        blob_service_client = BlobServiceClient(
            account_url=AZURE_STORAGE_ACCOUNT_URL,
            credential=credential
        )
        
        container_client = blob_service_client.get_container_client(container_name)
        blobs = [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]
        
        logger.info(f"Listed {len(blobs)} blobs in {container_name}")
        return blobs
    
    except Exception as e:
        logger.error(f"Error listing blobs: {str(e)}")
        return None


def delete_blob(container_name: str, blob_name: str) -> bool:
    """
    Delete a blob from Azure Blob Storage.
    
    Args:
        container_name: Name of the blob container
        blob_name: Name of the blob
    
    Returns:
        True if successful, False otherwise
    """
    try:
        blob_client = get_blob_client(container_name, blob_name)
        if not blob_client:
            return False
        
        blob_client.delete_blob()
        logger.info(f"Deleted blob: {container_name}/{blob_name}")
        return True
    
    except Exception as e:
        logger.error(f"Error deleting blob: {str(e)}")
        return False


def get_cosmos_client() -> Optional[CosmosClient]:
    """
    Get an Azure Cosmos DB client.
    
    Returns:
        CosmosClient or None if initialization fails
    
    Example:
        ```python
        client = get_cosmos_client()
        database = client.get_database_client(AZURE_COSMOS_DATABASE)
        ```
    """
    try:
        if not AZURE_COSMOS_ENDPOINT:
            logger.error("AZURE_COSMOS_ENDPOINT not configured")
            return None
        
        client = CosmosClient(
            url=AZURE_COSMOS_ENDPOINT,
            credential=credential
        )
        
        logger.info("Cosmos DB client created")
        return client
    
    except Exception as e:
        logger.error(f"Error creating Cosmos DB client: {str(e)}")
        return None


def insert_cosmos_document(
    database_name: str,
    container_name: str,
    document: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Insert a document into Cosmos DB.
    
    Args:
        database_name: Name of the database
        container_name: Name of the container
        document: Document to insert (must include 'id' and partition key)
    
    Returns:
        Created document or None if failed
    """
    try:
        client = get_cosmos_client()
        if not client:
            return None
        
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        response = container.create_item(body=document)
        logger.info(f"Inserted document into {database_name}/{container_name}")
        return response
    
    except Exception as e:
        logger.error(f"Error inserting document: {str(e)}")
        return None


def query_cosmos_documents(
    database_name: str,
    container_name: str,
    query: str,
    parameters: Optional[List[Dict]] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Query documents from Cosmos DB.
    
    Args:
        database_name: Name of the database
        container_name: Name of the container
        query: SQL query string
        parameters: Optional query parameters
    
    Returns:
        List of matching documents or None if failed
    
    Example:
        ```python
        docs = query_cosmos_documents(
            "python-api",
            "items",
            "SELECT * FROM c WHERE c.status = @status",
            [{"name": "@status", "value": "active"}]
        )
        ```
    """
    try:
        client = get_cosmos_client()
        if not client:
            return None
        
        database = client.get_database_client(database_name)
        container = database.get_container_client(container_name)
        
        items = list(container.query_items(query=query, parameters=parameters))
        logger.info(f"Queried {len(items)} documents from {container_name}")
        return items
    
    except Exception as e:
        logger.error(f"Error querying documents: {str(e)}")
        return None


def get_key_vault_client() -> Optional[SecretClient]:
    """
    Get an Azure Key Vault client.
    
    Returns:
        SecretClient or None if initialization fails
    
    Example:
        ```python
        client = get_key_vault_client()
        secret = client.get_secret("my-secret")
        ```
    """
    try:
        if not AZURE_KEY_VAULT_URL:
            logger.error("AZURE_KEY_VAULT_URL not configured")
            return None
        
        client = SecretClient(vault_url=AZURE_KEY_VAULT_URL, credential=credential)
        logger.info("Key Vault client created")
        return client
    
    except Exception as e:
        logger.error(f"Error creating Key Vault client: {str(e)}")
        return None


def get_secret(secret_name: str) -> Optional[str]:
    """
    Get a secret from Azure Key Vault.
    
    Args:
        secret_name: Name of the secret
    
    Returns:
        Secret value or None if not found
    
    Example:
        ```python
        api_key = get_secret("api-key")
        ```
    """
    try:
        client = get_key_vault_client()
        if not client:
            return None
        
        secret = client.get_secret(secret_name)
        logger.info(f"Retrieved secret: {secret_name}")
        return secret.value
    
    except Exception as e:
        logger.error(f"Error getting secret: {str(e)}")
        return None


def configure_app_insights():
    """
    Configure Azure Application Insights for monitoring.
    
    Should be called early in application startup.
    
    Example:
        ```python
        configure_app_insights()
        ```
    """
    try:
        if AZURE_APPINSIGHTS_INSTRUMENTATION_KEY:
            configure_azure_monitor()
            logger.info("Application Insights configured")
        else:
            logger.warning("Application Insights key not configured")
    
    except Exception as e:
        logger.error(f"Error configuring Application Insights: {str(e)}")
