# API Test Framework

Playwright-based API automation for the Salon Booking backend lives in `tests/api`.

## Coverage

- Auth:
  - customer signup
  - customer login
  - invalid login
  - get current user with JWT token
  - owner login
- Services:
  - get services
- Appointments:
  - book appointment
  - get my appointments
  - book appointment with unknown service
  - reject booking in the past
  - reject overlapping bookings
  - require auth for customer appointment list
  - block customer access to owner appointment list
  - allow owner access to all appointments

## Run Locally

Start the app stack first, then run:

```bash
pytest tests/api -q
```

Or from the repo root:

```bash
make test-api
```

## Environment Variables

- `TEST_API_BASE_URL`
- `TEST_DATABASE_URL`

The framework falls back to:

- `E2E_API_URL`
- `E2E_DATABASE_URL`
- `DATABASE_URL`

## Optional HTML Report

Install:

```bash
pip install pytest-html
```

Run:

```bash
pytest tests/api -q --html=reports/api-report.html --self-contained-html
```

## Optional Allure Report

Install:

```bash
pip install allure-pytest
```

Run:

```bash
pytest tests/api -q --alluredir=reports/allure-results
```

Then generate/view with your local Allure CLI:

```bash
allure serve reports/allure-results
```

Repo-root shortcuts:

```bash
make test-api-allure
make allure-report
make serve-allure
```
