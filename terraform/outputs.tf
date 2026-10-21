output "instance_public_ip" {
  description = "Public IP of the web server (use as EC2_HOST in Jenkins)"
  value       = aws_instance.web.public_ip
}

output "website_url" {
  description = "URL of the deployed website"
  value       = "http://${aws_instance.web.public_ip}"
}
