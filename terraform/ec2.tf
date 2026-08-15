# Looks up the current Amazon Linux 2023 AMI (machine image) instead of
# hardcoding an AMI ID - AMI IDs are region-specific and go stale as AWS
# ships updates, so a hardcoded one would eventually stop working or fall
# behind on security patches.

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# Uploads the PUBLIC half of a key pair you generate yourself with
# `ssh-keygen` (see DEPLOYMENT.md). Terraform never sees your private key.
resource "aws_key_pair" "deployer" {
  key_name   = "api-library-key"
  public_key = file(var.ssh_public_key_path)
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.app.id]
  key_name               = aws_key_pair.deployer.key_name

  user_data = templatefile("${path.module}/templates/user_data.sh.tpl", {
    secret_key  = random_password.secret_key.result
    db_password = random_password.db_password.result
    repo_url    = var.repo_url
    project_dir = var.project_dir_name
  })

  # user_data only runs on an instance's FIRST boot, not on every
  # `terraform apply`. Without this, editing the script wouldn't actually
  # change anything on an already-running instance - this forces AWS to
  # replace the instance (terminate + recreate) whenever it changes, so
  # the new script actually executes.
  user_data_replace_on_change = true

  tags = {
    Name = "api-library-app"
  }
}

# A bare EC2 instance's public IP changes if it's stopped/started or
# replaced (e.g. by the user_data_replace_on_change above). The GitHub
# Actions deploy workflow needs a stable address to SSH into, so we
# reserve a fixed IP and attach it to whatever instance currently exists.
#
# Elastic IPs are free WHILE attached to a running instance - AWS only
# bills for ones left unattached, which shouldn't happen here as long as
# `terraform destroy` is used to tear everything down together.
resource "aws_eip" "app" {
  domain   = "vpc"
  instance = aws_instance.app.id

  tags = {
    Name = "api-library-eip"
  }
}
