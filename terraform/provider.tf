# Tells Terraform which "providers" (plugins that know how to talk to a
# specific API) this project needs, and pins their versions so a
# `terraform init` next year doesn't silently pull in breaking changes.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# The AWS provider is what lets Terraform actually create/read/destroy
# real AWS resources. It authenticates using whatever credentials
# `aws configure` set up on your machine - Terraform itself never needs
# a separate login step, it just reuses the AWS CLI's credentials.
provider "aws" {
  region = var.region
}
