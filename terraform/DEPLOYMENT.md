# Deployment Runbook — QueryGen AI on AWS EC2

This document describes the deployment process for provisioning and running QueryGen AI on AWS infrastructure using the Terraform configuration in this directory.

## Prerequisites
- AWS account with active billing and free-tier eligibility (or budget approved for t3.micro usage)
- AWS CLI configured locally with valid credentials (`aws configure`)
- An EC2 key pair created in the target region, named `querygen-ai-key`
- Terraform installed locally (v1.5+)

## Step 1: Provision Infrastructure
```bash
cd terraform
terraform init
terraform plan
terraform apply
```
This provisions:
- One `t3.micro` EC2 instance (Ubuntu 22.04 LTS)
- A security group allowing inbound SSH (22) and HTTP (80)
- Docker and Docker Compose auto-installed via the instance's `user_data` startup script

On completion, Terraform outputs the instance's public IP address.

## Step 2: Deploy the Application
SSH into the provisioned instance:
```bash
ssh -i querygen-ai-key.pem ubuntu@<instance_public_ip>
```

Clone the application repository:
```bash
git clone https://github.com/PendemNikhitha/querygen-ai.git
cd querygen-ai
```

Create the production `.env` file with live credentials (never committed to source control):
```bash
nano .env
# Paste MONGO_URI, JWT_SECRET, PINECONE_API_KEY, GROQ_API_KEY
```

Start the application stack:
```bash
docker compose up -d --build
```

## Step 3: Verify Deployment
```bash
docker compose ps
curl http://localhost
```
The application should be reachable at `http://<instance_public_ip>`.

## Step 4: Teardown (Cost Control)
When the instance is no longer needed:
```bash
terraform destroy
```
This removes all provisioned AWS resources to avoid ongoing charges.

## Notes
- This deployment was designed and validated architecturally but not executed live, due to AWS free-tier account expiry at the time of this project.
- The Docker Compose configuration is identical to the one validated in local development, ensuring environment parity between local and cloud deployment.