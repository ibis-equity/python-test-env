import json
import boto3
import pandas as pd
import logging
from datetime import datetime
from typing import Any, Dict, List
import io

# Initialize AWS clients
s3_client = boto3.client('s3')
glue_client = boto3.client('glue')
kinesis_client = boto3.client('kinesis')

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for processing Kinesis Data Streams records.
    Reads data from Kinesis, processes with Pandas, writes to S3, and updates Glue table.
    
    Environment variables required:
    - S3_BUCKET: Target S3 bucket
    - S3_PREFIX: S3 key prefix (optional)
    - GLUE_DATABASE: Glue database name
    - GLUE_TABLE: Glue table name
    - STREAM_NAME: Kinesis stream name (optional, can be in event)
    
    Returns:
    - statusCode: 200 for success, 500 for error
    - body: JSON response with status and details
    """
    try:
        import os
        
        s3_bucket = os.environ.get('S3_BUCKET')
        s3_prefix = os.environ.get('S3_PREFIX', 'data')
        glue_database = os.environ.get('GLUE_DATABASE')
        glue_table = os.environ.get('GLUE_TABLE')
        
        if not all([s3_bucket, glue_database, glue_table]):
            return create_response(
                400,
                {
                    'error': 'Missing environment variables',
                    'message': 'S3_BUCKET, GLUE_DATABASE, and GLUE_TABLE are required'
                }
            )
        
        logger.info(f"Processing Kinesis stream records: {len(event.get('Records', []))} records")
        
        # Extract and process Kinesis records
        df = extract_kinesis_records(event)
        
        if df.empty:
            logger.warning("No records to process")
            return create_response(200, {'message': 'No records to process', 'records_processed': 0})
        
        logger.info(f"Processed {len(df)} records into DataFrame")
        
        # Write to S3
        s3_path = write_to_s3(df, s3_bucket, s3_prefix)
        logger.info(f"Data written to S3: s3://{s3_bucket}/{s3_path}")
        
        # Update Glue table
        update_glue_table(df, glue_database, glue_table, s3_bucket, s3_path)
        logger.info(f"Glue table updated: {glue_database}.{glue_table}")
        
        return create_response(
            200,
            {
                'message': 'Successfully processed and stored data',
                'records_processed': len(df),
                's3_location': f"s3://{s3_bucket}/{s3_path}",
                'glue_table': f"{glue_database}.{glue_table}"
            }
        )
    
    except Exception as e:
        logger.error(f"Error processing records: {str(e)}", exc_info=True)
        return create_response(
            500,
            {'error': 'Internal server error', 'message': str(e)}
        )


def extract_kinesis_records(event: Dict[str, Any]) -> pd.DataFrame:
    """
    Extract and parse records from Kinesis Data Streams event.
    
    Expected record format:
    - kinesis.data: Base64-encoded JSON data
    
    Args:
    - event: Kinesis event from Lambda trigger
    
    Returns:
    - DataFrame with processed records
    """
    import base64
    
    records_data = []
    
    for record in event.get('Records', []):
        try:
            # Decode Kinesis data
            kinesis_data = record.get('kinesis', {})
            encoded_data = kinesis_data.get('data')
            
            if encoded_data:
                decoded_data = base64.b64decode(encoded_data).decode('utf-8')
                record_json = json.loads(decoded_data)
                records_data.append(record_json)
                logger.debug(f"Decoded record: {record_json}")
        
        except Exception as e:
            logger.warning(f"Failed to decode record: {str(e)}")
            continue
    
    # Create DataFrame from records
    if records_data:
        df = pd.DataFrame(records_data)
        # Add processing timestamp
        df['processing_timestamp'] = datetime.utcnow().isoformat()
        return df
    
    return pd.DataFrame()


def write_to_s3(df: pd.DataFrame, bucket: str, prefix: str) -> str:
    """
    Write DataFrame to S3 as Parquet format.
    
    Args:
    - df: pandas DataFrame
    - bucket: S3 bucket name
    - prefix: S3 key prefix
    
    Returns:
    - S3 key path
    """
    try:
        # Create S3 path with timestamp
        timestamp = datetime.utcnow().strftime('%Y/%m/%d/%H%M%S')
        s3_key = f"{prefix}/{timestamp}/data.parquet"
        
        # Write DataFrame to Parquet in memory
        parquet_buffer = io.BytesIO()
        df.to_parquet(parquet_buffer, index=False, engine='pyarrow')
        parquet_buffer.seek(0)
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=parquet_buffer.getvalue(),
            ContentType='application/octet-stream',
            Metadata={
                'source': 'kinesis-stream',
                'record_count': str(len(df)),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Uploaded {len(df)} records to S3: {s3_key}")
        return s3_key
    
    except Exception as e:
        logger.error(f"Error writing to S3: {str(e)}")
        raise


def update_glue_table(df: pd.DataFrame, database: str, table_name: str, 
                     s3_bucket: str, s3_path: str) -> None:
    """
    Create or update Glue table schema based on DataFrame.
    
    Args:
    - df: pandas DataFrame
    - database: Glue database name
    - table_name: Glue table name
    - s3_bucket: S3 bucket name
    - s3_path: S3 path to data
    """
    try:
        # Generate Glue schema from DataFrame
        columns = generate_glue_columns(df)
        
        # Check if table exists
        try:
            glue_client.get_table(Database=database, Name=table_name)
            logger.info(f"Table {table_name} exists, updating...")
            
            # Update table
            glue_client.update_table(
                DatabaseName=database,
                TableInput={
                    'Name': table_name,
                    'StorageDescriptor': {
                        'Columns': columns,
                        'Location': f"s3://{s3_bucket}/{s3_path.rsplit('/', 1)[0]}/",
                        'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
                        'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
                        'SerdeInfo': {
                            'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
                        }
                    }
                }
            )
        
        except glue_client.exceptions.EntityNotFoundException:
            logger.info(f"Table {table_name} does not exist, creating...")
            
            # Create new table
            glue_client.create_table(
                DatabaseName=database,
                TableInput={
                    'Name': table_name,
                    'StorageDescriptor': {
                        'Columns': columns,
                        'Location': f"s3://{s3_bucket}/{s3_path.rsplit('/', 1)[0]}/",
                        'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
                        'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
                        'SerdeInfo': {
                            'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
                        }
                    }
                }
            )
    
    except Exception as e:
        logger.error(f"Error updating Glue table: {str(e)}")
        raise


def generate_glue_columns(df: pd.DataFrame) -> List[Dict[str, str]]:
    """
    Generate Glue column definitions from pandas DataFrame.
    
    Args:
    - df: pandas DataFrame
    
    Returns:
    - List of column definitions for Glue table
    """
    type_mapping = {
        'int64': 'bigint',
        'int32': 'int',
        'float64': 'double',
        'float32': 'float',
        'object': 'string',
        'bool': 'boolean',
        'datetime64[ns]': 'timestamp',
        'string': 'string'
    }
    
    columns = []
    for col_name, dtype in df.dtypes.items():
        glue_type = type_mapping.get(str(dtype), 'string')
        columns.append({
            'Name': col_name,
            'Type': glue_type
        })
    
    return columns


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a properly formatted Lambda response.
    
    Args:
    - status_code: HTTP status code
    - body: Response body as dictionary
    
    Returns:
    - Formatted response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }


def batch_get_kinesis_records(stream_name: str, shard_id: str, 
                              shard_iterator_type: str = 'LATEST') -> pd.DataFrame:
    """
    Batch retrieve and process records from Kinesis stream.
    Useful for manual invocation or batch processing.
    
    Args:
    - stream_name: Kinesis stream name
    - shard_id: Shard ID
    - shard_iterator_type: 'TRIM_HORIZON' or 'LATEST'
    
    Returns:
    - DataFrame with records
    """
    try:
        # Get shard iterator
        response = kinesis_client.get_shard_iterator(
            StreamName=stream_name,
            ShardId=shard_id,
            ShardIteratorType=shard_iterator_type
        )
        shard_iterator = response['ShardIterator']
        
        all_records = []
        
        # Retrieve records from shard
        while shard_iterator:
            response = kinesis_client.get_records(
                ShardIterator=shard_iterator,
                Limit=100
            )
            
            for record in response['Records']:
                import base64
                decoded_data = base64.b64decode(record['Data']).decode('utf-8')
                all_records.append(json.loads(decoded_data))
            
            shard_iterator = response.get('NextShardIterator')
        
        logger.info(f"Retrieved {len(all_records)} records from Kinesis stream")
        
        if all_records:
            df = pd.DataFrame(all_records)
            df['processing_timestamp'] = datetime.utcnow().isoformat()
            return df
        
        return pd.DataFrame()
    
    except Exception as e:
        logger.error(f"Error retrieving Kinesis records: {str(e)}")
        raise
