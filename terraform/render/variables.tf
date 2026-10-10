variable "render_api_key" {
  description = "Render API key generated from Account Settings -> API Keys"
  type        = string
  sensitive   = true
}

variable "render_owner_id" {
  description = "Render Owner/Team ID (starts with tea- or usr-)"
  type        = string
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "production"
}

variable "region" {
  description = "Render region for resources (oregon, frankfurt, ohio, singapore)"
  type        = string
  default     = "oregon"
}

variable "plan" {
  description = "Render service plan (free, starter, standard)"
  type        = string
  default     = "starter"
}

variable "db_plan" {
  description = "Render postgres plan (free, starter, standard)"
  type        = string
  default     = "starter"
}

variable "repo_url" {
  description = "Git repository URL containing the application source"
  type        = string
  default     = "https://github.com/pithwamanish/personal-lifecycle-tracker.git"
}

variable "repo_branch" {
  description = "Git branch to build and deploy"
  type        = string
  default     = "main"
}
