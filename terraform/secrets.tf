# Terraform generates this itself, once, the first time you run `apply`.
# It lives only in terraform.tfstate (local, gitignored, never
# committed) and gets written into the .env file on the EC2 instance via
# user_data - it never touches GitHub, and you never have to type or
# remember it.
#
# The database password used to be generated the same way, by a sibling
# random_password.db_password resource here - it's gone now that
# rds.tf uses manage_master_user_password = true instead, which has AWS
# generate and store the real master password in Secrets Manager. The
# EC2 instance fetches that real password at boot instead (see
# templates/user_data.sh.tpl step 5 and iam.tf).

resource "random_password" "secret_key" {
  length  = 64
  special = false
}
