resource "render_postgres" "db" {
  name          = "personal-lifecycle-db-${var.environment}"
  plan          = var.db_plan
  region        = var.region
  version       = "16"
  database_name = "lifecycle"
  database_user = "postgres"
}

resource "render_web_service" "backend" {
  name   = "personal-lifecycle-backend-${var.environment}"
  plan   = var.plan
  region = var.region

  runtime_source = {
    docker = {
      repo_url        = var.repo_url
      branch          = var.repo_branch
      dockerfile_path = "./backend/Dockerfile"
      context         = "./backend"
    }
  }

  env_vars = {
    PORT             = { value = "8000" }
    PYTHONUNBUFFERED = { value = "1" }
    CORS_ORIGINS     = { value = "*" }
    DATABASE_URL     = { value = render_postgres.db.connection_info.internal_connection_string }
  }
}

resource "render_web_service" "frontend" {
  name   = "personal-lifecycle-frontend-${var.environment}"
  plan   = var.plan
  region = var.region

  runtime_source = {
    docker = {
      repo_url          = var.repo_url
      branch            = var.repo_branch
      dockerfile_path   = "./frontend/Dockerfile"
      context           = "./frontend"
      dockerfile_target = "prod"
    }
  }

  env_vars = {
    PORT        = { value = "80" }
    BACKEND_URL = { value = render_web_service.backend.url }
  }
}
