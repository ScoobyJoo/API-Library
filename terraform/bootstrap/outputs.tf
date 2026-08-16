# Printed after `terraform apply` here, and re-readable any time with
# `terraform output` from inside terraform/bootstrap/. You'll copy these
# two values by hand into the backend block in terraform/provider.tf -
# see the comment there for why that has to be a manual copy-paste
# instead of an automatic reference.

output "bucket_name" {
  description = "S3 bucket holding the main config's Terraform state - copy into terraform/provider.tf's backend block"
  value       = aws_s3_bucket.tfstate.bucket
}

output "table_name" {
  description = "DynamoDB table used for state locking - copy into terraform/provider.tf's backend block"
  value       = aws_dynamodb_table.tfstate_lock.name
}
