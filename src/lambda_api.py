import json
import boto3
import logging
from typing import Any, Dict

# Initialize S3 client
s3_client = boto3.client('s3')

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for API Gateway events.
    Reads objects from an S3 bucket based on query parameters.
    
    Expected query parameters:
    - bucket: S3 bucket name (required)
    - key: S3 object key (required)
    
    Returns:
    - 200: Successfully retrieved object
    - 400: Missing required parameters
    - 404: Object not found
    - 500: Internal server error
    """
    try:
        # Extract query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        bucket = query_params.get('bucket')
        key = query_params.get('key')
        
        # Validate required parameters
        if not bucket or not key:
            return create_response(
                400,
                {
                    'error': 'Missing required parameters',
                    'message': 'Both "bucket" and "key" query parameters are required'
                }
            )
        
        logger.info(f"Reading object: s3://{bucket}/{key}")
        
        # Read object from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        object_content = response['Body'].read().decode('utf-8')
        
        return create_response(
            200,
            {
                'message': 'Object retrieved successfully',
                'bucket': bucket,
                'key': key,
                'content': object_content,
                'content_type': response.get('ContentType', 'text/plain')
            }
        )
    
    except s3_client.exceptions.NoSuchBucket:
        logger.error(f"Bucket not found: {bucket}")
        return create_response(404, {'error': 'Bucket not found', 'bucket': bucket})
    
    except s3_client.exceptions.NoSuchKey:
        logger.error(f"Key not found: {key}")
        return create_response(404, {'error': 'Object not found', 'key': key})
    
    except Exception as e:
        logger.error(f"Error reading from S3: {str(e)}")
        return create_response(
            500,
            {'error': 'Internal server error', 'message': str(e)}
        )


def list_s3_objects(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler to list objects in an S3 bucket.
    
    Expected query parameters:
    - bucket: S3 bucket name (required)
    - prefix: Optional prefix to filter objects
    
    Returns:
    - 200: List of objects
    - 400: Missing bucket parameter
    - 404: Bucket not found
    - 500: Internal server error
    """
    try:
        query_params = event.get('queryStringParameters', {}) or {}
        bucket = query_params.get('bucket')
        prefix = query_params.get('prefix', '')
        
        if not bucket:
            return create_response(
                400,
                {'error': 'Missing required parameter', 'message': 'Bucket parameter is required'}
            )
        
        logger.info(f"Listing objects in bucket: {bucket} with prefix: {prefix}")
        
        # List objects in S3 bucket
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        objects = []
        if 'Contents' in response:
            objects = [
                {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                }
                for obj in response['Contents']
            ]
        
        return create_response(
            200,
            {
                'message': 'Objects listed successfully',
                'bucket': bucket,
                'prefix': prefix,
                'object_count': len(objects),
                'objects': objects
            }
        )
    
    except s3_client.exceptions.NoSuchBucket:
        logger.error(f"Bucket not found: {bucket}")
        return create_response(404, {'error': 'Bucket not found', 'bucket': bucket})
    
    except Exception as e:
        logger.error(f"Error listing S3 objects: {str(e)}")
        return create_response(
            500,
            {'error': 'Internal server error', 'message': str(e)}
        )


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a properly formatted API Gateway response.
    
    Args:
    - status_code: HTTP status code
    - body: Response body as dictionary
    
    Returns:
    - Formatted API Gateway response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }
