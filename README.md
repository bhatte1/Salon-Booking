# Salon Booking

A full-stack salon booking project with a React frontend, a FastAPI backend, and PostgreSQL for persistence.

## Stack

- Frontend: React + Vite
- Backend: FastAPI + SQLAlchemy + Alembic
- Database: PostgreSQL 16

## Project Structure

```text
backend/    API, database models, migrations
frontend/   React client
```

## Prerequisites

- Node.js 18+
- Python 3.9+
- Docker

## Run Locally

### 1. Start PostgreSQL

```bash
docker compose up -d
```

This starts Postgres on `localhost:5433`.

### 2. Configure the backend

The backend reads settings from `backend/.env`.

Example:

```env
DATABASE_URL=postgresql://salon:salonpass@127.0.0.1:5433/salon_db
```

### 3. Run the backend

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

Health check:

```bash
curl http://127.0.0.1:8000/health
```

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://127.0.0.1:5173`.

## API Areas

- `GET /health`
- `GET /api/services`
- `POST /api/services`
- `GET /api/appointments`
- `POST /api/appointments`

## Notes

- The backend currently expects a local Python virtual environment in `backend/.venv/`.
- The frontend README inside `frontend/` still contains the default Vite template notes and can be refined later.

## Suggested Next Improvements

1. Add a committed backend dependency file such as `requirements.txt` or `pyproject.toml`.
2. Add seed data instructions for sample services.
3. Document environment variables more fully.
4. Add screenshots of the main booking flow.
