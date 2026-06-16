variable "aws_region" {
  description = "AWS region for API Gateway and Lambda"
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "langgraph-debate"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "agent_runtime_arn" {
  description = "Bedrock AgentCore runtime ARN (from agentcore deploy)"
  type        = string
}

variable "cors_allowed_origins" {
  description = "CloudFront frontend URL(s) allowed for CORS. Only the first entry (index 0) is used — pass the terraform/frontend frontend_url output. Additional list elements are ignored. The value must match the browser origin exactly (scheme + host)."
  type        = list(string)
}

variable "demo_password" {
  description = "Shared demo password; set via TF_VAR_demo_password, never commit"
  type        = string
  sensitive   = true
}

variable "login_rate_limit" {
  description = "API Gateway throttle rate (req/s) on POST /api/auth/login"
  type        = number
  default     = 5
}

variable "login_burst_limit" {
  description = "API Gateway throttle burst on POST /api/auth/login"
  type        = number
  default     = 10
}

variable "stream_rate_limit" {
  description = "API Gateway throttle rate (req/s) on POST /api/debate/stream"
  type        = number
  default     = 10
}

variable "stream_burst_limit" {
  description = "API Gateway throttle burst on POST /api/debate/stream"
  type        = number
  default     = 20
}

variable "api_stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "prod"
}

variable "lambda_web_adapter_layer_arn" {
  description = "Lambda Web Adapter layer ARN for the stream function (region/arch specific)"
  type        = string
  default     = "arn:aws:lambda:eu-west-1:753240598075:layer:LambdaAdapterLayerX86:27"
}
