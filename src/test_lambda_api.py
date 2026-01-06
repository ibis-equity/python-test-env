import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
import lambda_api


class TestLambdaHandler:
    """Test cases for the lambda_handler function."""
    
    @patch('lambda_api.s3_client')
    def test_lambda_handler_success(self, mock_s3):
        """Test successful S3 object retrieval."""
        # Mock the S3 response
        mock_body = MagicMock()
        mock_body.read.return_value = b'test content'
        mock_s3.get_object.return_value = {
            'Body': mock_body,
            'ContentType': 'text/plain'
        }
        
        # Create event
        event = {
            'queryStringParameters': {
                'bucket': 'test-bucket',
                'key': 'test-key.txt'
            }
        }
        
        # Call handler
        response = lambda_api.lambda_handler(event, None)
        
        # Assertions
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Object retrieved successfully'
        assert body['bucket'] == 'test-bucket'
        assert body['key'] == 'test-key.txt'
        assert body['content'] == 'test content'
        mock_s3.get_object.assert_called_once_with(Bucket='test-bucket', Key='test-key.txt')
    
    def test_lambda_handler_missing_bucket(self):
        """Test handler with missing bucket parameter."""
        event = {
            'queryStringParameters': {
                'key': 'test-key.txt'
            }
        }
        
        response = lambda_api.lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Missing required parameters'
    
    def test_lambda_handler_missing_key(self):
        """Test handler with missing key parameter."""
        event = {
            'queryStringParameters': {
                'bucket': 'test-bucket'
            }
        }
        
        response = lambda_api.lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Missing required parameters'
    
    def test_lambda_handler_no_query_params(self):
        """Test handler with no query parameters."""
        event = {
            'queryStringParameters': None
        }
        
        response = lambda_api.lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Missing required parameters'
    
    @patch('lambda_api.s3_client')
    def test_lambda_handler_bucket_not_found(self, mock_s3):
        """Test handler when bucket doesn't exist."""
        # Mock NoSuchBucket exception
        error_response = {'Error': {'Code': 'NoSuchBucket'}}
        mock_s3.get_object.side_effect = ClientError(error_response, 'GetObject')
        mock_s3.exceptions.NoSuchBucket = ClientError
        
        event = {
            'queryStringParameters': {
                'bucket': 'nonexistent-bucket',
                'key': 'test-key.txt'
            }
        }
        
        response = lambda_api.lambda_handler(event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['error'] == 'Internal server error'
    
    @patch('lambda_api.s3_client')
    def test_lambda_handler_key_not_found(self, mock_s3):
        """Test handler when key doesn't exist."""
        # Mock NoSuchKey exception
        error_response = {'Error': {'Code': 'NoSuchKey'}}
        mock_s3.get_object.side_effect = ClientError(error_response, 'GetObject')
        mock_s3.exceptions.NoSuchKey = ClientError
        
        event = {
            'queryStringParameters': {
                'bucket': 'test-bucket',
                'key': 'nonexistent-key.txt'
            }
        }
        
        response = lambda_api.lambda_handler(event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['error'] == 'Internal server error'
    
    @patch('lambda_api.s3_client')
    def test_lambda_handler_s3_error(self, mock_s3):
        """Test handler with generic S3 error."""
        mock_s3.get_object.side_effect = Exception('S3 Connection Error')
        
        event = {
            'queryStringParameters': {
                'bucket': 'test-bucket',
                'key': 'test-key.txt'
            }
        }
        
        response = lambda_api.lambda_handler(event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['error'] == 'Internal server error'


class TestListS3Objects:
    """Test cases for the list_s3_objects function."""
    
    @patch('lambda_api.s3_client')
    def test_list_s3_objects_success(self, mock_s3):
        """Test successful listing of S3 objects."""
        mock_s3.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'file1.txt',
                    'Size': 100,
                    'LastModified': MagicMock(isoformat=Mock(return_value='2026-01-05T10:00:00'))
                },
                {
                    'Key': 'file2.txt',
                    'Size': 200,
                    'LastModified': MagicMock(isoformat=Mock(return_value='2026-01-05T11:00:00'))
                }
            ]
        }
        
        event = {
            'queryStringParameters': {
                'bucket': 'test-bucket',
                'prefix': 'logs/'
            }
        }
        
        response = lambda_api.list_s3_objects(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['message'] == 'Objects listed successfully'
        assert body['object_count'] == 2
        assert len(body['objects']) == 2
        mock_s3.list_objects_v2.assert_called_once_with(Bucket='test-bucket', Prefix='logs/')
    
    def test_list_s3_objects_missing_bucket(self):
        """Test list handler with missing bucket parameter."""
        event = {
            'queryStringParameters': {}
        }
        
        response = lambda_api.list_s3_objects(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'Missing required parameter'
    
    @patch('lambda_api.s3_client')
    def test_list_s3_objects_empty_bucket(self, mock_s3):
        """Test list handler with empty bucket."""
        mock_s3.list_objects_v2.return_value = {}
        
        event = {
            'queryStringParameters': {
                'bucket': 'empty-bucket'
            }
        }
        
        response = lambda_api.list_s3_objects(event, None)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['object_count'] == 0
        assert body['objects'] == []
    
    @patch('lambda_api.s3_client')
    def test_list_s3_objects_bucket_not_found(self, mock_s3):
        """Test list handler when bucket doesn't exist."""
        error_response = {'Error': {'Code': 'NoSuchBucket'}}
        mock_s3.list_objects_v2.side_effect = ClientError(error_response, 'ListObjectsV2')
        mock_s3.exceptions.NoSuchBucket = ClientError
        
        event = {
            'queryStringParameters': {
                'bucket': 'nonexistent-bucket'
            }
        }
        
        response = lambda_api.list_s3_objects(event, None)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['error'] == 'Internal server error'


class TestCreateResponse:
    """Test cases for the create_response helper function."""
    
    def test_create_response_200(self):
        """Test response creation with 200 status."""
        body = {'message': 'Success', 'data': 'test'}
        response = lambda_api.create_response(200, body)
        
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert json.loads(response['body']) == body
    
    def test_create_response_400(self):
        """Test response creation with 400 status."""
        body = {'error': 'Bad Request', 'message': 'Invalid input'}
        response = lambda_api.create_response(400, body)
        
        assert response['statusCode'] == 400
        assert json.loads(response['body']) == body
    
    def test_create_response_500(self):
        """Test response creation with 500 status."""
        body = {'error': 'Internal Server Error', 'message': 'Something went wrong'}
        response = lambda_api.create_response(500, body)
        
        assert response['statusCode'] == 500
        assert json.loads(response['body']) == body


class TestIntegration:
    """Integration tests."""
    
    @patch('lambda_api.s3_client')
    def test_full_workflow_read_object(self, mock_s3):
        """Test complete workflow of reading an S3 object."""
        mock_body = MagicMock()
        mock_body.read.return_value = b'{"key": "value"}'
        mock_s3.get_object.return_value = {
            'Body': mock_body,
            'ContentType': 'application/json'
        }
        
        event = {
            'queryStringParameters': {
                'bucket': 'my-bucket',
                'key': 'data.json'
            }
        }
        
        response = lambda_api.lambda_handler(event, None)
        body = json.loads(response['body'])
        
        # Verify the flow
        assert response['statusCode'] == 200
        assert '{"key": "value"}' in body['content']
        assert body['bucket'] == 'my-bucket'
        assert body['key'] == 'data.json'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
