output "cloudfront_domain_name" {
  description = "Global CloudFront CDN endpoint serving the React 19 application"
  value       = aws_cloudfront_distribution.cdn.domain_name
}

output "application_url" {
  description = "Production Application URL"
  value       = "https://${aws_cloudfront_distribution.cdn.domain_name}"
}

output "lambda_function_url" {
  description = "Direct AWS Lambda Function URL for backend API"
  value       = aws_lambda_function_url.backend_url.function_url
}

output "ecr_repository_url" {
  description = "Amazon ECR container repository URL"
  value       = aws_ecr_repository.backend.repository_url
}

output "s3_bucket_name" {
  description = "Frontend S3 bucket for static builds"
  value       = aws_s3_bucket.frontend.bucket
}

output "prometheus_metrics_url" {
  description = "Live Prometheus metrics scraping endpoint for Grafana / CloudWatch"
  value       = "https://${aws_cloudfront_distribution.cdn.domain_name}/metrics"
}
