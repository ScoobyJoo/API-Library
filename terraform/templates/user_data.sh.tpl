#!/bin/bash
# This script runs automatically, once, the first time the EC2 instance
# boots (as root, via AWS's "user data" mechanism / cloud-init). It sets
# the box up from nothing to "the app is live" with no manual steps.
#
# $${...} placeholders below are filled in by Terraform's templatefile()
# BEFORE this script ever reaches the instance - by the time it runs on
# EC2, they're just plain text. If you ever need a literal '$' in this
# script, it has to be written as '$$' so Terraform doesn't try to
# interpolate it.
#
# If something here goes wrong, the full output is logged on the
# instance at /var/log/cloud-init-output.log - SSH in and check there.

set -euxo pipefail
# -e: stop on the first error   -u: error on unset variables
# -x: log every command as it runs, so the log file above is genuinely
#     useful for debugging instead of just showing the final failure

# --- 1. System packages ---
dnf update -y
dnf install -y docker git

# --- 2. Start Docker, and let ec2-user run docker commands without sudo ---
systemctl enable --now docker
usermod -aG docker ec2-user

# --- 3. Install the Docker Compose CLI plugin ---
# Amazon Linux 2023 doesn't reliably ship `docker compose` via dnf, so we
# install the plugin binary directly - the same method Docker's own docs
# recommend, and it works identically on any Linux distro.
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# --- 3b. Install a current Buildx CLI plugin ---
# `docker compose up --build` delegates the actual image build to Buildx,
# not to the older classic `docker build`. Recent Compose plugin versions
# require Buildx >= 0.17.0, but AL2023's base `docker` package (installed
# above) bundles one too old to satisfy that - without this step, any
# `--build` fails with "compose build requires buildx 0.17.0 or later".
# Buildx's release assets are named with the version in the filename (unlike
# Compose's), so the latest tag has to be looked up first.
BUILDX_VERSION=$(curl -s https://api.github.com/repos/docker/buildx/releases/latest | grep '"tag_name":' | cut -d'"' -f4)
curl -SL "https://github.com/docker/buildx/releases/download/$${BUILDX_VERSION}/buildx-$${BUILDX_VERSION}.linux-amd64" \
  -o /usr/local/lib/docker/cli-plugins/docker-buildx
chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx

# --- 4. Clone the app repo ---
sudo -u ec2-user git clone ${repo_url} /home/ec2-user/${project_dir}

# --- 4b. Install AWS CLI v2 and jq ---
# Same "install the binary directly" pattern already needed for Docker
# Compose and Buildx above - AL2023's dnf-packaged `awscli` is old/
# unreliable, so this uses AWS's own documented cross-distro install
# method instead. `unzip` is required to extract it and isn't included
# on AL2023 by default. `jq` (a command-line JSON parser) IS reliably
# available via dnf here, unlike the other three - it's only needed
# below, to pull the "password" field back out of the JSON blob Secrets
# Manager returns.
dnf install -y unzip jq
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install

# --- 5. Fetch the REAL master password from Secrets Manager ---
# rds.tf's manage_master_user_password = true means Terraform never
# generates or even sees the actual database password - AWS creates it,
# encrypts it, and stores it in Secrets Manager. This instance can read
# ONLY that one secret because of the IAM role attached above via
# iam_instance_profile (see iam.tf) - the AWS CLI picks up permission to
# make this call automatically from that role's temporary credentials,
# no access keys stored anywhere on this box.
#
# --region is passed explicitly rather than relying on the AWS CLI to
# infer it from instance metadata - that auto-detection isn't reliably
# on by default, so being explicit here avoids a flaky, hard-to-diagnose
# failure mode.
SECRET_JSON=$(aws secretsmanager get-secret-value \
  --secret-id ${db_secret_arn} \
  --region ${region} \
  --query SecretString \
  --output text)
DB_PASSWORD=$(echo "$SECRET_JSON" | jq -r .password)

# --- 6. Write the .env file docker-compose.prod.yml reads via $${VAR} substitution ---
# No POSTGRES_PASSWORD here anymore - production doesn't run its own
# Postgres container (docker-compose.prod.yml only has the "web" service),
# so there's nothing local to configure. DATABASE_URL instead points at
# the AWS-managed RDS database, over SSL (?sslmode=require) -
# psycopg2-binary (already in requirements.txt) supports this natively.
#
# IMPORTANT: $${DB_PASSWORD} below uses the same double-$ escaping as
# $${BUILDX_VERSION} earlier in this file, but for a different reason
# than the header comment at the top describes. ${secret_key}, ${db_host},
# ${db_secret_arn}, and ${region} above are Terraform-time values -
# templatefile() fills those in before this script ever reaches EC2.
# DB_PASSWORD is the opposite: a genuine bash variable that doesn't exist
# until THIS SCRIPT runs, on the instance, at boot - Terraform has never
# heard of it. Writing it as $${DB_PASSWORD} tells Terraform "leave this
# alone, render it as a literal $${DB_PASSWORD}", which bash then expands
# for real when this heredoc executes. Writing it with only one $ instead
# would make templatefile() try to substitute ITS OWN "DB_PASSWORD"
# variable, which doesn't exist, and fail at `terraform apply` time,
# before this script ever ran.
cat > /home/ec2-user/${project_dir}/.env <<EOF
SECRET_KEY=${secret_key}
DATABASE_URL=postgresql+psycopg2://postgres:$${DB_PASSWORD}@${db_host}:5432/library?sslmode=require
FLASK_DEBUG=0
EOF
chown ec2-user:ec2-user /home/ec2-user/${project_dir}/.env
chmod 600 /home/ec2-user/${project_dir}/.env

# --- 7. First build & start, so the site is live right after `terraform apply` ---
# -f docker-compose.prod.yml (instead of the bare `docker compose up`,
# which would use docker-compose.yml) picks the production-only compose
# file - just the "web" service, no local "db" container, since the
# database is now RDS.
cd /home/ec2-user/${project_dir}
docker compose -f docker-compose.prod.yml up -d --build
