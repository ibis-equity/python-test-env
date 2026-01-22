variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "salesforce-api"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "function_name" {
  description = "Lambda function name"
  type        = string
  default     = "salesforce-api"
}

variable "lambda_source_dir" {
  description = "Directory containing Lambda source code"
  type        = string
  default     = "../src"
}

variable "lambda_handler" {
  description = "Lambda handler function"
  type        = string
  default     = "aws_salesforce_lambda.router"
}

variable "lambda_runtime" {
  description = "Lambda runtime environment"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 512

  validation {
    condition     = var.lambda_memory >= 128 && var.lambda_memory <= 10240
    error_message = "Memory must be between 128 and 10240 MB."
  }
}

variable "lambda_layers" {
  description = "List of Lambda layer ARNs"
  type        = list(string)
  default     = []
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "log_level" {
  description = "Log level (DEBUG, INFO, WARNING, ERROR)"
  type        = string
  default     = "INFO"
}

variable "environment_variables" {
  description = "Environment variables for Lambda function"
  type        = map(string)
  sensitive   = true
  default = {
    SALESFORCE_INSTANCE_URL  = ""
    SALESFORCE_CLIENT_ID     = ""
    SALESFORCE_CLIENT_SECRET = ""
    SALESFORCE_USERNAME      = ""
    SALESFORCE_PASSWORD      = ""
  }
}

variable "api_stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "dev"
}

variable "cors_allow_origins" {
  description = "CORS allowed origins for API Gateway"
  type        = list(string)
  default     = ["*"]
}

variable "error_threshold" {
  description = "CloudWatch alarm threshold for Lambda errors"
  type        = number
  default     = 5
}

variable "duration_threshold" {
  description = "CloudWatch alarm threshold for Lambda duration (milliseconds)"
  type        = number
  default     = 25000
}

variable "enable_api_logging" {
  description = "Enable API Gateway request/response logging"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}
