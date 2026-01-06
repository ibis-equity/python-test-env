# Python API Project

A modern Python API project with FastAPI, AWS Lambda integration, and comprehensive testing.

## Features

- **FastAPI**: Modern, fast web framework for building APIs
- **Lambda Functions**: AWS Lambda handlers for Kinesis streams and S3 operations
- **Pandas Integration**: Data processing with Pandas and Parquet format
- **Glue Catalog**: Automatic table schema management
- **Docker Support**: Multi-stage Dockerfile and docker-compose setup
- **Comprehensive Testing**: Pytest with mocking for AWS services
- **CI/CD**: GitHub Actions workflows for testing, linting, and Docker builds

## Project Structure

```
├── api/
│   ├── main.py                 # FastAPI application
│   ├── lambda_handler.py       # S3 read/list Lambda
│   ├── lambda_datastream.py    # Kinesis processing Lambda
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile             # Docker image definition
│   ├── docker-compose.yml     # Local development setup
│   └── .dockerignore          # Docker build exclusions
├── .github/
│   ├── workflows/
│   │   ├── tests.yml          # Unit test CI/CD
│   │   ├── quality.yml        # Code quality checks
│   │   └── docker.yml         # Docker build pipeline
│   └── ISSUE_TEMPLATE/        # GitHub issue templates
└── requirements.txt           # Root dependencies
```

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run API
python -m uvicorn main:app --reload

# Run tests
pytest -v

# Run with Docker Compose
docker-compose up
```

### API Endpoints

- `GET /` - Welcome message
- `GET /api/items/{item_id}` - Get item by ID
- `POST /api/items/` - Create item
- `GET /api/health` - Health check
- `GET /docs` - Interactive API documentation

### Lambda Functions

#### lambda_handler.py
- Read objects from S3 buckets
- List objects in S3 with optional prefix filtering
- Query params: `bucket`, `key`, `prefix`

#### lambda_datastream.py
- Process Kinesis Data Streams records
- Write data to S3 in Parquet format
- Auto-update AWS Glue table schema
- Environment variables: `S3_BUCKET`, `GLUE_DATABASE`, `GLUE_TABLE`

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_lambda_api.py -v
pytest test_lambda_datastream.py -v
```

## Docker

```bash
# Build image
docker build -t python-api:latest ./api

# Run container
docker run -p 8000:8000 python-api:latest

# With Docker Compose (includes LocalStack for AWS testing)
docker-compose up
```

## AWS Configuration

### Lambda Execution Role Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket",
        "s3:PutObject"
      ],
      "Resource": ["arn:aws:s3:::*/*", "arn:aws:s3:::*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:GetRecords",
        "kinesis:GetShardIterator",
        "kinesis:DescribeStream",
        "kinesis:ListStreams"
      ],
      "Resource": "arn:aws:kinesis:*:*:stream/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:CreateTable",
        "glue:UpdateTable",
        "glue:GetTable"
      ],
      "Resource": "arn:aws:glue:*:*:catalog/database/*"
    }
  ]
}
```

## Environment Variables

```bash
# API
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Lambda Functions
S3_BUCKET=your-bucket-name
S3_PREFIX=data
GLUE_DATABASE=your_database
GLUE_TABLE=your_table
```

## CI/CD Workflows

### tests.yml
- Runs on push and pull requests
- Tests across Python 3.11, 3.12, 3.13
- Uploads coverage to Codecov

### quality.yml
- Code formatting checks (black, isort)
- Linting (flake8, pylint)
- Type checking (mypy)

### docker.yml
- Builds and pushes Docker image
- Uses Docker layer caching
- Semantic versioning with tags

## Contributing

See GitHub issue templates for bug reports and feature requests.

## License

[Your License Here]

## Support

For issues and questions, please open a GitHub issue.
