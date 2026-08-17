# Puts the database in the subnets
resource "aws_db_subnet_group" "app" {
  name       = "api-library-db-subnet-group"
  subnet_ids = data.aws_subnets.default.ids

  tags = {
    Name = "api-library-db-subnet-group"
  }
}

# Unlike the app's security group (security_group.tf), this one does NOT
# open anything to the internet. The ingress rule below references the
# APP's security group directly as the allowed source
# ("security_groups = [...]" instead of "cidr_blocks = [...]"). That
# means: only traffic coming from something that has the app's security
# group attached (i.e. our one EC2 instance) can reach Postgres on port
# 5432 - not "anyone who knows the app's IP", not "anyone at all". This
# is reinforced at a second, independent layer by publicly_accessible =
# false on the database itself, below.
#
# No egress block is defined here on purpose. Security groups are
# "stateful" - return traffic for a connection that was allowed in is
# automatically allowed back out, with no matching egress rule needed.
# RDS never initiates outbound connections to do its job, so there's
# nothing for an egress rule to allow here.
resource "aws_security_group" "rds" {
  name        = "api-library-rds-sg"
  description = "Allow Postgres only from the app security group"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "Postgres - only reachable from the app EC2 instance, never directly from the internet"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
}

resource "aws_db_instance" "app" {
  identifier = "api-library-db"

  engine              = "postgres"
  engine_version      = "16"
  instance_class      = "db.t3.micro"
  allocated_storage   = 10    # GB - matches the free tier's storage allowance
  storage_type        = "gp2" # matches the free tier's documented storage type
  storage_encrypted   = true  # encryption at rest, using AWS's default key - free, zero downside
  publicly_accessible = false

  db_name                     = "apilibrary"
  username                    = "postgres"
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.app.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # How many days of automated backups RDS keeps. Kept short since this
  # project intentionally starts with an empty database and isn't
  # storing anything irreplaceable - raise this later for anything that
  # actually matters.
  backup_retention_period = 1

  # These two together mean `terraform destroy` deletes the database and
  # all its data immediately, with no final snapshot and no "are you
  # sure" protection to remove first. Matches this project's "start
  # fresh, nothing here is precious" decision (see DEPLOYMENT.md).
  skip_final_snapshot = true
  deletion_protection = false

  tags = {
    Name = "api-library-db"
  }
}
