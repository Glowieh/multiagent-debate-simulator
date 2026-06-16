output "api_base_url" {
  description = "API Gateway base URL for VITE_API_BASE_URL (no trailing slash)"
  value       = "https://${aws_api_gateway_rest_api.debate.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.debate.stage_name}"
}

output "auth_secret_arn" {
  description = "Secrets Manager ARN for demo auth (password + jwt_secret)"
  value       = aws_secretsmanager_secret.demo_auth.arn
}

output "auth_lambda_name" {
  description = "Auth Lambda function name"
  value       = aws_lambda_function.auth.function_name
}

output "stream_lambda_name" {
  description = "Stream Lambda function name"
  value       = aws_lambda_function.stream.function_name
}
