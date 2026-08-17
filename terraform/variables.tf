# Every value here can be overridden with -var="name=value" on the command
# line, a terraform.tfvars file, or TF_VAR_name environment variables.
# Variables with no `default` MUST be supplied - Terraform will prompt for
# them interactively if you forget.

variable "region" {
  description = "AWS region to deploy into. us-east-1 is used in most tutorials and has every service available."
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance size. t3.micro/t2.micro are the free-tier-eligible sizes."
  type        = string
  default     = "t3.micro"
}

# Unused as of the fix that opened SSH to everyone (GitHub Actions
# runners have no stable IP to allowlist) - security_group.tf's SSH rule
# is now a hardcoded 0.0.0.0/0, not var.allowed_ssh_cidr. Left here,
# commented out, instead of deleted in case SSH access ever gets
# restricted to a real IP range again later.
#
# variable "allowed_ssh_cidr" {
#   description = "CIDR block allowed to SSH into the instance on port 22, e.g. \"203.0.113.4/32\" (your own public IP with /32). Never set this to \"0.0.0.0/0\" - that lets anyone on the internet attempt to log in to your server."
#   type        = string
# }

variable "ssh_public_key_path" {
  description = "Path to the PUBLIC half of an SSH key pair you generate yourself with `ssh-keygen` (e.g. ~/.ssh/api-library.pub). Terraform uploads this to AWS; it never sees or generates your private key."
  type        = string
}

variable "app_port" {
  description = "Port the Flask app listens on inside docker-compose (matches EXPOSE 5000 in the Dockerfile)."
  type        = number
  default     = 5000
}

variable "repo_url" {
  description = "HTTPS URL of the git repo the EC2 instance clones on first boot."
  type        = string
  default     = "https://github.com/ScoobyJoo/API-Library.git"
}

variable "project_dir_name" {
  description = "Directory name the repo is cloned into under /home/ec2-user/. Must match the path used in .github/workflows/deploy.yml."
  type        = string
  default     = "API-Library"
}
