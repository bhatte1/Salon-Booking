# Salon Booking

A full-stack salon booking application with a React/Vite frontend, a FastAPI backend, PostgreSQL persistence, and Playwright/Pytest end-to-end coverage.

## Overview

This project supports:

- Customer sign up and login
- Owner login
- Service browsing and appointment booking
- Service availability lookup by date
- Customer appointment history
- Owner appointment review and status updates
- Forgot password and forgot username flows
- End-to-end testing across frontend, API, and database behavior

## Tech Stack

- Frontend: React 19, React Router, Vite
- Backend: FastAPI, SQLAlchemy, Alembic
- Database: PostgreSQL 16
- Auth: JWT plus HTTP-only auth cookie support
- Testing: Pytest and Playwright

## Repository Structure

```text
backend/    FastAPI app, models, API routes, Alembic migrations
frontend/   React/Vite client
e2e/        End-to-end, API, and database tests
security/   HTML pentest and retest reports
```

## Prerequisites

- Node.js 18+
- Python 3.9+
- Docker and Docker Compose
- PostgreSQL client tools are helpful but optional

## Environment

The backend reads configuration from `backend/.env`.

Minimum variables expected by the backend:

```env
DATABASE_URL=postgresql://salon:salonpass@127.0.0.1:5433/salon_db
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

The frontend can optionally use:

```env
VITE_API_BASE=http://localhost:8000
```

If `VITE_API_BASE` is not set, the frontend defaults to `http://<current-host>:8000`.

## Local Setup

### 1. Start PostgreSQL

```bash
docker compose up -d
```

This starts PostgreSQL on `127.0.0.1:5433`.

### 2. Set up the backend

There is currently no committed backend `requirements.txt` or `pyproject.toml`, so backend dependencies must be installed from your local environment or captured into a dependency file.

Core packages used by the backend include:

- `fastapi`
- `uvicorn`
- `sqlalchemy`
- `alembic`
- `pydantic-settings`
- `passlib`
- `python-jose`
- `psycopg` or `psycopg2`

Typical local flow:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

Run migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

### 3. Set up the frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://127.0.0.1:5173`.

## Testing

### Frontend/API/DB E2E suite

See [e2e/README.md](e2e/README.md) for the full Playwright/Pytest setup.

Quick start:

```bash
python3 -m venv .e2e-venv
source .e2e-venv/bin/activate
pip install -r e2e/requirements.txt
python -m playwright install chromium
pytest -v e2e
```

## API Highlights

Main route groups:

- `GET /health`
- `POST /api/auth/signup/customer`
- `POST /api/auth/login/customer`
- `POST /api/auth/login/owner`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `POST /api/auth/forgot-password`
- `POST /api/auth/forgot-username`
- `POST /api/auth/reset-password`
- `GET /api/services`
- `POST /api/services`
- `GET /api/appointments/availability`
- `POST /api/appointments/me`
- `GET /api/appointments/me/list`
- `GET /api/appointments/owner/all`

## Notes

- Customer booking currently creates an appointment for one active service at a time.
- The customer dashboard UI supports multi-select service selection, but booking still uses the currently active selected service.
- `security/` contains generated pentest reports.
- This repo currently includes generated files such as virtualenv contents and `__pycache__` artifacts in git history.

## Recommended README Improvements

If this project continues, the next documentation improvements should be:

1. Add a committed backend dependency manifest such as `requirements.txt` or `pyproject.toml`.
2. Add seed-data instructions for owner and service creation.
3. Document the expected local `.env` values more formally.
4. Add screenshots or short GIFs of the main booking flows.
5. Add deployment instructions for frontend, backend, and database.
