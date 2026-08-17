# Printed after `terraform apply` finishes, and re-readable any time with
# `terraform output` (or `terraform output <name>` for a single value).

output "app_url" {
  description = "URL to open the running app in a browser"
  value       = "http://${aws_eip.app.public_ip}:${var.app_port}"
}

output "ssh_command" {
  description = "Command to SSH into the instance"
  value       = "ssh ec2-user@${aws_eip.app.public_ip}"
}

output "instance_public_ip" {
  description = "The instance's stable public IP - use this for the EC2_HOST GitHub Secret"
  value       = aws_eip.app.public_ip
}

output "rds_endpoint" {
  description = "The database's hostname:port - useful for debugging (e.g. connecting via psql through an SSH tunnel through the EC2 instance, since the database itself isn't publicly reachable)"
  value       = aws_db_instance.app.endpoint
}
