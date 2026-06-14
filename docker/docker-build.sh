#!/bin/bash
# Docker build and deployment script for Salesforce Lambda

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="${IMAGE_NAME:-salesforce-lambda}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-}"
CONTAINER_NAME="${CONTAINER_NAME:-salesforce-lambda}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Commands
build_image() {
    print_header "Building Docker Image"
    
    FULL_IMAGE_NAME="${REGISTRY}${REGISTRY:+/}${IMAGE_NAME}:${IMAGE_TAG}"
    
    echo "Image: $FULL_IMAGE_NAME"
    
    docker build \
        -f Dockerfile.lambda.dev \
        -t "$FULL_IMAGE_NAME" \
        .
    
    print_success "Image built: $FULL_IMAGE_NAME"
}

run_local() {
    print_header "Running Lambda Locally"
    
    # Check if .env.docker exists
    if [ ! -f ".env.docker" ]; then
        print_warning ".env.docker not found. Copying from example..."
        cp .env.docker.example .env.docker
        print_warning "Please edit .env.docker with your Salesforce credentials"
        exit 1
    fi
    
    FULL_IMAGE_NAME="${REGISTRY}${REGISTRY:+/}${IMAGE_NAME}:${IMAGE_TAG}"
    
    # Check if container is already running
    if docker ps | grep -q "$CONTAINER_NAME"; then
        print_warning "Container $CONTAINER_NAME is already running"
        print_warning "Stopping existing container..."
        docker stop "$CONTAINER_NAME"
    fi
    
    # Remove existing container if it exists
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    
    # Run the container
    docker run -d \
        --name "$CONTAINER_NAME" \
        --env-file .env.docker \
        -p 8080:8080 \
        "$FULL_IMAGE_NAME"
    
    print_success "Container started: $CONTAINER_NAME"
    print_success "Lambda endpoint: http://localhost:8080"
    print_success "View logs: docker logs -f $CONTAINER_NAME"
}

run_compose() {
    print_header "Starting Docker Compose Stack"
    
    if [ ! -f ".env.docker" ]; then
        print_warning ".env.docker not found. Copying from example..."
        cp .env.docker.example .env.docker
        print_warning "Please edit .env.docker with your Salesforce credentials"
        exit 1
    fi
    
    docker-compose up -d
    
    print_success "Docker Compose stack started"
    print_success "Lambda endpoint: http://localhost:8080"
    print_success "View logs: docker-compose logs -f"
}

stop_container() {
    print_header "Stopping Container"
    
    if docker ps | grep -q "$CONTAINER_NAME"; then
        docker stop "$CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
        print_success "Container stopped and removed"
    else
        print_warning "Container $CONTAINER_NAME is not running"
    fi
}

stop_compose() {
    print_header "Stopping Docker Compose Stack"
    
    docker-compose down
    
    print_success "Docker Compose stack stopped"
}

test_lambda() {
    print_header "Testing Lambda Endpoint"
    
    print_success "Testing health check..."
    curl -s http://localhost:8080/health | jq . || echo "Health check failed"
    
    print_success "Testing create account..."
    curl -X POST http://localhost:8080/accounts \
        -H "Content-Type: application/json" \
        -d '{
            "Name": "Test Company",
            "Phone": "555-1234",
            "Industry": "Technology"
        }' | jq .
}

view_logs() {
    print_header "Lambda Logs"
    
    docker logs -f "$CONTAINER_NAME"
}

push_image() {
    print_header "Pushing Image to Registry"
    
    if [ -z "$REGISTRY" ]; then
        print_error "REGISTRY environment variable not set"
        echo "Usage: REGISTRY=docker.io/your-username push"
        exit 1
    fi
    
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    print_success "Pushing $FULL_IMAGE_NAME..."
    docker push "$FULL_IMAGE_NAME"
    
    print_success "Image pushed successfully"
}

show_usage() {
    cat << EOF
Docker build and deployment script for Salesforce Lambda

Usage: $0 [command]

Commands:
  build       Build Docker image
  run         Run Lambda in Docker container
  compose     Start full stack with Docker Compose
  stop        Stop running container
  down        Stop Docker Compose stack
  test        Test Lambda endpoint
  logs        View Lambda logs
  push        Push image to registry (requires REGISTRY env var)

Environment Variables:
  IMAGE_NAME      Docker image name (default: salesforce-lambda)
  IMAGE_TAG       Docker image tag (default: latest)
  REGISTRY        Docker registry (optional)
  CONTAINER_NAME  Container name (default: salesforce-lambda)

Examples:
  # Build image
  $0 build

  # Run locally
  $0 run

  # Run with Docker Compose
  $0 compose

  # Test endpoint
  $0 test

  # Push to registry
  REGISTRY=docker.io/your-username $0 push

Prerequisites:
  - Docker installed and running
  - .env.docker file with Salesforce credentials
  - Docker Compose (for compose command)

EOF
}

# Main
case "$1" in
    build)
        build_image
        ;;
    run)
        build_image
        run_local
        ;;
    compose)
        build_image
        run_compose
        ;;
    stop)
        stop_container
        ;;
    down)
        stop_compose
        ;;
    test)
        test_lambda
        ;;
    logs)
        view_logs
        ;;
    push)
        push_image
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
