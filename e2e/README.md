# Python Playwright E2E Tests

This suite validates:
- Frontend booking flow
- API create/list/conflict behavior
- Database persistence and duration logic

## Install

```bash
cd /Users/vinayakbhatte/projects/salon-booking
python3 -m venv .e2e-venv
source .e2e-venv/bin/activate
pip install -r e2e/requirements.txt
python -m playwright install chromium
```

## Run

```bash
pytest -v e2e
```

### Local mode

Local mode is the default. It will:
- run `alembic upgrade head`
- start the local FastAPI backend from `backend/.venv`
- start the local Vite frontend
- target localhost URLs

```bash
TEST_ENV=local pytest -v e2e
```

### AWS deployed mode

AWS mode will:
- not run Alembic
- not start local frontend/backend processes
- target deployed URLs from environment variables
- skip DB-coupled tests unless `E2E_DATABASE_URL` or `DATABASE_URL` is provided

Example:

```bash
set -a
source e2e/.env.test.aws
set +a
.e2e-venv/bin/pytest -v e2e
```

### AWS smoke suite

Use the dedicated AWS-safe smoke suite for EC2 / CI runners when you want
frontend and backend validation without direct database access.

It:
- runs only when `TEST_ENV=aws`
- does not start local services
- does not require `E2E_DATABASE_URL`
- avoids direct DB cleanup
- validates deployed frontend, backend health, and low-risk public endpoints
- uses isolated customer signup data for one safe write-path smoke check

Example:

```bash
set -a
source e2e/.env.test.aws
set +a
backend/.venv/bin/python -m pytest e2e/test_smoke_aws.py -v --html=reports/aws_smoke_report.html --self-contained-html
```

## Optional environment variables

- `E2E_FRONTEND_URL` (default: `http://127.0.0.1:5173`)
- `E2E_API_URL` (default: `http://127.0.0.1:8000`)
- `E2E_DATABASE_URL` (default: `postgresql://salon:salonpass@127.0.0.1:5433/salon_db`)
- `TEST_ENV` (`local` or `aws`)

By default the fixtures will start:
- frontend Vite app
- backend migrations + FastAPI app
