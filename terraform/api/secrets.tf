locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "aws_secretsmanager_secret" "demo_auth" {
  name = "${local.name_prefix}-demo-auth"
}

resource "aws_secretsmanager_secret_version" "demo_auth" {
  secret_id = aws_secretsmanager_secret.demo_auth.id
  secret_string = jsonencode({
    demo_password = var.demo_password
    jwt_secret    = random_password.jwt_secret.result
  })
}
