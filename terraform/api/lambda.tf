locals {
  cors_origin = var.cors_allowed_origins[0]
}

resource "null_resource" "build_api_proxy" {
  triggers = {
    auth_hash      = filemd5("${path.module}/../../lambda/api-proxy/auth_handler.py")
    auth_py        = filemd5("${path.module}/../../lambda/api-proxy/auth.py")
    cors_py        = filemd5("${path.module}/../../lambda/api-proxy/cors.py")
    secrets_module = filemd5("${path.module}/../../lambda/api-proxy/secrets_module.py")
    run_sh         = filemd5("${path.module}/../../lambda/api-proxy/run.sh")
    stream_hash    = filemd5("${path.module}/../../lambda/api-proxy/stream_app.py")
    auth_reqs      = filemd5("${path.module}/../../lambda/api-proxy/requirements-auth.txt")
    stream_reqs    = filemd5("${path.module}/../../lambda/api-proxy/requirements-stream.txt")
  }

  provisioner "local-exec" {
    command = "${path.module}/../../scripts/build-api-proxy.sh"
  }
}

data "archive_file" "auth_lambda" {
  depends_on  = [null_resource.build_api_proxy]
  type        = "zip"
  source_dir  = "${path.module}/build/auth"
  output_path = "${path.module}/build/auth.zip"
}

data "archive_file" "stream_lambda" {
  depends_on  = [null_resource.build_api_proxy]
  type        = "zip"
  source_dir  = "${path.module}/build/stream"
  output_path = "${path.module}/build/stream.zip"
}

resource "aws_cloudwatch_log_group" "auth" {
  name              = "/aws/lambda/${local.name_prefix}-api-auth"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "stream" {
  name              = "/aws/lambda/${local.name_prefix}-api-stream"
  retention_in_days = 14
}

resource "aws_lambda_function" "auth" {
  depends_on = [data.archive_file.auth_lambda]

  function_name = "${local.name_prefix}-api-auth"
  role          = aws_iam_role.auth_lambda.arn
  handler       = "auth_handler.handler"
  runtime       = "python3.12"
  timeout       = 10
  memory_size   = 256

  filename         = data.archive_file.auth_lambda.output_path
  source_code_hash = data.archive_file.auth_lambda.output_base64sha256

  environment {
    variables = {
      AUTH_SECRET_ARN     = aws_secretsmanager_secret.demo_auth.arn
      CORS_ALLOWED_ORIGIN = local.cors_origin
    }
  }
}

resource "aws_lambda_function" "stream" {
  depends_on = [data.archive_file.stream_lambda]

  function_name = "${local.name_prefix}-api-stream"
  role          = aws_iam_role.stream_lambda.arn
  handler       = "run.sh"
  runtime       = "python3.12"
  timeout       = 900
  memory_size   = 512
  layers        = [var.lambda_web_adapter_layer_arn]

  filename         = data.archive_file.stream_lambda.output_path
  source_code_hash = data.archive_file.stream_lambda.output_base64sha256

  environment {
    variables = {
      AUTH_SECRET_ARN         = aws_secretsmanager_secret.demo_auth.arn
      AGENT_RUNTIME_ARN       = var.agent_runtime_arn
      AWS_LAMBDA_EXEC_WRAPPER = "/opt/bootstrap"
      AWS_LWA_INVOKE_MODE     = "response_stream"
      CORS_ALLOWED_ORIGIN     = local.cors_origin
      PORT                    = "8080"
    }
  }
}
