output "database_id" {
  description = "ID of the provisioned Render PostgreSQL database"
  value       = render_postgres.db.id
}

output "backend_url" {
  description = "Public URL of the backend FastAPI service"
  value       = render_web_service.backend.url
}

output "frontend_url" {
  description = "Public URL of the frontend application"
  value       = render_web_service.frontend.url
}

output "application_health_url" {
  description = "Healthcheck URL on the frontend reverse proxy"
  value       = "${render_web_service.frontend.url}/health"
}
