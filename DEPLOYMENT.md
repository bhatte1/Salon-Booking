# Deployment Guide

This document explains how to deploy the salon booking app without committing secrets, passwords, tokens, or AWS credentials.

## Architecture

- React frontend hosted on AWS Amplify
- FastAPI backend running in Docker on an AWS EC2 instance
- PostgreSQL hosted on AWS RDS

## Before You Deploy

1. Never commit real `.env` files, AWS credentials, JWT secrets, database passwords, or API tokens.
2. Use [backend/.env.example](backend/.env.example) and [frontend/.env.example](frontend/.env.example) as templates only.
3. Make sure your GitHub repository contains the latest source code and deployment files:
   - `backend/Dockerfile`
   - `backend/requirements.txt`
   - `amplify.yml`

## 1. Deploy React Frontend to AWS Amplify

### GitHub connection

1. Open AWS Amplify.
2. Choose `New app` -> `Host web app`.
3. Connect your GitHub repository.
4. Select the branch you want Amplify to deploy.

### Build settings

This repository includes a root [amplify.yml](amplify.yml), so Amplify can build the frontend automatically from the `frontend/` directory.

### Amplify environment variables

In Amplify, add:

```env
VITE_API_BASE_URL=https://your-backend-domain-or-ec2-dns
```

After that, trigger a build and deploy.

## 2. Deploy FastAPI Backend to AWS EC2 Using Docker

### Launch and prepare EC2

1. Launch an EC2 instance running Ubuntu.
2. SSH into the instance.
3. Install Docker:

```bash
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

Log out and back in if needed after updating Docker group membership.

### Copy the application

Clone the repository on the EC2 instance:

```bash
git clone <your-repo-url>
cd salon-booking/backend
```

### Create backend environment file

Create a real `.env` from [backend/.env.example](backend/.env.example):

```bash
cp .env.example .env
```

Update:

- `DATABASE_URL` to point to your RDS PostgreSQL instance
- `SECRET_KEY` to a strong random value
- `CORS_ORIGINS` to your Amplify domain and any custom frontend domains
- `COOKIE_SECURE=true`
- `COOKIE_SAMESITE=none`

### Build and run Docker container

```bash
docker build -t salon-backend .
docker run -d \
  --name salon-backend \
  --restart unless-stopped \
  --env-file .env \
  -p 8000:8000 \
  salon-backend
```

### Reverse proxy and TLS

For production, place Nginx or another reverse proxy in front of the container and terminate HTTPS there. Your frontend should call the HTTPS backend URL, not the raw EC2 HTTP port.

## 3. Deploy PostgreSQL to AWS RDS

### Create the database

1. Create a PostgreSQL RDS instance.
2. Create a database such as `salon_db`.
3. Create a database user with minimum required permissions.
4. Make sure the EC2 security group can reach the RDS security group on port `5432`.

### Backend connection string

Use a connection string like:

```env
DATABASE_URL=postgresql+psycopg://app_user:strong_password@your-rds-endpoint:5432/salon_db
```

Do not commit this value to git.

## 4. Run Alembic Migrations Against Cloud PostgreSQL

After the EC2 host has the backend source and `.env` file in place, run migrations against RDS:

```bash
cd salon-booking/backend
docker build -t salon-backend .
docker run --rm --env-file .env salon-backend alembic upgrade head
```

This uses the same backend image and the `DATABASE_URL` from `.env` to migrate the cloud PostgreSQL database.

If you prefer running from a Python virtual environment instead of Docker:

```bash
cd salon-booking/backend
source .venv/bin/activate
alembic upgrade head
```

## 5. CORS for Production

The backend reads `CORS_ORIGINS` from the environment as a comma-separated list.

Example:

```env
CORS_ORIGINS=https://main.d123.amplifyapp.com,https://app.yourdomain.com
```

If your frontend domain changes, update this value and restart the backend container.

## 6. Deployment Checklist

Before going live, verify:

- Amplify has `VITE_API_BASE_URL` configured
- EC2 has a valid backend `.env`
- RDS allows traffic from the EC2 instance
- Alembic migrations ran successfully
- `SECRET_KEY` is strong and unique
- `COOKIE_SECURE=true` in production
- `CORS_ORIGINS` includes only trusted frontend domains
- No secrets or AWS credentials are committed to the repository

## 7. Useful Commands

View backend container logs:

```bash
docker logs -f salon-backend
```

Restart backend container:

```bash
docker restart salon-backend
```

Run migrations after a new deployment:

```bash
docker run --rm --env-file .env salon-backend alembic upgrade head
```
