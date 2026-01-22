from fastapi import FastAPI, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import os
import json
import logging
from mangum import Mangum

# Configure logging for AWS Lambda and local development
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define request/response models for better documentation
class Item(BaseModel):
    """Item model for API requests and responses."""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the item")
    description: Optional[str] = Field(None, max_length=500, description="Detailed description of the item")
    status: Optional[str] = Field("created", description="Current status of the item")


class ItemResponse(BaseModel):
    """Response model for item operations."""
    item_id: Optional[int] = Field(None, description="Unique identifier for the item")
    name: Optional[str] = Field(None, description="Name of the item")
    description: Optional[str] = Field(None, description="Description of the item")
    status: str = Field(..., description="Status of the operation or item")
    query: Optional[str] = Field(None, description="Query parameter if provided")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status of the API")
    version: str = Field("1.0.0", description="API version")


# Initialize FastAPI with comprehensive metadata
app = FastAPI(
    title="Python API",
    description="""
A comprehensive Python API built with FastAPI for managing items and server health.

## Features
- Item management (create, read)
- Health check endpoint
- AWS Lambda integration ready
- Comprehensive API documentation

## Authentication
Currently no authentication required (demo).

## Rate Limiting
No rate limiting (demo).
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "url": "http://localhost:8000/docs",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": 1}
)


@app.get(
    "/",
    response_model=dict,
    tags=["General"],
    summary="Welcome endpoint",
    description="Returns a welcome message from the API",
    responses={
        200: {"description": "Successful response with welcome message"}
    }
)
async def read_root():
    """
    Root endpoint that returns a welcome message.
    
    Returns:
        dict: A dictionary containing a welcome message
    """
    return {
        "message": "Welcome to the Python API",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/api/v1/openapi.json"
        }
    }


@app.get(
    "/api/items/{item_id}",
    response_model=ItemResponse,
    tags=["Items"],
    summary="Get item by ID",
    description="Retrieves an item by its ID with optional query parameter",
    responses={
        200: {"description": "Item retrieved successfully", "model": ItemResponse},
        404: {"description": "Item not found"}
    }
)
async def read_item(
    item_id: int = Path(..., gt=0, description="The ID of the item to retrieve"),
    q: Optional[str] = Query(None, min_length=1, max_length=50, description="Optional query parameter")
) -> ItemResponse:
    """
    Get an item by its ID.
    
    Args:
        item_id: The unique identifier of the item (must be greater than 0)
        q: Optional search query parameter
    
    Returns:
        ItemResponse: The item details with optional query information
    
    Example:
        ```
        GET /api/items/1?q=search_term
        ```
    """
    return ItemResponse(
        item_id=item_id,
        query=q,
        name=f"Item {item_id}",
        description=f"Description for item {item_id}",
        status="retrieved"
    )


@app.post(
    "/api/items/",
    response_model=ItemResponse,
    tags=["Items"],
    summary="Create a new item",
    description="Creates a new item with the provided name and optional description",
    status_code=201,
    responses={
        201: {"description": "Item created successfully", "model": ItemResponse},
        400: {"description": "Invalid request body"}
    }
)
async def create_item(
    item: Item
) -> ItemResponse:
    """
    Create a new item.
    
    Args:
        item: Item object containing name and optional description
    
    Returns:
        ItemResponse: The created item with status information
    
    Example:
        ```json
        {
            "name": "New Item",
            "description": "A new item description"
        }
        ```
    """
    return ItemResponse(
        name=item.name,
        description=item.description,
        status=item.status or "created"
    )


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint",
    description="Returns the health status of the API",
    responses={
        200: {"description": "API is healthy", "model": HealthResponse}
    }
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for monitoring.
    
    Returns:
        HealthResponse: Current health status and version information
    
    Use this endpoint to verify the API is running and responsive.
    """
    return HealthResponse(status="healthy", version="1.0.0")


@app.get(
    "/api/aws-info",
    response_model=dict,
    tags=["AWS"],
    summary="Get AWS environment info",
    description="Returns AWS Lambda environment information when running in Lambda"
)
async def get_aws_info():
    """
    Get AWS Lambda environment information.
    
    Returns:
        dict: AWS environment details including function name, region, and environment type
    """
    return {
        "lambda_function_name": os.getenv("AWS_LAMBDA_FUNCTION_NAME", "local"),
        "aws_region": os.getenv("AWS_REGION", "us-east-1"),
        "environment": "aws" if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "local",
        "lambda_version": os.getenv("AWS_LAMBDA_FUNCTION_VERSION", "N/A")
    }


# AWS Lambda handler wrapper - translates API Gateway events to ASGI
lambda_handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
