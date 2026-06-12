variable "aws_region" {
  description = "AWS region for S3 and CloudFront"
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
