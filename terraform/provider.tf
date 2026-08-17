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

  # Where Terraform stores its state file, instead of the default (a local
  # terraform.tfstate file that only exists on whichever machine ran
  # `apply`). Storing it in S3 means anyone with AWS access can run
  # Terraform against the same infrastructure and see what already exists;
  # dynamodb_table adds locking so two people can't run apply/destroy at
  # the same time and corrupt it.
  #
  # IMPORTANT LIMITATION: backend blocks cannot use variables, locals, or
  # any other interpolation - only literal hardcoded strings are allowed
  # here. This is a real Terraform restriction (backend config has to be
  # knowable before Terraform has evaluated anything else in the config),
  # not a style choice. That means the bucket/table names below are typed
  # in by hand, copied from `terraform -chdir=bootstrap output` after
  # you've run the bootstrap config once - see DEPLOYMENT.md.
  backend "s3" {
    bucket       = "api-library-tfstate-492613460331" # from: terraform -chdir=bootstrap output bucket_name
    key          = "api-library/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
    encrypt      = true
  }
}

# The AWS provider is what lets Terraform actually create/read/destroy
# real AWS resources. It authenticates using whatever credentials
# `aws configure` set up on your machine - Terraform itself never needs
# a separate login step, it just reuses the AWS CLI's credentials.
provider "aws" {
  region = var.region
}
