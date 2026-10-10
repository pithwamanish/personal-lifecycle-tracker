variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project identifier"
  type        = string
  default     = "personal-lifecycle-tracker"
}

variable "environment" {
  description = "Target deployment environment"
  type        = string
  default     = "production"
}

variable "database_url" {
  description = "Neon Serverless PostgreSQL pooled connection string (e.g. postgresql://user:pass@ep-xyz-pooler.us-east-2.aws.neon.tech/lifecycle?sslmode=require)"
  type        = string
  sensitive   = true
  default     = "sqlite:///./lifecycle.db"
}

variable "secret_key" {
  description = "JWT authentication secret key"
  type        = string
  sensitive   = true
  default     = "super-secret-jwt-key-change-in-production-2026"
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
