output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.salesforce_api.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.salesforce_api.arn
}

output "lambda_role_arn" {
  description = "IAM role ARN for Lambda function"
  value       = aws_iam_role.lambda_role.arn
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = "${aws_apigatewayv2_api.salesforce_api.api_endpoint}/${var.api_stage_name}"
}

output "api_id" {
  description = "API Gateway API ID"
  value       = aws_apigatewayv2_api.salesforce_api.id
}

output "stage_name" {
  description = "API Gateway stage name"
  value       = aws_apigatewayv2_stage.default.name
}

output "lambda_logs_group_name" {
  description = "CloudWatch log group name for Lambda"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "api_logs_group_name" {
  description = "CloudWatch log group name for API Gateway"
  value       = aws_cloudwatch_log_group.api_logs.name
}

output "health_check_url" {
  description = "Health check endpoint URL"
  value       = "${aws_apigatewayv2_api.salesforce_api.api_endpoint}/${var.api_stage_name}/health"
}

output "create_account_url" {
  description = "Create account endpoint URL"
  value       = "${aws_apigatewayv2_api.salesforce_api.api_endpoint}/${var.api_stage_name}/accounts"
}

output "query_endpoint_url" {
  description = "SOQL query endpoint URL"
  value       = "${aws_apigatewayv2_api.salesforce_api.api_endpoint}/${var.api_stage_name}/query"
}

output "alarm_error_arn" {
  description = "CloudWatch alarm ARN for Lambda errors"
  value       = aws_cloudwatch_metric_alarm.lambda_errors.arn
}

output "alarm_duration_arn" {
  description = "CloudWatch alarm ARN for Lambda duration"
  value       = aws_cloudwatch_metric_alarm.lambda_duration.arn
}

output "deployment_summary" {
  description = "Deployment summary"
  value = {
    api_endpoint  = "${aws_apigatewayv2_api.salesforce_api.api_endpoint}/${var.api_stage_name}"
    lambda_function = aws_lambda_function.salesforce_api.function_name
    environment   = var.environment
    region        = var.aws_region
  }
}
