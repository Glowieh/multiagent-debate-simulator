data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "auth_lambda" {
  statement {
    sid    = "Logs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.auth.arn}:*"]
  }

  statement {
    sid    = "ReadAuthSecret"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [aws_secretsmanager_secret.demo_auth.arn]
  }
}

data "aws_iam_policy_document" "stream_lambda" {
  statement {
    sid    = "Logs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.stream.arn}:*"]
  }

  statement {
    sid    = "ReadAuthSecret"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [aws_secretsmanager_secret.demo_auth.arn]
  }

  statement {
    sid    = "InvokeAgentRuntime"
    effect = "Allow"
    actions = [
      "bedrock-agentcore:InvokeAgentRuntime",
    ]
    resources = [var.agent_runtime_arn]
  }
}

resource "aws_iam_role" "auth_lambda" {
  name               = "${local.name_prefix}-api-auth"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role" "stream_lambda" {
  name               = "${local.name_prefix}-api-stream"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy" "auth_lambda" {
  name   = "${local.name_prefix}-api-auth"
  role   = aws_iam_role.auth_lambda.id
  policy = data.aws_iam_policy_document.auth_lambda.json
}

resource "aws_iam_role_policy" "stream_lambda" {
  name   = "${local.name_prefix}-api-stream"
  role   = aws_iam_role.stream_lambda.id
  policy = data.aws_iam_policy_document.stream_lambda.json
}
