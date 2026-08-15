# Every AWS account already has a "default VPC" in each region, pre-wired
# with public subnets, an internet gateway, and route tables - all set up
# automatically when the account was created. Reading it with a `data`
# block (instead of creating a custom VPC with `resource` blocks) skips a
# whole layer of networking concepts (subnets, route tables, gateways)
# this small project doesn't need to manage itself.

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}
