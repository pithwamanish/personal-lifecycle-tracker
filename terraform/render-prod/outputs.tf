output "backend_url" {
  description = "Render URL for the backend API service"
  value       = render_web_service.backend.url
}

output "frontend_url" {
  description = "Render URL for the frontend application"
  value       = render_web_service.frontend.url
}

output "application_health_url" {
  description = "Public healthcheck URL via frontend reverse proxy"
  value       = "${render_web_service.frontend.url}/health"
}

output "database_id" {
  description = "Render Managed PostgreSQL database ID"
  value       = render_postgres.db.id
}
