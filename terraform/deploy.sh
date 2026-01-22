#!/bin/bash
# Terraform Deployment Script for Salesforce API
# Usage: ./deploy.sh [init|plan|apply|destroy] [environment]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${2:-dev}"
ACTION="${1:-plan}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
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

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install Terraform 1.0 or later."
        exit 1
    fi
    print_success "Terraform found: $(terraform version -json | jq -r '.terraform_version')"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install AWS CLI."
        exit 1
    fi
    print_success "AWS CLI found"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run: aws configure"
        exit 1
    fi
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    REGION=$(aws configure get region)
    print_success "AWS Account: $ACCOUNT_ID"
    print_success "AWS Region: $REGION"
    
    # Check for tfvars file
    TFVARS_FILE="terraform.tfvars"
    if [ ! -f "$TFVARS_FILE" ]; then
        print_warning "terraform.tfvars not found. Copying from example..."
        cp terraform.tfvars.example "$TFVARS_FILE"
        print_warning "Please edit $TFVARS_FILE with your values before deploying."
        exit 1
    fi
    print_success "terraform.tfvars found"
}

terraform_init() {
    print_header "Initializing Terraform"
    
    cd "$SCRIPT_DIR"
    terraform init
    
    print_success "Terraform initialized"
}

terraform_plan() {
    print_header "Planning Terraform Changes (Environment: $ENVIRONMENT)"
    
    cd "$SCRIPT_DIR"
    terraform plan -out=tfplan
    
    print_success "Terraform plan complete. Review the changes above."
}

terraform_apply() {
    print_header "Applying Terraform Changes (Environment: $ENVIRONMENT)"
    
    cd "$SCRIPT_DIR"
    
    if [ ! -f tfplan ]; then
        print_error "No plan file found. Run 'deploy.sh plan' first."
        exit 1
    fi
    
    print_warning "About to apply Terraform changes. This will create/modify AWS resources."
    read -p "Are you sure? (yes/no): " -r
    echo
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        terraform apply tfplan
        
        print_header "Deployment Complete!"
        print_success "Terraform apply complete"
        
        # Output important values
        print_header "Important Outputs"
        terraform output -json | jq -r 'to_entries[] | "\(.key): \(.value.value)"'
        
        # Save outputs to file
        terraform output -json > deployment-outputs.json
        print_success "Outputs saved to deployment-outputs.json"
    else
        print_warning "Deployment cancelled"
    fi
}

terraform_destroy() {
    print_header "Destroying Terraform Resources (Environment: $ENVIRONMENT)"
    
    cd "$SCRIPT_DIR"
    
    print_warning "About to destroy all AWS resources created by this module!"
    print_warning "This includes Lambda functions, API Gateway, and CloudWatch resources."
    read -p "Are you absolutely sure? Type 'destroy' to confirm: " -r
    echo
    if [[ $REPLY == "destroy" ]]; then
        terraform destroy
        print_success "Resources destroyed"
    else
        print_warning "Destruction cancelled"
    fi
}

show_usage() {
    cat << EOF
Terraform Deployment Script for Salesforce API

Usage: $0 [command] [environment]

Commands:
  init      Initialize Terraform (required first step)
  plan      Plan Terraform changes (review before apply)
  apply     Apply Terraform changes (creates/modifies AWS resources)
  destroy   Destroy all Terraform resources

Examples:
  $0 init dev
  $0 plan dev
  $0 apply dev
  $0 destroy dev

Default environment: dev

Prerequisites:
  - Terraform >= 1.0
  - AWS CLI configured with credentials
  - terraform.tfvars file with configuration

EOF
}

# Main execution
case "$ACTION" in
    init)
        check_prerequisites
        terraform_init
        ;;
    plan)
        check_prerequisites
        terraform_init
        terraform_plan
        ;;
    apply)
        check_prerequisites
        terraform_init
        terraform_apply
        ;;
    destroy)
        check_prerequisites
        terraform_destroy
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        print_error "Unknown command: $ACTION"
        show_usage
        exit 1
        ;;
esac
