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

## Optional environment variables

- `E2E_FRONTEND_URL` (default: `http://127.0.0.1:5173`)
- `E2E_API_URL` (default: `http://127.0.0.1:8000`)
- `E2E_DATABASE_URL` (default: `postgresql://salon:salonpass@127.0.0.1:5433/salon_db`)

By default the fixtures will start:
- frontend Vite app
- backend migrations + FastAPI app
