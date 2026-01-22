#!/bin/bash
# run-tests-docker.sh
# Docker test runner for FastAPI with sample dataset

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
BUILD=false
NO_CACHE=false
INTERACTIVE=false
FOLLOW_LOGS=false
CLEAN=false
FILTER=""

# Helper functions
log_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

show_banner() {
    echo -e "${CYAN}"
    cat << "EOF"
╔════════════════════════════════════════════════════════════════╗
║                   DOCKER TEST RUNNER                          ║
║              FastAPI + Sample Dataset Testing                 ║
╚════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

verify_docker() {
    log_info "Verifying Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    DOCKER_VERSION=$(docker --version)
    COMPOSE_VERSION=$(docker-compose --version)
    
    log_success "$DOCKER_VERSION"
    log_success "$COMPOSE_VERSION"
}

build_test_image() {
    log_info "Building test image..."
    
    CACHE_ARG=""
    if [ "$NO_CACHE" = true ]; then
        CACHE_ARG="--no-cache"
    fi
    
    docker-compose -f docker-compose.test.yml build $CACHE_ARG test-runner
    
    if [ $? -ne 0 ]; then
        log_error "Failed to build image"
        exit 1
    fi
    
    log_success "Image built successfully"
}

clean_test_containers() {
    log_info "Cleaning up test containers and volumes..."
    
    docker-compose -f docker-compose.test.yml down -v
    
    log_success "Cleanup complete"
}

run_all_tests() {
    log_info "Running all tests with coverage..."
    
    if [ "$FOLLOW_LOGS" = true ]; then
        docker-compose -f docker-compose.test.yml run --rm test-runner
    else
        docker-compose -f docker-compose.test.yml up --abort-on-container-exit test-runner
    fi
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_success "All tests passed!"
    else
        log_error "Tests failed (exit code: $EXIT_CODE)"
    fi
    
    return $EXIT_CODE
}

run_integration_tests() {
    log_info "Running integration tests..."
    
    docker-compose -f docker-compose.test.yml --profile integration up --abort-on-container-exit test-integration
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_success "Integration tests passed!"
    else
        log_error "Integration tests failed (exit code: $EXIT_CODE)"
    fi
    
    return $EXIT_CODE
}

run_performance_tests() {
    log_info "Running performance tests..."
    
    docker-compose -f docker-compose.test.yml --profile performance up --abort-on-container-exit test-performance
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_success "Performance tests completed!"
    else
        log_error "Performance tests failed (exit code: $EXIT_CODE)"
    fi
    
    return $EXIT_CODE
}

run_sample_data_tests() {
    log_info "Running sample data validation tests..."
    
    docker-compose -f docker-compose.test.yml --profile sample up --abort-on-container-exit test-sample-data
    
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_success "Sample data tests passed!"
    else
        log_error "Sample data tests failed (exit code: $EXIT_CODE)"
    fi
    
    return $EXIT_CODE
}

show_coverage_report() {
    log_info "Coverage Report"
    
    if [ -f "test-results/coverage/index.html" ]; then
        log_success "Coverage report generated at: test-results/coverage/index.html"
        
        if [ "$INTERACTIVE" = true ]; then
            log_info "Opening coverage report in browser..."
            if command -v xdg-open &> /dev/null; then
                xdg-open "test-results/coverage/index.html"
            elif command -v open &> /dev/null; then
                open "test-results/coverage/index.html"
            else
                log_warn "Could not open browser"
            fi
        fi
    else
        log_warn "Coverage report not found"
    fi
}

show_test_results() {
    if [ -d "test-results" ]; then
        log_info "Test Results Directory:"
        find test-results -type f | while read file; do
            echo "   $file"
        done
    fi
}

show_help() {
    cat << EOF
${CYAN}USAGE:${NC}
    ./run-tests-docker.sh [OPTIONS]

${CYAN}OPTIONS:${NC}
    -t, --test-type {all|integration|performance|sample|unit}
        Type of tests to run (default: all)
        
    -b, --build
        Build the Docker image before running tests
        
    --no-cache
        Build without using cached layers
        
    -i, --interactive
        Open coverage report in browser after tests
        
    -f, --follow
        Follow Docker logs during test execution
        
    -c, --clean
        Remove test containers and volumes
        
    --filter <pattern>
        Run only tests matching the filter pattern
        
    -h, --help
        Show this help message

${CYAN}EXAMPLES:${NC}
    # Run all tests
    ./run-tests-docker.sh
    
    # Build and run all tests
    ./run-tests-docker.sh --build
    
    # Run only integration tests
    ./run-tests-docker.sh --test-type integration
    
    # Run tests with coverage report in browser
    ./run-tests-docker.sh --interactive
    
    # Clean up test containers
    ./run-tests-docker.sh --clean

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--test-type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -b|--build)
            BUILD=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        -i|--interactive)
            INTERACTIVE=true
            shift
            ;;
        -f|--follow)
            FOLLOW_LOGS=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        --filter)
            FILTER="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    show_banner
    
    if [ "$CLEAN" = true ]; then
        clean_test_containers
        exit 0
    fi
    
    verify_docker
    
    if [ "$BUILD" = true ]; then
        build_test_image
    fi
    
    EXIT_CODE=0
    
    case $TEST_TYPE in
        all)
            run_all_tests || EXIT_CODE=$?
            ;;
        integration)
            run_integration_tests || EXIT_CODE=$?
            ;;
        performance)
            run_performance_tests || EXIT_CODE=$?
            ;;
        sample)
            run_sample_data_tests || EXIT_CODE=$?
            ;;
        unit)
            run_all_tests || EXIT_CODE=$?
            ;;
        *)
            log_error "Unknown test type: $TEST_TYPE"
            exit 1
            ;;
    esac
    
    show_test_results
    show_coverage_report
    
    echo ""
    
    if [ $EXIT_CODE -eq 0 ]; then
        log_success "Testing completed successfully!"
    else
        log_error "Testing failed"
    fi
    
    exit $EXIT_CODE
}

main
