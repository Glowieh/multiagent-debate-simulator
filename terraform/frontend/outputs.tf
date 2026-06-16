output "frontend_bucket_name" {
  description = "S3 bucket name for frontend static assets"
  value       = aws_s3_bucket.frontend.bucket
}

output "frontend_cloudfront_distribution_id" {
  description = "CloudFront distribution ID for cache invalidation"
  value       = aws_cloudfront_distribution.frontend.id
}

output "frontend_url" {
  description = "HTTPS URL for the deployed frontend"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}
