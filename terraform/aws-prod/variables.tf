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
  default     = "production"
}

variable "vpc_cidr" {
  description = "VPC CIDR block for production"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "Public Subnet CIDR block for production"
  type        = string
  default     = "10.0.1.0/24"
}

variable "instance_type" {
  description = "EC2 instance type (Free Tier eligible: t3.micro or t4g.micro)"
  type        = string
  default     = "t3.micro"
}

variable "ami_id" {
  description = "Specific AMI ID. If null, latest Ubuntu 24.04 LTS is automatically selected"
  type        = string
  default     = null
}

variable "key_name" {
  description = "Optional EC2 Key Pair name for SSH access (optional, SSM Session Manager is enabled by default)"
  type        = string
  default     = null
}

variable "allowed_ssh_cidr" {
  description = "Allowed CIDR block for SSH access (port 22)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "allowed_http_cidr" {
  description = "Allowed CIDR block for web traffic (ports 80, 443, 8088)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "app_port" {
  description = "Host port on EC2 mapped to production Caddy reverse proxy"
  type        = number
  default     = 80
}

variable "root_volume_size" {
  description = "Root EBS GP3 volume size in GB (Free tier covers up to 30 GB)"
  type        = number
  default     = 20
}

variable "repo_url" {
  description = "Git repository URL to clone and run on the EC2 instance"
  type        = string
  default     = "https://github.com/pithwamanish/personal-lifecycle-tracker.git"
}

variable "repo_branch" {
  description = "Git branch to check out"
  type        = string
  default     = "main"
}

variable "postgres_password" {
  description = "Password for PostgreSQL. If left empty, a secure random password will be generated automatically"
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_github_oidc" {
  description = "Whether to provision the GitHub Actions OIDC provider and IAM role for Render deployment"
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
