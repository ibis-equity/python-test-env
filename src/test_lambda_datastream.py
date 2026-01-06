import json
import pytest
import pandas as pd
import base64
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime
from botocore.exceptions import ClientError
import lambda_datastream


class TestExtractKinesisRecords:
    """Test cases for extract_kinesis_records function."""
    
    def test_extract_kinesis_records_success(self):
        """Test successful extraction of Kinesis records."""
        # Create test data
        test_data = [
            {'id': 1, 'name': 'record1', 'value': 100},
            {'id': 2, 'name': 'record2', 'value': 200}
        ]
        
        # Encode data as Kinesis would
        encoded_records = [
            {
                'kinesis': {
                    'data': base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
                }
            }
            for data in test_data
        ]
        
        event = {'Records': encoded_records}
        
        # Extract records
        df = lambda_datastream.extract_kinesis_records(event)
        
        # Assertions
        assert len(df) == 2
        assert 'processing_timestamp' in df.columns
        assert df['id'].tolist() == [1, 2]
        assert df['name'].tolist() == ['record1', 'record2']
        assert df['value'].tolist() == [100, 200]
    
    def test_extract_kinesis_records_empty_event(self):
        """Test extraction with no records."""
        event = {'Records': []}
        
        df = lambda_datastream.extract_kinesis_records(event)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_extract_kinesis_records_no_records_key(self):
        """Test extraction with missing Records key."""
        event = {}
        
        df = lambda_datastream.extract_kinesis_records(event)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_extract_kinesis_records_invalid_json(self):
        """Test extraction with invalid JSON data."""
        # Create invalid data
        invalid_records = [
            {
                'kinesis': {
                    'data': base64.b64encode(b'invalid json').decode('utf-8')
                }
            },
            {
                'kinesis': {
                    'data': base64.b64encode(json.dumps({'id': 1}).encode('utf-8')).decode('utf-8')
                }
            }
        ]
        
        event = {'Records': invalid_records}
        
        # Should skip invalid record and process valid one
        df = lambda_datastream.extract_kinesis_records(event)
        
        assert len(df) == 1
        assert df['id'].iloc[0] == 1
    
    def test_extract_kinesis_records_no_data_field(self):
        """Test extraction with missing data field."""
        records = [
            {
                'kinesis': {
                    'sequenceNumber': '123'
                }
            }
        ]
        
        event = {'Records': records}
        df = lambda_datastream.extract_kinesis_records(event)
        
        assert len(df) == 0


class TestWriteToS3:
    """Test cases for write_to_s3 function."""
    
    @patch('lambda_datastream.s3_client')
    def test_write_to_s3_success(self, mock_s3):
        """Test successful write to S3."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['a', 'b', 'c'],
            'value': [10.5, 20.5, 30.5]
        })
        
        s3_key = lambda_datastream.write_to_s3(df, 'test-bucket', 'data')
        
        # Assertions
        assert 'data/' in s3_key
        assert s3_key.endswith('data.parquet')
        mock_s3.put_object.assert_called_once()
        
        # Verify call arguments
        call_args = mock_s3.put_object.call_args
        assert call_args.kwargs['Bucket'] == 'test-bucket'
        assert call_args.kwargs['Key'] == s3_key
        assert call_args.kwargs['ContentType'] == 'application/octet-stream'
        assert 'source' in call_args.kwargs['Metadata']
        assert call_args.kwargs['Metadata']['record_count'] == '3'
    
    @patch('lambda_datastream.s3_client')
    def test_write_to_s3_empty_dataframe(self, mock_s3):
        """Test write with empty DataFrame."""
        df = pd.DataFrame()
        
        s3_key = lambda_datastream.write_to_s3(df, 'test-bucket', 'data')
        
        assert mock_s3.put_object.called
        assert '0' in mock_s3.put_object.call_args.kwargs['Metadata']['record_count']
    
    @patch('lambda_datastream.s3_client')
    def test_write_to_s3_with_custom_prefix(self, mock_s3):
        """Test write with custom S3 prefix."""
        df = pd.DataFrame({'col': [1, 2]})
        
        s3_key = lambda_datastream.write_to_s3(df, 'test-bucket', 'custom/prefix')
        
        assert s3_key.startswith('custom/prefix/')
    
    @patch('lambda_datastream.s3_client')
    def test_write_to_s3_s3_error(self, mock_s3):
        """Test write when S3 operation fails."""
        df = pd.DataFrame({'col': [1, 2]})
        mock_s3.put_object.side_effect = Exception('S3 Connection Error')
        
        with pytest.raises(Exception) as exc_info:
            lambda_datastream.write_to_s3(df, 'test-bucket', 'data')
        
        assert 'S3 Connection Error' in str(exc_info.value)


class TestGenerateGlueColumns:
    """Test cases for generate_glue_columns function."""
    
    def test_generate_glue_columns_mixed_types(self):
        """Test column generation with mixed data types."""
        df = pd.DataFrame({
            'int_col': [1, 2, 3],
            'float_col': [1.5, 2.5, 3.5],
            'str_col': ['a', 'b', 'c'],
            'bool_col': [True, False, True]
        })
        
        columns = lambda_datastream.generate_glue_columns(df)
        
        assert len(columns) == 4
        
        # Check column names
        col_names = [col['Name'] for col in columns]
        assert 'int_col' in col_names
        assert 'float_col' in col_names
        assert 'str_col' in col_names
        assert 'bool_col' in col_names
        
        # Check types
        col_dict = {col['Name']: col['Type'] for col in columns}
        assert col_dict['int_col'] == 'bigint'
        assert col_dict['float_col'] == 'double'
        assert col_dict['str_col'] == 'string'
        assert col_dict['bool_col'] == 'boolean'
    
    def test_generate_glue_columns_single_type(self):
        """Test column generation with single data type."""
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [4, 5, 6]
        })
        
        columns = lambda_datastream.generate_glue_columns(df)
        
        assert len(columns) == 2
        assert all(col['Type'] == 'bigint' for col in columns)
    
    def test_generate_glue_columns_empty_dataframe(self):
        """Test column generation with empty DataFrame."""
        df = pd.DataFrame()
        
        columns = lambda_datastream.generate_glue_columns(df)
        
        assert isinstance(columns, list)
        assert len(columns) == 0


class TestUpdateGlueTable:
    """Test cases for update_glue_table function."""
    
    @patch('lambda_datastream.glue_client')
    def test_update_glue_table_create_new(self, mock_glue):
        """Test creating a new Glue table."""
        # Mock table not found
        mock_glue.get_table.side_effect = mock_glue.exceptions.EntityNotFoundException({}, 'GetTable')
        
        df = pd.DataFrame({
            'id': [1, 2],
            'name': ['a', 'b']
        })
        
        lambda_datastream.update_glue_table(df, 'test_db', 'test_table', 'bucket', 'path/data.parquet')
        
        # Verify create_table was called
        assert mock_glue.create_table.called
        call_args = mock_glue.create_table.call_args
        assert call_args.kwargs['DatabaseName'] == 'test_db'
        assert call_args.kwargs['TableInput']['Name'] == 'test_table'
    
    @patch('lambda_datastream.glue_client')
    def test_update_glue_table_update_existing(self, mock_glue):
        """Test updating an existing Glue table."""
        # Mock table exists
        mock_glue.get_table.return_value = {'Table': {'Name': 'test_table'}}
        
        df = pd.DataFrame({
            'id': [1, 2],
            'name': ['a', 'b']
        })
        
        lambda_datastream.update_glue_table(df, 'test_db', 'test_table', 'bucket', 'path/data.parquet')
        
        # Verify update_table was called
        assert mock_glue.update_table.called
        call_args = mock_glue.update_table.call_args
        assert call_args.kwargs['DatabaseName'] == 'test_db'
        assert call_args.kwargs['TableInput']['Name'] == 'test_table'
    
    @patch('lambda_datastream.glue_client')
    def test_update_glue_table_with_columns(self, mock_glue):
        """Test table schema generation."""
        mock_glue.get_table.side_effect = mock_glue.exceptions.EntityNotFoundException({}, 'GetTable')
        
        df = pd.DataFrame({
            'col1': [1, 2],
            'col2': ['a', 'b'],
            'col3': [1.5, 2.5]
        })
        
        lambda_datastream.update_glue_table(df, 'test_db', 'test_table', 'bucket', 'path/data.parquet')
        
        call_args = mock_glue.create_table.call_args
        columns = call_args.kwargs['TableInput']['StorageDescriptor']['Columns']
        
        assert len(columns) == 3
        col_dict = {col['Name']: col['Type'] for col in columns}
        assert col_dict['col1'] == 'bigint'
        assert col_dict['col2'] == 'string'
        assert col_dict['col3'] == 'double'
    
    @patch('lambda_datastream.glue_client')
    def test_update_glue_table_error(self, mock_glue):
        """Test error handling in Glue update."""
        mock_glue.get_table.side_effect = Exception('Glue Error')
        
        df = pd.DataFrame({'col': [1, 2]})
        
        with pytest.raises(Exception) as exc_info:
            lambda_datastream.update_glue_table(df, 'test_db', 'test_table', 'bucket', 'path/data.parquet')
        
        assert 'Glue Error' in str(exc_info.value)


class TestLambdaHandler:
    """Test cases for lambda_handler function."""
    
    @patch.dict('os.environ', {
        'S3_BUCKET': 'test-bucket',
        'GLUE_DATABASE': 'test_db',
        'GLUE_TABLE': 'test_table'
    })
    @patch('lambda_datastream.update_glue_table')
    @patch('lambda_datastream.write_to_s3')
    @patch('lambda_datastream.extract_kinesis_records')
    def test_lambda_handler_success(self, mock_extract, mock_write, mock_update):
        """Test successful lambda handler execution."""
        # Mock DataFrame
        mock_df = pd.DataFrame({
            'id': [1, 2],
            'data': ['a', 'b']
        })
        mock_extract.return_value = mock_df
        mock_write.return_value = 'path/to/data.parquet'
        
        event = {'Records': []}
        response = lambda_datastream.lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Successfully processed and stored data'
        assert body['records_processed'] == 2
    
    @patch.dict('os.environ', {})
    def test_lambda_handler_missing_env_vars(self):
        """Test handler with missing environment variables."""
        event = {'Records': []}
        response = lambda_datastream.lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Missing environment variables'
    
    @patch.dict('os.environ', {
        'S3_BUCKET': 'test-bucket',
        'GLUE_DATABASE': 'test_db',
        'GLUE_TABLE': 'test_table'
    })
    @patch('lambda_datastream.extract_kinesis_records')
    def test_lambda_handler_no_records(self, mock_extract):
        """Test handler with no records."""
        mock_extract.return_value = pd.DataFrame()
        
        event = {'Records': []}
        response = lambda_datastream.lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'No records to process'
        assert body['records_processed'] == 0
    
    @patch.dict('os.environ', {
        'S3_BUCKET': 'test-bucket',
        'GLUE_DATABASE': 'test_db',
        'GLUE_TABLE': 'test_table'
    })
    @patch('lambda_datastream.extract_kinesis_records')
    def test_lambda_handler_exception(self, mock_extract):
        """Test handler exception handling."""
        mock_extract.side_effect = Exception('Processing Error')
        
        event = {'Records': []}
        response = lambda_datastream.lambda_handler(event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['error'] == 'Internal server error'
        assert 'Processing Error' in body['message']


class TestCreateResponse:
    """Test cases for create_response function."""
    
    def test_create_response_200(self):
        """Test response with 200 status."""
        body = {'message': 'Success', 'data': [1, 2, 3]}
        response = lambda_datastream.create_response(200, body)
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/json'
        assert json.loads(response['body']) == body
    
    def test_create_response_400(self):
        """Test response with 400 status."""
        body = {'error': 'Bad Request'}
        response = lambda_datastream.create_response(400, body)
        
        assert response['statusCode'] == 400
        assert json.loads(response['body']) == body
    
    def test_create_response_500(self):
        """Test response with 500 status."""
        body = {'error': 'Internal Server Error', 'message': 'Something failed'}
        response = lambda_datastream.create_response(500, body)
        
        assert response['statusCode'] == 500
        assert json.loads(response['body']) == body


class TestBatchGetKinesisRecords:
    """Test cases for batch_get_kinesis_records function."""
    
    @patch('lambda_datastream.kinesis_client')
    def test_batch_get_kinesis_records_success(self, mock_kinesis):
        """Test successful batch retrieval of Kinesis records."""
        # Mock iterator response
        mock_kinesis.get_shard_iterator.return_value = {
            'ShardIterator': 'test-iterator'
        }
        
        # Mock records response
        test_data = [
            {'id': 1, 'value': 'test1'},
            {'id': 2, 'value': 'test2'}
        ]
        encoded_records = [
            {
                'Data': base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
            }
            for data in test_data
        ]
        
        mock_kinesis.get_records.return_value = {
            'Records': encoded_records,
            'NextShardIterator': None
        }
        
        df = lambda_datastream.batch_get_kinesis_records('test-stream', 'test-shard')
        
        assert len(df) == 2
        assert 'processing_timestamp' in df.columns
        assert df['id'].tolist() == [1, 2]
    
    @patch('lambda_datastream.kinesis_client')
    def test_batch_get_kinesis_records_multiple_calls(self, mock_kinesis):
        """Test batch retrieval with pagination."""
        mock_kinesis.get_shard_iterator.return_value = {
            'ShardIterator': 'iterator-1'
        }
        
        # First call returns records and next iterator
        # Second call returns more records with no next iterator
        test_data_1 = [{'id': 1}]
        test_data_2 = [{'id': 2}]
        
        encoded_1 = [
            {
                'Data': base64.b64encode(json.dumps(test_data_1[0]).encode('utf-8')).decode('utf-8')
            }
        ]
        encoded_2 = [
            {
                'Data': base64.b64encode(json.dumps(test_data_2[0]).encode('utf-8')).decode('utf-8')
            }
        ]
        
        mock_kinesis.get_records.side_effect = [
            {'Records': encoded_1, 'NextShardIterator': 'iterator-2'},
            {'Records': encoded_2, 'NextShardIterator': None}
        ]
        
        df = lambda_datastream.batch_get_kinesis_records('test-stream', 'test-shard')
        
        assert len(df) == 2
        assert mock_kinesis.get_records.call_count == 2
    
    @patch('lambda_datastream.kinesis_client')
    def test_batch_get_kinesis_records_empty(self, mock_kinesis):
        """Test batch retrieval with no records."""
        mock_kinesis.get_shard_iterator.return_value = {
            'ShardIterator': 'test-iterator'
        }
        
        mock_kinesis.get_records.return_value = {
            'Records': [],
            'NextShardIterator': None
        }
        
        df = lambda_datastream.batch_get_kinesis_records('test-stream', 'test-shard')
        
        assert len(df) == 0
    
    @patch('lambda_datastream.kinesis_client')
    def test_batch_get_kinesis_records_error(self, mock_kinesis):
        """Test batch retrieval error handling."""
        mock_kinesis.get_shard_iterator.side_effect = Exception('Kinesis Error')
        
        with pytest.raises(Exception) as exc_info:
            lambda_datastream.batch_get_kinesis_records('test-stream', 'test-shard')
        
        assert 'Kinesis Error' in str(exc_info.value)


class TestIntegration:
    """Integration tests."""
    
    @patch.dict('os.environ', {
        'S3_BUCKET': 'test-bucket',
        'GLUE_DATABASE': 'test_db',
        'GLUE_TABLE': 'test_table'
    })
    @patch('lambda_datastream.glue_client')
    @patch('lambda_datastream.s3_client')
    def test_full_pipeline_end_to_end(self, mock_s3, mock_glue):
        """Test complete pipeline from Kinesis to S3 to Glue."""
        # Setup
        mock_glue.get_table.side_effect = mock_glue.exceptions.EntityNotFoundException({}, 'GetTable')
        
        # Create test event
        test_data = [
            {'id': 1, 'name': 'Alice', 'score': 95.5},
            {'id': 2, 'name': 'Bob', 'score': 87.3}
        ]
        encoded_records = [
            {
                'kinesis': {
                    'data': base64.b64encode(json.dumps(data).encode('utf-8')).decode('utf-8')
                }
            }
            for data in test_data
        ]
        event = {'Records': encoded_records}
        
        # Execute
        response = lambda_datastream.lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['records_processed'] == 2
        assert mock_s3.put_object.called
        assert mock_glue.create_table.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
