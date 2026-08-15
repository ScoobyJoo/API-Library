# Deploying to AWS

This document walks through running API Library on a real AWS server, using Terraform to create the infrastructure and GitHub Actions to redeploy automatically whenever you push to `main`.

This is written as a learning exercise, not just a runbook — read the explanations, not just the commands, especially the first time through.

## 1. What you're building

One EC2 instance (a rented Linux virtual machine) running the exact same `docker-compose.yml` you already use locally, given a stable public IP address so it's reachable on the internet on port 5000. When you push to `main`, GitHub Actions SSHes into that machine, pulls your latest code, and restarts the containers.

## 2. Glossary

A few AWS/Terraform terms used below, in plain language:

- **Default VPC** — every AWS account already has one "Virtual Private Cloud" (an isolated network) per region, pre-configured and ready to use. We use the one that's already there instead of building a custom network.
- **Security group** — a firewall attached to the instance. Nothing gets in unless a rule explicitly allows it.
- **EC2 instance** — the actual virtual machine your app runs on.
- **Elastic IP** — a public IP address you reserve, which stays the same even if the instance is replaced. Without one, the server's address could change every time you run `terraform apply`.
- **Key pair** — an SSH key pair (a private key you keep secret, a public key AWS stores) used to log into the instance instead of a password.
- **`user_data`** — a script AWS runs automatically the very first time an instance boots. This project uses it to install Docker, clone the repo, and start the app — so the site is live immediately after `terraform apply`, with no manual setup on the box.
- **Terraform state** (`terraform.tfstate`) — a file Terraform keeps to track what it created. It contains real secrets in this project (see below) and must never be committed to git — it's already in `.gitignore`.

## 3. Trade-offs made here (read this before you're surprised later)

- **No managed database (RDS).** Postgres runs in a container on the same EC2 instance, exactly like local dev. This means the database's data lives on that instance's disk — if the instance is ever replaced (e.g. because `user_data` changed), **the data is lost**. Fine for a learning project with no real data; a real production setup would use RDS instead. That's a natural next step once you're comfortable with what's here.
- **No container registry (ECR).** Deploying doesn't build a Docker image and push it anywhere — GitHub Actions just SSHes into the server and rebuilds the image from source there (`docker compose up -d --build`), the same way you'd do it locally. Simpler and needs zero AWS credentials in GitHub, but slower per deploy since it rebuilds from scratch every time. Also a natural next step later.
- **No load balancer, no HTTPS, no custom domain.** You'll access the app over plain HTTP at `http://<ip>:5000`.
- **The `/admin` section still has no authentication at all** (a separate, pre-existing limitation of this app, not something introduced by deploying it) — deploying to a public server makes this more consequential than running it locally, since it's now reachable by anyone who finds the IP.

## 4. Prerequisites (do these once)

1. **Create an AWS account** if you don't have one, and set a budget alert (Billing → Budgets) so you get an email if spend ever leaves the free tier.
2. **Create an IAM user** for yourself to use from the command line — don't use your AWS account's root login for this. In the AWS Console: IAM → Users → Create user → attach a policy with EC2 permissions (e.g. `AmazonEC2FullAccess` is the simplest to start with) → create an access key for it. Root credentials can do literally anything to your account with no way to limit the damage if they ever leak; an IAM user's permissions can be scoped down and revoked independently.
3. **Install the AWS CLI**, then run `aws configure` and paste in that IAM user's access key ID and secret.
4. **Install Terraform** (the `terraform` command).
5. **Generate an SSH key pair** you'll use to reach the server:
   ```
   ssh-keygen -t ed25519 -f ~/.ssh/api-library
   ```
   This creates `~/.ssh/api-library` (private — never share this) and `~/.ssh/api-library.pub` (public — Terraform uploads this one to AWS).
6. **Find your own public IP** (search "what is my ip") — you'll need it as `allowed_ssh_cidr` below, as `<your-ip>/32`.

## 5. Provisioning the infrastructure

```
cd terraform
terraform init
terraform plan  -var="allowed_ssh_cidr=YOUR_IP/32" -var="ssh_public_key_path=~/.ssh/api-library.pub"
terraform apply -var="allowed_ssh_cidr=YOUR_IP/32" -var="ssh_public_key_path=~/.ssh/api-library.pub"
```

`terraform init` downloads the AWS/random providers. `terraform plan` shows you exactly what it's about to create, with no changes made yet — always worth reading before `apply`. `terraform apply` asks for confirmation, then actually creates everything.

Tip: instead of typing the two `-var` flags every time, create a `terraform/terraform.tfvars` file (already gitignored, since it'll contain your IP):
```
allowed_ssh_cidr     = "YOUR_IP/32"
ssh_public_key_path  = "~/.ssh/api-library.pub"
```
Terraform reads that automatically — then you can just run `terraform plan` / `terraform apply` with no flags.

## 6. Getting the app's URL

```
terraform output app_url
```

Give the instance a minute or two after `apply` finishes — `user_data` is still installing Docker and building the app in the background the first time.

## 7. Setting up automatic deploys

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**, add two:

- `EC2_SSH_PRIVATE_KEY` — the full contents of your private key file (`~/.ssh/api-library`, not the `.pub` one).
- `EC2_HOST` — the output of `terraform output instance_public_ip`.

From then on, every push to `main` runs `.github/workflows/deploy.yml`, which SSHes in and redeploys.

## 8. Tearing it down

```
cd terraform
terraform destroy
```

This deletes everything Terraform created — including the database container and its data (see the trade-off above). It's the way to make sure you're not paying for anything once you're done experimenting; there's nothing left running afterward.

## 9. Where to learn more

- HashiCorp's official "Get Started - AWS" tutorial (on developer.hashicorp.com) covers the same core Terraform concepts used here in more depth.
- AWS's own EC2 getting-started documentation is worth reading if you want to understand more of what's happening under the hood beyond what Terraform abstracts away.
