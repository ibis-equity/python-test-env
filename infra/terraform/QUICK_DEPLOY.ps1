#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick deployment script for FastAPI to AWS Lambda using Terraform

.DESCRIPTION
    Automates the Terraform deployment process with validation and error handling

.EXAMPLE
    .\QUICK_DEPLOY.ps1
    .\QUICK_DEPLOY.ps1 -Destroy
    .\QUICK_DEPLOY.ps1 -Plan
#>

param(
    [switch]$Plan,
    [switch]$Destroy,
    [switch]$Init,
    [switch]$Validate
)

$ErrorActionPreference = "Stop"
$WarningPreference = "Continue"

function Write-Header {
    param([string]$Message)
    Write-Host "`n" -NoNewline
    Write-Host "╔" + ("═" * 78) + "╗" -ForegroundColor Cyan
    Write-Host "║ $Message".PadRight(79) + "║" -ForegroundColor Cyan
    Write-Host "╚" + ("═" * 78) + "╝" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Blue
}

function Check-Prerequisites {
    Write-Header "Checking Prerequisites"

    # Check Terraform
    try {
        $tfVersion = terraform version
        Write-Success "Terraform installed: $($tfVersion.Split(' ')[1])"
    } catch {
        Write-Error-Custom "Terraform not found. Install from https://www.terraform.io/downloads.html"
        exit 1
    }

    # Check AWS CLI
    try {
        $awsVersion = aws --version
        Write-Success "AWS CLI installed: $awsVersion"
    } catch {
        Write-Error-Custom "AWS CLI not found. Install from https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    }

    # Check AWS Credentials
    try {
        $identity = aws sts get-caller-identity | ConvertFrom-Json
        Write-Success "AWS authenticated as: $($identity.Arn)"
    } catch {
        Write-Error-Custom "AWS credentials not configured. Run 'aws configure'"
        exit 1
    }

    # Check terraform.tfvars
    if (-not (Test-Path "terraform.tfvars")) {
        Write-Info "terraform.tfvars not found. Copying from example..."
        Copy-Item terraform.tfvars.example terraform.tfvars
        Write-Info "Created terraform.tfvars - PLEASE REVIEW AND EDIT IF NEEDED"
        Write-Info "Edit terraform.tfvars with your settings before continuing"
        Read-Host "Press Enter to continue"
    }

    Write-Success "All prerequisites met"
}

function Validate-Configuration {
    Write-Header "Validating Terraform Configuration"

    terraform validate
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Terraform configuration is valid"
    } else {
        Write-Error-Custom "Terraform configuration validation failed"
        exit 1
    }
}

function Format-Configuration {
    Write-Header "Formatting Terraform Files"

    terraform fmt -recursive
    Write-Success "Terraform files formatted"
}

function Initialize-Terraform {
    Write-Header "Initializing Terraform"

    terraform init
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Terraform initialized successfully"
    } else {
        Write-Error-Custom "Terraform initialization failed"
        exit 1
    }
}

function Plan-Deployment {
    Write-Header "Planning Terraform Deployment"

    Write-Info "Generating deployment plan..."
    terraform plan -out=tfplan -no-color

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Deployment plan created: tfplan"
        Write-Info "Review the plan above carefully"
        Write-Info "Run '.\QUICK_DEPLOY.ps1' without -Plan to apply"
    } else {
        Write-Error-Custom "Terraform plan failed"
        exit 1
    }
}

function Apply-Deployment {
    Write-Header "Applying Terraform Configuration"

    if (Test-Path "tfplan") {
        Write-Info "Using existing plan: tfplan"
        $plan = "tfplan"
    } else {
        Write-Info "Creating new plan..."
        terraform plan -out=tfplan
        $plan = "tfplan"
    }

    Write-Info "Review the changes above (resources being created/modified/deleted)"
    Write-Host ""
    $continue = Read-Host "Continue with deployment? (yes/no)"

    if ($continue -ne "yes") {
        Write-Info "Deployment cancelled"
        exit 0
    }

    Write-Info "Applying Terraform configuration (this may take 2-5 minutes)..."
    terraform apply $plan

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Terraform deployment completed successfully!"
        Write-Header "Deployment Outputs"
        terraform output
    } else {
        Write-Error-Custom "Terraform apply failed"
        exit 1
    }
}

function Destroy-Deployment {
    Write-Header "Destroying AWS Resources"

    Write-Info "This will DELETE all AWS resources created by Terraform:"
    Write-Host ""
    terraform plan -destroy
    Write-Host ""

    $confirm = Read-Host "Are you sure you want to destroy? (type 'destroy' to confirm)"

    if ($confirm -ne "destroy") {
        Write-Info "Destruction cancelled"
        exit 0
    }

    Write-Info "Destroying resources (this may take 2-3 minutes)..."
    terraform destroy -auto-approve

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Resources destroyed successfully"
        Write-Info "Cleaning up local files..."
        Remove-Item -Force terraform.tfstate, terraform.tfstate.backup -ErrorAction SilentlyContinue
        Write-Success "Cleanup complete"
    } else {
        Write-Error-Custom "Terraform destroy failed"
        exit 1
    }
}

function Show-Next-Steps {
    Write-Header "Next Steps"

    $endpoint = terraform output -raw api_endpoint 2>/dev/null
    if ($endpoint) {
        Write-Info "API Endpoint: $endpoint"
        Write-Info ""
        Write-Info "Test your API:"
        Write-Host "  # Health check" -ForegroundColor Yellow
        Write-Host "  curl '$endpoint/api/health'" -ForegroundColor Yellow
        Write-Host "  "
        Write-Host "  # Create item" -ForegroundColor Yellow
        Write-Host "  curl -X POST '$endpoint/api/items/' -H 'Content-Type: application/json' -d '{""name"":""Test""}'" -ForegroundColor Yellow
        Write-Host "  "
        Write-Host "  # View all outputs" -ForegroundColor Yellow
        Write-Host "  terraform output" -ForegroundColor Yellow
        Write-Host "  "
        Write-Host "  # View logs" -ForegroundColor Yellow
        Write-Host "  aws logs tail /aws/lambda/python-api-lambda --follow" -ForegroundColor Yellow
    }
}

# Main execution
try {
    Check-Prerequisites

    if ($Init) {
        Initialize-Terraform
        exit 0
    }

    if ($Validate) {
        Validate-Configuration
        Format-Configuration
        exit 0
    }

    Validate-Configuration
    Format-Configuration
    Initialize-Terraform

    if ($Plan) {
        Plan-Deployment
    } elseif ($Destroy) {
        Destroy-Deployment
    } else {
        Plan-Deployment
        Apply-Deployment
        Show-Next-Steps
    }

    Write-Success "Operation completed successfully"
} catch {
    Write-Error-Custom "Script failed: $_"
    exit 1
}
