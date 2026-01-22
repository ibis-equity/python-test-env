@echo off
REM Terraform Deployment Script for Salesforce API (Windows)
REM Usage: deploy.bat [init|plan|apply|destroy]

setlocal enabledelayedexpansion

set ACTION=%1
if "%ACTION%"=="" set ACTION=plan

set ENVIRONMENT=%2
if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev

REM Color codes (using echo with special characters)
set GREEN=[92m
set RED=[91m
set YELLOW=[93m
set BLUE=[94m
set NC=[0m

REM Functions
:check_prerequisites
cls
echo.
echo ========================================
echo Checking Prerequisites
echo ========================================
echo.

REM Check Terraform
where terraform >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [91mError: Terraform is not installed[0m
    echo Please install Terraform 1.0 or later
    exit /b 1
)
echo [92mOK: Terraform found[0m

REM Check AWS CLI
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [91mError: AWS CLI is not installed[0m
    echo Please install AWS CLI
    exit /b 1
)
echo [92mOK: AWS CLI found[0m

REM Check AWS credentials
aws sts get-caller-identity >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [91mError: AWS credentials not configured[0m
    echo Please run: aws configure
    exit /b 1
)
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
echo [92mOK: AWS Account: !ACCOUNT_ID![0m

REM Check for tfvars file
if not exist "terraform.tfvars" (
    echo [93mWarning: terraform.tfvars not found[0m
    echo Copying from terraform.tfvars.example...
    copy terraform.tfvars.example terraform.tfvars
    echo [93mPlease edit terraform.tfvars with your values before deploying[0m
    exit /b 1
)
echo [92mOK: terraform.tfvars found[0m
echo.
goto :eof

:terraform_init
echo.
echo ========================================
echo Initializing Terraform
echo ========================================
echo.
call terraform init
if %ERRORLEVEL% NEQ 0 (
    echo [91mError: Terraform init failed[0m
    exit /b 1
)
echo [92mOK: Terraform initialized[0m
echo.
goto :eof

:terraform_plan
echo.
echo ========================================
echo Planning Terraform Changes
echo ========================================
echo.
call terraform plan -out=tfplan
if %ERRORLEVEL% NEQ 0 (
    echo [91mError: Terraform plan failed[0m
    exit /b 1
)
echo [92mOK: Terraform plan complete[0m
echo Review the changes above before applying.
echo.
goto :eof

:terraform_apply
echo.
echo ========================================
echo Applying Terraform Changes
echo ========================================
echo.
if not exist "tfplan" (
    echo [91mError: No plan file found[0m
    echo Please run: deploy.bat plan
    exit /b 1
)
echo [93mWarning: About to create/modify AWS resources[0m
set /p CONFIRM="Are you sure? (yes/no): "
if /i not "%CONFIRM%"=="yes" (
    echo [93mCancelled[0m
    exit /b 1
)
call terraform apply tfplan
if %ERRORLEVEL% NEQ 0 (
    echo [91mError: Terraform apply failed[0m
    exit /b 1
)
echo [92mOK: Terraform apply complete[0m
echo.
echo ========================================
echo Deployment Complete!
echo ========================================
call terraform output
echo.
call terraform output -json > deployment-outputs.json
echo [92mOK: Outputs saved to deployment-outputs.json[0m
echo.
goto :eof

:terraform_destroy
echo.
echo ========================================
echo Destroying Terraform Resources
echo ========================================
echo.
echo [91m!!! WARNING: This will delete all AWS resources !!!
echo [91mIncluding Lambda functions, API Gateway, and CloudWatch resources[0m
echo.
set /p CONFIRM="Type 'destroy' to confirm: "
if /i not "%CONFIRM%"=="destroy" (
    echo [93mCancelled[0m
    exit /b 1
)
call terraform destroy
if %ERRORLEVEL% NEQ 0 (
    echo [91mError: Terraform destroy failed[0m
    exit /b 1
)
echo [92mOK: Resources destroyed[0m
echo.
goto :eof

:show_usage
echo.
echo Terraform Deployment Script for Salesforce API
echo.
echo Usage: %0 [command]
echo.
echo Commands:
echo   init      Initialize Terraform (required first step)
echo   plan      Plan Terraform changes (review before apply)
echo   apply     Apply Terraform changes
echo   destroy   Destroy all AWS resources
echo.
echo Examples:
echo   deploy.bat init
echo   deploy.bat plan
echo   deploy.bat apply
echo   deploy.bat destroy
echo.
echo Prerequisites:
echo   - Terraform ^>= 1.0
echo   - AWS CLI configured with credentials
echo   - terraform.tfvars file with your configuration
echo.
goto :eof

REM Main execution
if "%ACTION%"=="init" (
    call :check_prerequisites
    call :terraform_init
) else if "%ACTION%"=="plan" (
    call :check_prerequisites
    call :terraform_init
    call :terraform_plan
) else if "%ACTION%"=="apply" (
    call :check_prerequisites
    call :terraform_init
    call :terraform_apply
) else if "%ACTION%"=="destroy" (
    call :check_prerequisites
    call :terraform_destroy
) else if "%ACTION%"=="help" (
    call :show_usage
) else (
    echo [91mUnknown command: %ACTION%[0m
    call :show_usage
    exit /b 1
)

endlocal
