# This file lets the EC2 instance ask AWS Secrets Manager for the RDS
# master password itself, at boot, instead of Terraform ever knowing or
# handling that password. This is the first thing in this project that
# is IAM (AWS's permissions system) as something Terraform CREATES,
# rather than something you click through once by hand in the IAM
# console for your own login (see DEPLOYMENT.md's prerequisites).

# An IAM ROLE is an identity that isn't a person - something an AWS
# resource can "assume" (temporarily wear) to gain a specific, limited
# set of permissions. This role grants exactly one permission (defined
# below): read one specific secret. Nothing else.
#
# The "assume_role_policy" (AWS calls this a "trust policy") answers a
# different question than the permissions themselves: not "what can this
# role DO" but "who/what is ALLOWED to assume this role in the first
# place". Here, only the EC2 service itself is trusted to use it - not
# other AWS services, not other AWS accounts, not people.
resource "aws_iam_role" "ec2_app" {
  name = "api-library-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "api-library-ec2-role"
  }
}

# The actual permission this role grants: read ONE specific secret - the
# auto-generated RDS master password created because
# manage_master_user_password = true in rds.tf - and nothing else.
#
# Resource is scoped to that exact secret's ARN, not "*" (every secret in
# the account). If this ever expanded to "*", any code running on this
# EC2 instance (including a future security bug in the Flask app itself)
# could read ANY secret in this AWS account, not just this one database
# password. Least-privilege here costs nothing extra to set up and
# closes off a real blast-radius risk.
#
# No kms:Decrypt permission is needed here: manage_master_user_password
# with no master_user_secret_kms_key_id set uses AWS's own default
# Secrets Manager key, not a customer-managed KMS key. If a custom KMS
# key were ever configured for the secret later, kms:Decrypt on that key
# would need to be added to this policy too.
resource "aws_iam_role_policy" "secrets_access" {
  name = "api-library-secrets-access"
  role = aws_iam_role.ec2_app.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "secretsmanager:GetSecretValue"
        Resource = aws_db_instance.app.master_user_secret[0].secret_arn
      }
    ]
  })
}

# EC2 instances can't attach an IAM role directly - AWS requires the
# extra step of wrapping it in an "instance profile" (basically just a
# named container that holds exactly one role) and attaching THAT to the
# instance instead. This is a fixed AWS API requirement, not a design
# choice made in this project - ec2.tf attaches this instance profile,
# not the role above, via its iam_instance_profile argument.
resource "aws_iam_instance_profile" "app" {
  name = "api-library-ec2-instance-profile"
  role = aws_iam_role.ec2_app.name
}
