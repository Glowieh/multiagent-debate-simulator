resource "aws_api_gateway_rest_api" "debate" {
  name        = "${local.name_prefix}-api"
  description = "Debate demo API (auth + streaming proxy)"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "api" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  parent_id   = aws_api_gateway_rest_api.debate.root_resource_id
  path_part   = "api"
}

resource "aws_api_gateway_resource" "auth" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "auth"
}

resource "aws_api_gateway_resource" "login" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  parent_id   = aws_api_gateway_resource.auth.id
  path_part   = "login"
}

resource "aws_api_gateway_resource" "debate_path" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  parent_id   = aws_api_gateway_resource.api.id
  path_part   = "debate"
}

resource "aws_api_gateway_resource" "stream" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  parent_id   = aws_api_gateway_resource.debate_path.id
  path_part   = "stream"
}

# --- POST /api/auth/login ---

resource "aws_api_gateway_method" "login_post" {
  rest_api_id   = aws_api_gateway_rest_api.debate.id
  resource_id   = aws_api_gateway_resource.login.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "login_post" {
  rest_api_id             = aws_api_gateway_rest_api.debate.id
  resource_id             = aws_api_gateway_resource.login.id
  http_method             = aws_api_gateway_method.login_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.auth.invoke_arn
}

resource "aws_lambda_permission" "login" {
  statement_id  = "AllowAPIGatewayInvokeLogin"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.auth.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.debate.execution_arn}/*/*"
}

# --- OPTIONS /api/auth/login (CORS) ---

resource "aws_api_gateway_method" "login_options" {
  rest_api_id   = aws_api_gateway_rest_api.debate.id
  resource_id   = aws_api_gateway_resource.login.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "login_options" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  resource_id = aws_api_gateway_resource.login.id
  http_method = aws_api_gateway_method.login_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "login_options" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  resource_id = aws_api_gateway_resource.login.id
  http_method = aws_api_gateway_method.login_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "login_options" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  resource_id = aws_api_gateway_resource.login.id
  http_method = aws_api_gateway_method.login_options.http_method
  status_code = aws_api_gateway_method_response.login_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods"   = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"    = "'${local.cors_origin}'"
  }
}

# --- POST /api/debate/stream (response streaming) ---

resource "aws_api_gateway_method" "stream_post" {
  rest_api_id   = aws_api_gateway_rest_api.debate.id
  resource_id   = aws_api_gateway_resource.stream.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "stream_post" {
  rest_api_id             = aws_api_gateway_rest_api.debate.id
  resource_id             = aws_api_gateway_resource.stream.id
  http_method             = aws_api_gateway_method.stream_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.stream.response_streaming_invoke_arn
  response_transfer_mode  = "STREAM"
  timeout_milliseconds    = 900000
}

resource "aws_lambda_permission" "stream" {
  statement_id  = "AllowAPIGatewayInvokeStream"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stream.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.debate.execution_arn}/*/*"
}

# --- OPTIONS /api/debate/stream (CORS) ---

resource "aws_api_gateway_method" "stream_options" {
  rest_api_id   = aws_api_gateway_rest_api.debate.id
  resource_id   = aws_api_gateway_resource.stream.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "stream_options" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  resource_id = aws_api_gateway_resource.stream.id
  http_method = aws_api_gateway_method.stream_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "stream_options" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  resource_id = aws_api_gateway_resource.stream.id
  http_method = aws_api_gateway_method.stream_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "stream_options" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  resource_id = aws_api_gateway_resource.stream.id
  http_method = aws_api_gateway_method.stream_options.http_method
  status_code = aws_api_gateway_method_response.stream_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods"   = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"    = "'${local.cors_origin}'"
  }
}

# --- Deployment ---

resource "aws_api_gateway_deployment" "debate" {
  rest_api_id = aws_api_gateway_rest_api.debate.id

  triggers = {
    redeploy = sha1(jsonencode([
      aws_api_gateway_integration.login_post.id,
      aws_api_gateway_integration.login_options.id,
      aws_api_gateway_integration.stream_post.id,
      aws_api_gateway_integration.stream_options.id,
      local.cors_origin,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.login_post,
    aws_api_gateway_integration.login_options,
    aws_api_gateway_integration.stream_post,
    aws_api_gateway_integration.stream_options,
  ]
}

resource "aws_api_gateway_stage" "debate" {
  rest_api_id   = aws_api_gateway_rest_api.debate.id
  deployment_id = aws_api_gateway_deployment.debate.id
  stage_name    = var.api_stage_name
}

resource "aws_api_gateway_method_settings" "login_throttle" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  stage_name  = aws_api_gateway_stage.debate.stage_name
  method_path = "api/auth/login/POST"

  settings {
    throttling_rate_limit  = var.login_rate_limit
    throttling_burst_limit = var.login_burst_limit
    metrics_enabled        = true
    logging_level          = "OFF"
  }
}

resource "aws_api_gateway_method_settings" "stream_throttle" {
  rest_api_id = aws_api_gateway_rest_api.debate.id
  stage_name  = aws_api_gateway_stage.debate.stage_name
  method_path = "api/debate/stream/POST"

  settings {
    throttling_rate_limit  = var.stream_rate_limit
    throttling_burst_limit = var.stream_burst_limit
    metrics_enabled        = true
    logging_level          = "OFF"
  }
}
