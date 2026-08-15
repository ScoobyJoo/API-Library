# Terraform generates these itself, once, the first time you run `apply`.
# They live only in terraform.tfstate (local, gitignored, never committed)
# and get written into the .env file on the EC2 instance via user_data -
# they never touch GitHub, and you never have to type or remember them.

resource "random_password" "secret_key" {
  length  = 64
  special = false
}

resource "random_password" "db_password" {
  length = 24
  # special = false: this password gets embedded directly into a
  # postgresql://user:PASSWORD@host/db connection URL. Special characters
  # like @, /, or : would need URL-encoding there and could break parsing -
  # keeping it alphanumeric avoids that whole problem.
  special = false
}
