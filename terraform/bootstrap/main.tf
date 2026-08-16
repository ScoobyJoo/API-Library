# This is a SEPARATE, one-time-run Terraform config from the main
# terraform/ directory. Its only job is creating the S3 bucket and
# DynamoDB table that the main config will store ITS state in.
#
# It deliberately does NOT use an S3 backend itself - that would be a
# chicken-and-egg problem, since the backend it would use doesn't exist
# until this config creates it. Its own state stays local, right here in
# terraform/bootstrap/terraform.tfstate (gitignored). That's fine: this
# config is tiny, rarely touched, and only needs to be run once, ever.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" { 
  region = "us-east-1" # keep this matching terraform/variables.tf's region default
}

# S3 bucket names are globally unique across EVERY AWS account on earth,
# not just yours - "api-library-tfstate" alone is almost certainly already
# taken by someone else's bucket somewhere. Baking your AWS account ID
# into the name (read dynamically here, never hardcoded) makes it unique
# to you automatically, with nothing to pick by hand.
data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "tfstate" {
  bucket = "api-library-tfstate-${data.aws_caller_identity.current.account_id}"

  # Note: force_destroy defaults to false here, meaning `terraform destroy`
  # on THIS config will refuse to delete the bucket while it still holds
  # objects (i.e. your real state file). That's intentional friction - you
  # almost never want to destroy this bucket, since it's the memory of
  # everything else this project created.
}

# Versioning: every time the state file changes, S3 keeps the previous
# version instead of overwriting it. If state ever gets corrupted or a
# bad apply happens, you can roll back to an earlier version instead of
# losing Terraform's entire memory of what it built.
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption at rest. AES256 (SSE-S3) uses keys AWS manages for you - no
# extra KMS key to create, rotate, or pay for. Plenty for this project;
# the state file's real secrets (the random_password values in
# terraform/secrets.tf) are only ever as safe as your AWS account's IAM
# permissions regardless of this setting.
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Belt-and-suspenders: block every path to this bucket ever becoming
# public, even if someone later attaches a public-read policy or ACL by
# mistake. This bucket holds plaintext secrets - it should never be
# reachable from the internet, full stop.
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# A DynamoDB table used purely for locking, not as a database. When you
# run `terraform apply`, Terraform writes a row here first ("I'm using
# this state right now") and deletes it when done. If a second `apply`
# starts while that row still exists, Terraform refuses to run instead of
# letting two applies race against each other and corrupt the state file.
#
# The table's partition key must be literally named "LockID" (type
# String) - that's a hardcoded requirement of Terraform's S3 backend
# itself, not a naming choice you get to make.
resource "aws_dynamodb_table" "tfstate_lock" {
  name         = "api-library-tfstate-lock"
  billing_mode = "PAY_PER_REQUEST" # no capacity to plan for - you pay per
  # request, and at this scale (one or two
  # people occasionally running terraform)
  # that's effectively free.
  hash_key = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
