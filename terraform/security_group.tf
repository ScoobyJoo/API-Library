# A security group is a virtual firewall attached to the instance. By
# default AWS blocks ALL inbound traffic - every port you want reachable
# has to be explicitly opened here.

resource "aws_security_group" "app" {
  name        = "api-library-app-sg"
  description = "Allow SSH from a trusted IP and app traffic from anywhere"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH - Only accessible with private key"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Flask app - public, this is the whole point of the server"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic (installing packages, pulling docker images, etc.)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # Catch all
    cidr_blocks = ["0.0.0.0/0"]
  }
}
