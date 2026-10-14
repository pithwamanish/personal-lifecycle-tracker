variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name identifier for the project"
  type        = string
  default     = "personal-lifecycle-tracker"
}

variable "environment" {
  description = "Deployment environment (e.g., dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "database_url" {
  description = "Neon Serverless PostgreSQL connection URL"
  type        = string
  default     = "postgresql://postgres:postgres@localhost:5432/lifecycle"
  sensitive   = true
}

variable "secret_key" {
  description = "Cryptographic secret key for signing JWT tokens"
  type        = string
  default     = "dev-insecure-jwt-secret-key-replace-in-production-at-least-32-chars"
  sensitive   = true
}

variable "warmer_rate" {
  description = "EventBridge warm-up schedule expression to eliminate cold starts"
  type        = string
  default     = "rate(4 minutes)"
}

variable "digest_cron" {
  description = "EventBridge cron schedule for morning daily email digest (08:00 AM UTC)"
  type        = string
  default     = "cron(0 8 * * ? *)"
}

variable "enable_github_oidc" {
  description = "Whether to provision the GitHub Actions OIDC provider and IAM role for automated deployments"
  type        = bool
  default     = true
}

variable "existing_oidc_provider_arn" {
  description = "Optional ARN of an existing GitHub Actions OIDC provider in the AWS account to prevent duplicate provider creation"
  type        = string
  default     = null
}

variable "github_repo" {
  description = "GitHub repository identifier in org/repo format (e.g. pithwamanish/personal-lifecycle-tracker)"
  type        = string
  default     = "pithwamanish/personal-lifecycle-tracker"
}

variable "ecr_backend_repository_name" {
  description = "Optional custom name for the backend ECR repository"
  type        = string
  default     = null
}

variable "ecr_frontend_repository_name" {
  description = "Optional custom name for the frontend ECR repository"
  type        = string
  default     = null
}

variable "otel_exporter_otlp_endpoint" {
  description = "OpenTelemetry Collector OTLP endpoint (optional)"
  type        = string
  default     = ""
}

variable "otel_exporter_otlp_headers" {
  description = "OpenTelemetry Collector authorization headers (optional)"
  type        = string
  default     = ""
}
