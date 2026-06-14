# Docker Setup for AWS Salesforce Lambda

Complete Docker setup for building, testing, and deploying the Salesforce Lambda function.

## Overview

Three Docker configurations are provided:

1. **Dockerfile.lambda** - Production-ready image for AWS ECR
2. **Dockerfile.lambda.dev** - Development image for local testing
3. **docker-compose.yml** - Full stack with Lambda, API Gateway, Prometheus, and Grafana

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (for full stack)
- Salesforce credentials
- Linux/Mac or Windows (with WSL2)

## Quick Start

### 1. Setup Environment

```bash
# Copy example environment file
cp .env.docker.example .env.docker

# Edit with your Salesforce credentials
nano .env.docker  # or use your editor
```

### 2. Build Image

```bash
# Using build script
./docker-build.sh build

# Or using Docker directly
docker build -f Dockerfile.lambda.dev -t salesforce-lambda:latest .
```

### 3. Run Lambda Locally

```bash
# Using build script
./docker-build.sh run

# Or using Docker directly
docker run -d \
  --name salesforce-lambda \
  --env-file .env.docker \
  -p 8080:8080 \
  salesforce-lambda:latest
```

### 4. Test the Endpoint

```bash
# Health check
curl http://localhost:8080/health

# Create account
curl -X POST http://localhost:8080/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "Name": "Test Company",
    "Phone": "555-1234",
    "Industry": "Technology"
  }'
```

## Docker Images

### Production Image (Dockerfile.lambda)

Minimal production image using AWS Lambda base.

**Build:**
```bash
docker build -f Dockerfile.lambda -t salesforce-lambda:prod .
```

**Features:**
- AWS Lambda Python 3.11 base image
- Minimal dependencies
- Optimized for AWS ECR

### Development Image (Dockerfile.lambda.dev)

Full-featured development image for local testing.

**Build:**
```bash
docker build -f Dockerfile.lambda.dev -t salesforce-lambda:dev .
```

**Features:**
- AWS Lambda base image
- Development tools (curl, wget, git)
- Health checks
- RIC (Runtime Interface Client) for local testing
- Volume mounting for hot reload

## Docker Compose Stack

Full stack with monitoring and local API Gateway emulation.

### Services

| Service | Port | Purpose |
|---------|------|---------|
| salesforce-lambda | 8080 | Lambda function |
| localstack | 4566 | API Gateway emulation |
| prometheus | 9090 | Metrics collection |
| grafana | 3000 | Metrics visualization |

### Start Stack

```bash
# Using build script
./docker-build.sh compose

# Or using Docker Compose directly
docker-compose up -d
```

### Access Services

```bash
# Lambda health check
curl http://localhost:8080/health

# Prometheus metrics
open http://localhost:9090

# Grafana dashboards
open http://localhost:3000
# Login: admin/admin
```

### Stop Stack

```bash
./docker-build.sh down
# or
docker-compose down
```

## Commands

### Using Build Script

```bash
# Build image
./docker-build.sh build

# Run in container
./docker-build.sh run

# Start full stack
./docker-build.sh compose

# Stop container
./docker-build.sh stop

# Stop compose stack
./docker-build.sh down

# View logs
./docker-build.sh logs

# Test endpoints
./docker-build.sh test

# Push to registry
REGISTRY=docker.io/username ./docker-build.sh push
```

### Direct Docker Commands

```bash
# Build
docker build -f Dockerfile.lambda.dev -t salesforce-lambda:latest .

# Run
docker run -d \
  --name salesforce-lambda \
  --env-file .env.docker \
  -p 8080:8080 \
  salesforce-lambda:latest

# Logs
docker logs -f salesforce-lambda

# Stop
docker stop salesforce-lambda
docker rm salesforce-lambda

# Interactive shell
docker exec -it salesforce-lambda /bin/bash
```

## Environment Configuration

### .env.docker File

```env
SALESFORCE_INSTANCE_URL=https://your-instance.salesforce.com
SALESFORCE_CLIENT_ID=your_client_id
SALESFORCE_CLIENT_SECRET=your_client_secret
SALESFORCE_USERNAME=your_username@example.com
SALESFORCE_PASSWORD=your_password
SALESFORCE_SECURITY_TOKEN=your_token

LOG_LEVEL=INFO
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
```

### Environment Variables in docker-compose.yml

All environment variables are sourced from `.env.docker` file. You can override specific values:

```bash
docker-compose -e SALESFORCE_INSTANCE_URL=... up -d
```

## Testing

### Health Check

```bash
curl http://localhost:8080/health
```

### Create Account

```bash
curl -X POST http://localhost:8080/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "Name": "Acme Corporation",
    "Phone": "555-1234",
    "Website": "https://acme.com",
    "Industry": "Technology",
    "BillingCity": "San Francisco",
    "BillingCountry": "USA"
  }'
```

### Execute SOQL Query

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "soql": "SELECT Id, Name FROM Account LIMIT 5"
  }'
```

### Run Pytest Tests

```bash
# Inside container
docker exec salesforce-lambda python -m pytest test_aws_salesforce_lambda.py -v

# Or mount test files
docker run -it \
  --env-file .env.docker \
  -v $(pwd)/src:/var/task:ro \
  salesforce-lambda:latest \
  python -m pytest test_aws_salesforce_lambda.py -v
```

## Volumes & Mounts

### Development Hot Reload

Mount source code for live code changes:

```bash
docker run -d \
  --name salesforce-lambda \
  --env-file .env.docker \
  -p 8080:8080 \
  -v $(pwd)/src:/var/task:ro \
  salesforce-lambda:latest
```

### Logs Volume

Persist container logs:

```bash
docker run -d \
  --name salesforce-lambda \
  --env-file .env.docker \
  -p 8080:8080 \
  -v lambda-logs:/var/log \
  salesforce-lambda:latest
```

## Networking

### Docker Network Bridge

Connect multiple containers:

```bash
# Create network
docker network create salesforce-network

# Run containers on network
docker run -d \
  --name salesforce-lambda \
  --network salesforce-network \
  --env-file .env.docker \
  -p 8080:8080 \
  salesforce-lambda:latest
```

### Access Between Containers

```bash
# From another container, use service name as hostname
docker exec my-container curl http://salesforce-lambda:8080/health
```

## Performance Optimization

### Memory & CPU Limits

```bash
docker run -d \
  --memory=512m \
  --cpus=0.5 \
  --name salesforce-lambda \
  --env-file .env.docker \
  -p 8080:8080 \
  salesforce-lambda:latest
```

### Layer Caching

Dockerfile is optimized for layer caching:

```dockerfile
# Layers are cached by order of change frequency
COPY requirements.txt  # Rarely changes
COPY source code      # Often changes
```

### Build Without Cache

```bash
docker build --no-cache -f Dockerfile.lambda.dev -t salesforce-lambda:latest .
```

## Registry & ECR

### Push to AWS ECR

```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag salesforce-lambda:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/salesforce-lambda:latest

# Push
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/salesforce-lambda:latest
```

### Using Build Script

```bash
REGISTRY=123456789012.dkr.ecr.us-east-1.amazonaws.com \
IMAGE_TAG=latest \
./docker-build.sh push
```

## Debugging

### Interactive Shell

```bash
docker exec -it salesforce-lambda /bin/bash
```

### View Logs

```bash
# Follow logs
docker logs -f salesforce-lambda

# Last 100 lines
docker logs --tail 100 salesforce-lambda

# With timestamps
docker logs --timestamps salesforce-lambda
```

### Health Status

```bash
docker ps --filter "name=salesforce-lambda"
docker inspect salesforce-lambda | grep -A 5 Health
```

### Port Conflicts

```bash
# Find what's using port 8080
lsof -i :8080
# or
netstat -ano | findstr :8080
```

## Troubleshooting

### Image Won't Build

Check Docker daemon is running:
```bash
docker ps
```

Clear Docker cache:
```bash
docker system prune -a
```

### Container Won't Start

Check logs:
```bash
docker logs salesforce-lambda
```

Verify environment variables:
```bash
docker inspect salesforce-lambda | grep -A 10 Env
```

### Lambda Handler Errors

Check handler is correct:
```bash
# Should be: aws_salesforce_lambda.router
docker exec salesforce-lambda python -c "import aws_salesforce_lambda; print(aws_salesforce_lambda.router)"
```

### Network Issues

Test connectivity:
```bash
docker exec salesforce-lambda curl http://localhost:8080/health
```

### Salesforce Authentication Fails

Verify credentials in `.env.docker`:
```bash
docker exec salesforce-lambda env | grep SALESFORCE
```

## Security Best Practices

### Environment Variables

Never commit `.env.docker` to version control:
```bash
echo ".env.docker" >> .gitignore
```

Use AWS Secrets Manager for production:
```bash
docker run -d \
  --name salesforce-lambda \
  -e AWS_ROLE_ARN=arn:aws:iam::... \
  -p 8080:8080 \
  salesforce-lambda:latest
```

### Image Scanning

Scan for vulnerabilities:
```bash
docker scan salesforce-lambda:latest
```

### User Permissions

Run as non-root in production:
```dockerfile
RUN useradd -m -u 1000 lambda
USER lambda
```

## Monitoring

### Prometheus Metrics

Metrics available at `http://localhost:9090`

**Important metrics:**
- `aws_lambda_duration_seconds` - Function duration
- `aws_lambda_invocations_total` - Total invocations
- `aws_lambda_errors_total` - Total errors

### Grafana Dashboards

Access at `http://localhost:3000`

Create dashboards using Prometheus metrics.

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Build and Push Docker Image
  run: |
    docker build -f Dockerfile.lambda -t $REGISTRY/salesforce-lambda:${{ github.sha }} .
    docker push $REGISTRY/salesforce-lambda:${{ github.sha }}
```

### GitLab CI Example

```yaml
build:
  image: docker:latest
  script:
    - docker build -f Dockerfile.lambda -t $REGISTRY/salesforce-lambda:$CI_COMMIT_SHA .
    - docker push $REGISTRY/salesforce-lambda:$CI_COMMIT_SHA
```

## Production Deployment

### AWS Lambda

```bash
# Create ECR repository
aws ecr create-repository --repository-name salesforce-lambda

# Build and push
docker build -f Dockerfile.lambda -t 123456789012.dkr.ecr.us-east-1.amazonaws.com/salesforce-lambda:latest .
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/salesforce-lambda:latest

# Create Lambda function from image
aws lambda create-function \
  --function-name salesforce-api \
  --role arn:aws:iam::123456789012:role/lambda-role \
  --code ImageUri=123456789012.dkr.ecr.us-east-1.amazonaws.com/salesforce-lambda:latest \
  --timeout 30 \
  --memory-size 512
```

### ECS/Fargate

```bash
# Push to ECR (same as above)

# Create ECS cluster and service
aws ecs create-cluster --cluster-name salesforce
aws ecs register-task-definition --cli-input-json file://task-definition.json
aws ecs create-service --cluster salesforce --service-name api --task-definition salesforce-api
```

## Cleanup

### Remove Container

```bash
docker rm -f salesforce-lambda
```

### Remove Image

```bash
docker rmi salesforce-lambda:latest
```

### Remove All

```bash
docker system prune -a
```

## Support & Resources

- [Docker Documentation](https://docs.docker.com/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)

## License

Docker configuration is provided as-is for use with AWS Lambda and Salesforce.
