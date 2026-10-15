output "lambda_function_name" {
  description = "Name of the backend FastAPI Lambda function"
  value       = aws_lambda_function.backend.function_name
}

output "lambda_function_url" {
  description = "Public direct HTTPS Function URL for the backend API"
  value       = aws_lambda_function_url.backend_url.function_url
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name serving SPA and reverse-proxying /api"
  value       = aws_cloudfront_distribution.cdn.domain_name
}

output "frontend_s3_bucket" {
  description = "S3 bucket name hosting the React frontend assets"
  value       = aws_s3_bucket.frontend.id
}

output "github_oidc_role_arn" {
  description = "IAM Role ARN assumed by GitHub Actions for automated deployment"
  value       = var.enable_github_oidc ? aws_iam_role.github_actions_render_deployer[0].arn : null
}
