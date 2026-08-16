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

# --- 5. Write the .env file docker-compose.yml reads via $${VAR} substitution ---
cat > /home/ec2-user/${project_dir}/.env <<EOF
SECRET_KEY=${secret_key}
POSTGRES_PASSWORD=${db_password}
DATABASE_URL=postgresql+psycopg2://postgres:${db_password}@db:5432/library
FLASK_DEBUG=0
EOF
chown ec2-user:ec2-user /home/ec2-user/${project_dir}/.env
chmod 600 /home/ec2-user/${project_dir}/.env

# --- 6. First build & start, so the site is live right after `terraform apply` ---
cd /home/ec2-user/${project_dir}
docker compose up -d --build
