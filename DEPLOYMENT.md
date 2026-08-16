# Deploying to AWS

This document walks through running API Library on a real AWS server, using Terraform to create the infrastructure and GitHub Actions to redeploy automatically whenever you push to `main`.

This is written as a learning exercise, not just a runbook — read the explanations, not just the commands, especially the first time through.

## 1. What you're building

One EC2 instance (a rented Linux virtual machine) running the exact same `docker-compose.yml` you already use locally, given a stable public IP address so it's reachable on the internet on port 5000. When you push to `main`, GitHub Actions SSHes into that machine, pulls your latest code, and restarts the containers — after you manually approve the deploy (see section 8).

## 2. Glossary

A few AWS/Terraform terms used below, in plain language:

- **Default VPC** — every AWS account already has one "Virtual Private Cloud" (an isolated network) per region, pre-configured and ready to use. We use the one that's already there instead of building a custom network.
- **Security group** — a firewall attached to the instance. Nothing gets in unless a rule explicitly allows it.
- **EC2 instance** — the actual virtual machine your app runs on.
- **Elastic IP** — a public IP address you reserve, which stays the same even if the instance is replaced. Without one, the server's address could change every time you run `terraform apply`.
- **Key pair** — an SSH key pair (a private key you keep secret, a public key AWS stores) used to log into the instance instead of a password.
- **`user_data`** — a script AWS runs automatically the very first time an instance boots. This project uses it to install Docker, clone the repo, and start the app — so the site is live immediately after `terraform apply`, with no manual setup on the box.
- **Terraform state** (`terraform.tfstate`) — a file Terraform keeps to track what it created, including real secrets (see section 5). It lives in an S3 bucket, not as a local file on your machine — see section 5 for why and how that's set up.
- **Remote backend** — instead of Terraform's default (a state file that only exists on your laptop), a remote backend stores state somewhere shared and durable — here, an S3 bucket — so anyone with access can run Terraform against the same infrastructure, and it's backed up instead of being a single point of failure.
- **State locking** — a safeguard that stops two `terraform apply`/`destroy` runs from happening at the same time and corrupting the state file. Here it's implemented with a small DynamoDB table.

## 3. Trade-offs made here (read this before you're surprised later)

- **No managed database (RDS).** Postgres runs in a container on the same EC2 instance, exactly like local dev. This means the database's data lives on that instance's disk — if the instance is ever replaced (e.g. because `user_data` changed), **the data is lost**. Fine for a learning project with no real data; a real production setup would use RDS instead. That's a natural next step once you're comfortable with what's here.
- **No container registry (ECR).** Deploying doesn't build a Docker image and push it anywhere — GitHub Actions just SSHes into the server and rebuilds the image from source there (`docker compose up -d --build`), the same way you'd do it locally. Simpler and needs zero AWS credentials in GitHub, but slower per deploy since it rebuilds from scratch every time. Also a natural next step later.
- **No load balancer, no HTTPS, no custom domain.** You'll access the app over plain HTTP at `http://<ip>:5000`.
- **The `/admin` section still has no authentication at all** (a separate, pre-existing limitation of this app, not something introduced by deploying it) — deploying to a public server makes this more consequential than running it locally, since it's now reachable by anyone who finds the IP.

## 4. Prerequisites (do these once)

1. **Create an AWS account** if you don't have one, and set a budget alert (Billing → Budgets) so you get an email if spend ever leaves the free tier.
2. **Create an IAM user** for yourself to use from the command line — don't use your AWS account's root login for this. In the AWS Console: IAM → Users → Create user → attach a policy with EC2 permissions (e.g. `AmazonEC2FullAccess` is the simplest to start with) → create an access key for it. Root credentials can do literally anything to your account with no way to limit the damage if they ever leak; an IAM user's permissions can be scoped down and revoked independently.
3. **Install the AWS CLI**, then run `aws configure` and paste in that IAM user's access key ID and secret. For the region prompt, use a real region code like `us-east-1` — not a human-readable name like "Oregon"; the CLI needs the code, not the console's display name.
4. **Install Terraform** (the `terraform` command).
5. **Generate an SSH key pair** you'll use to reach the server:
   ```
   ssh-keygen -t ed25519 -f ~/.ssh/api-library
   ```
   This creates `~/.ssh/api-library` (private — never share this) and `~/.ssh/api-library.pub` (public — Terraform uploads this one to AWS).
6. **Find your own public IP** (search "what is my ip") — you'll need it as `allowed_ssh_cidr` below, as `<your-ip>/32`.
7. **Attach S3 and DynamoDB permissions to your IAM user.** Terraform now needs to read/write an S3 bucket and a DynamoDB table to manage its own state (see section 5). In the AWS Console: IAM → Users → your user → Add permissions → attach `AmazonS3FullAccess` and `AmazonDynamoDBFullAccess`, the same way you attached `AmazonEC2FullAccess` in step 2.

## 5. Setting up remote state storage (once)

Terraform needs somewhere to keep track of what it's created. By default that's a local file, which only one machine can see and which isn't backed up. This project instead stores that file in S3, with a DynamoDB table used to prevent two people running Terraform at the same time from corrupting it.

Since a backend can't be configured to create the bucket it depends on, that bucket (and the lock table) come from a tiny separate Terraform config in `terraform/bootstrap/`, run once:

```
cd terraform/bootstrap
terraform init
terraform apply
```

This creates the S3 bucket and DynamoDB table and prints their names. Read them back any time with:

```
terraform output bucket_name
terraform output table_name
```

Copy both into the `backend "s3" {}` block in `terraform/provider.tf`, replacing the placeholder bucket name (`api-library-tfstate-XXXXXXXXXXXX`) with the real one.

Then go back to the main config and re-initialize:

```
cd ..
terraform init
```

Terraform will notice the new backend block and ask whether to migrate existing state into it. Since no state exists yet in this project (no one's completed an `apply` before this point), there's nothing to migrate — this prompt is just Terraform initializing fresh into S3. Answer "yes" and it's done; you only ever do this once.

## 6. Provisioning the infrastructure

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

## 7. Getting the app's URL

```
terraform output app_url
```

Give the instance a minute or two after `apply` finishes — `user_data` is still installing Docker and building the app in the background the first time.

## 8. Setting up automatic deploys

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**, add two:

- `EC2_SSH_PRIVATE_KEY` — the full contents of your private key file (`~/.ssh/api-library`, not the `.pub` one).
- `EC2_HOST` — the output of `terraform output instance_public_ip`.

From then on, every push to `main` runs `.github/workflows/deploy.yml`, which SSHes in and redeploys.

### Requiring your approval before each deploy

By default, a push to `main` deploys immediately once the secrets above are set. To require a manual approval click first:

In your GitHub repo: **Settings → Environments → New environment** → name it `production` → under **Required reviewers**, add yourself → **Save protection rules**.

From then on, every run of the `Deploy` workflow pauses with a "Waiting for review" status instead of running immediately — go to the **Actions** tab, open the run, and click **Review deployments → Approve and deploy** to let it proceed. This is a manual one-time setup step in GitHub's UI (not something the workflow YAML alone can create) — the `environment: production` line already in `deploy.yml` is what tells the workflow to check for this gate.

## 9. Tearing it down

```
cd terraform
terraform destroy
```

This deletes everything Terraform created — including the database container and its data (see the trade-off above). It's the way to make sure you're not paying for anything once you're done experimenting; there's nothing left running afterward.

Note this only tears down the main config — it does **not** delete the S3 bucket/DynamoDB table from `terraform/bootstrap/` (and shouldn't; that bucket has `force_destroy` disabled specifically so it can't be deleted while it still holds your state). If you truly want everything gone, empty the bucket by hand first, then `cd terraform/bootstrap && terraform destroy`.

## 10. Where to learn more

- HashiCorp's official "Get Started - AWS" tutorial (on developer.hashicorp.com) covers the same core Terraform concepts used here in more depth.
- AWS's own EC2 getting-started documentation is worth reading if you want to understand more of what's happening under the hood beyond what Terraform abstracts away.
