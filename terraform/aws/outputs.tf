output "instance_id" {
  description = "EC2 Instance ID"
  value       = aws_instance.app.id
}

output "public_ip" {
  description = "Allocated Elastic IP address of the EC2 instance"
  value       = aws_eip.app.public_ip
}

output "public_dns" {
  description = "Public DNS hostname of the EC2 instance"
  value       = aws_eip.app.public_dns
}

output "application_url" {
  description = "Public HTTP web application URL"
  value       = var.app_port == 80 ? "http://${aws_eip.app.public_ip}" : "http://${aws_eip.app.public_ip}:${var.app_port}"
}

output "healthcheck_url" {
  description = "Application healthcheck endpoint"
  value       = var.app_port == 80 ? "http://${aws_eip.app.public_ip}/health" : "http://${aws_eip.app.public_ip}:${var.app_port}/health"
}

output "ssh_command" {
  description = "SSH connection string (if key_name was supplied)"
  value       = var.key_name != null ? "ssh -i <your-key.pem> ubuntu@${aws_eip.app.public_ip}" : "SSH Key not specified. Connect via AWS Systems Manager Session Manager."
}

output "ssm_session_command" {
  description = "AWS CLI command to start an encrypted browser/terminal session via SSM"
  value       = "aws ssm start-session --target ${aws_instance.app.id} --region ${var.aws_region}"
}
