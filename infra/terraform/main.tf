terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment to use S3 backend
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "salesforce-lambda/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      CreatedAt   = timestamp()
    }
  }
}

# ==================== IAM Role ====================

resource "aws_iam_role" "lambda_role" {
  name              = "${var.function_name}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.function_name}-role"
  }
}

# Basic Lambda execution policy (for logs)
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy for Secrets Manager (optional, for storing Salesforce credentials)
resource "aws_iam_role_policy" "lambda_secrets" {
  name   = "${var.function_name}-secrets-policy"
  role   = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:*:secret:salesforce/*"
      }
    ]
  })
}

# ==================== CloudWatch Log Group ====================

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.function_name}-logs"
  }
}

# ==================== Lambda Function ====================

# Archive the source code
data "archive_file" "lambda_source" {
  type        = "zip"
  source_dir  = var.lambda_source_dir
  output_path = "${path.module}/.lambda_build/${var.function_name}.zip"

  depends_on = [
    # Ensure source files exist
  ]
}

resource "aws_lambda_function" "salesforce_api" {
  filename            = data.archive_file.lambda_source.output_path
  function_name       = var.function_name
  role                = aws_iam_role.lambda_role.arn
  handler             = var.lambda_handler
  runtime             = var.lambda_runtime
  timeout             = var.lambda_timeout
  memory_size         = var.lambda_memory

  source_code_hash = data.archive_file.lambda_source.output_base64sha256

  environment {
    variables = merge(
      var.environment_variables,
      {
        LOG_LEVEL = var.log_level
      }
    )
  }

  layers = var.lambda_layers

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_cloudwatch_log_group.lambda_logs
  ]

  tags = {
    Name = var.function_name
  }
}

# ==================== API Gateway ====================

resource "aws_apigatewayv2_api" "salesforce_api" {
  name          = "${var.function_name}-api"
  protocol_type = "HTTP"
  
  cors_configuration {
    allow_origins = var.cors_allow_origins
    allow_methods = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization", "X-Amz-Date", "X-Api-Key"]
  }

  tags = {
    Name = "${var.function_name}-api"
  }
}

# ==================== Lambda Integration ====================

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.salesforce_api.id
  integration_type = "AWS_PROXY"
  
  integration_method = "POST"
  integration_uri    = aws_lambda_function.salesforce_api.invoke_arn
  
  payload_format_version = "2.0"

  depends_on = [
    aws_lambda_function.salesforce_api
  ]
}

# ==================== API Routes ====================

# Catch-all route for all paths and methods
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "$default"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Specific routes with documentation
resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "GET /health"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "create_account" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "POST /accounts"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "get_account" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "GET /accounts/{account_id}"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "update_account" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "PATCH /accounts/{account_id}"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "delete_account" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "DELETE /accounts/{account_id}"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "create_contact" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "POST /contacts"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "get_contact" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "GET /contacts/{contact_id}"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "update_contact" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "PATCH /contacts/{contact_id}"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "delete_contact" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "DELETE /contacts/{contact_id}"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "create_opportunity" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "POST /opportunities"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "get_opportunity" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "GET /opportunities/{opportunity_id}"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "update_opportunity" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "PATCH /opportunities/{opportunity_id}"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "delete_opportunity" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "DELETE /opportunities/{opportunity_id}"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "query" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "POST /query"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_route" "batch_accounts" {
  api_id    = aws_apigatewayv2_api.salesforce_api.id
  route_key = "POST /batch/accounts"
  
  target = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# ==================== API Stage ====================

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.salesforce_api.id
  name        = var.api_stage_name
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      integrationLatency = "$context.integration.latency"
      userAgent      = "$context.identity.userAgent"
    })
  }

  tags = {
    Name = "${var.function_name}-${var.api_stage_name}"
  }

  depends_on = [aws_cloudwatch_log_group.api_logs]
}

# ==================== API Gateway CloudWatch Logs ====================

resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.function_name}-api-logs"
  }
}

# ==================== Lambda Permission ====================

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.salesforce_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.salesforce_api.execution_arn}/*/*"

  depends_on = [aws_lambda_function.salesforce_api]
}

# ==================== CloudWatch Alarms ====================

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.function_name}-errors"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = var.error_threshold
  alarm_description   = "Alert when Lambda function has errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.salesforce_api.function_name
  }

  tags = {
    Name = "${var.function_name}-errors-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.function_name}-high-duration"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = var.duration_threshold
  alarm_description   = "Alert when Lambda function duration is high"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.salesforce_api.function_name
  }

  tags = {
    Name = "${var.function_name}-duration-alarm"
  }
}
