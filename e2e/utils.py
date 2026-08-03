from __future__ import annotations

import logging
import os
import random
import time
from datetime import datetime, timedelta

import requests

LOGGER = logging.getLogger(__name__)


LOCAL_TEST_ENV = "local"
AWS_TEST_ENV = "aws"


def test_env() -> str:
    return os.getenv("TEST_ENV", LOCAL_TEST_ENV).strip().lower()


def is_local_env() -> bool:
    return test_env() == LOCAL_TEST_ENV


def is_aws_env() -> bool:
    return test_env() == AWS_TEST_ENV


def database_access_enabled() -> bool:
    if is_local_env():
        return True
    return bool(os.getenv("E2E_DATABASE_URL") or os.getenv("DATABASE_URL"))


def require_database_access() -> None:
    if database_access_enabled():
        return
    raise RuntimeError(
        "Database access is not configured for this test run. "
        "Set E2E_DATABASE_URL (or DATABASE_URL) to enable DB-backed cleanup and validation."
    )


def frontend_url() -> str:
    default = "http://127.0.0.1:5173" if is_local_env() else ""
    return os.getenv("E2E_FRONTEND_URL", default).rstrip("/")


def api_url() -> str:
    default = "http://127.0.0.1:8000" if is_local_env() else ""
    return os.getenv("E2E_API_URL", default).rstrip("/")


def current_environment_summary() -> dict[str, str | bool]:
    return {
        "test_env": test_env(),
        "frontend_url": frontend_url(),
        "api_url": api_url(),
        "database_access_enabled": database_access_enabled(),
    }


def _normalize_db_url(raw: str | None) -> str:
    if not raw:
        return "postgresql://salon:salonpass@127.0.0.1:5433/salon_db"
    return raw.replace("postgresql+psycopg://", "postgresql://")


def db_url() -> str:
    require_database_access()
    return _normalize_db_url(
        os.getenv("E2E_DATABASE_URL") or os.getenv("DATABASE_URL")
    )


def unique_marker(prefix: str = "e2e") -> str:
    return f"{prefix}-{int(time.time() * 1000)}-{random.randint(1000, 99999)}"


def future_iso(minutes_from_now: int = 120) -> str:
    dt = datetime.utcnow() + timedelta(minutes=minutes_from_now)
    return dt.replace(microsecond=0).isoformat() + "Z"


def future_datetime_local(minutes_from_now: int = 120) -> str:
    dt = datetime.now() + timedelta(minutes=minutes_from_now)
    return dt.strftime("%Y-%m-%dT%H:%M")


def business_time_iso(*, days_from_now: int = 1, hour: int = 10, minute: int = 0) -> str:
    dt = datetime.now() + timedelta(days=days_from_now)
    dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return dt.isoformat()


def business_date_local(days_from_now: int = 1) -> str:
    dt = datetime.now() + timedelta(days=days_from_now)
    return dt.strftime("%Y-%m-%d")


def cleanup_by_email_and_service(*, email: str | None = None, service_name: str | None = None) -> None:
    require_database_access()
    import psycopg

    with psycopg.connect(db_url()) as conn:
        with conn.cursor() as cur:
            if email:
                cur.execute("DELETE FROM appointments WHERE customer_email = %s", (email,))
            if service_name:
                cur.execute(
                    """
                    DELETE FROM services
                    WHERE name = %s
                    AND NOT EXISTS (
                        SELECT 1
                        FROM appointments a
                        WHERE a.service_id = services.id
                    )
                    """,
                    (service_name,),
                )
        conn.commit()


TEST_OWNER_PASSWORD = "OwnerPass123!"
TEST_OWNER_PASSWORD_HASH = (
    "$2b$12$l8tab5MBcvijnTJhJCF1ce5FyJvNbtuVtJ6lGeL4DM6PFTptOaS4i"
)


def create_service(*, name: str, price_cents: int = 4500, duration_minutes: int = 45) -> dict:
    response = requests.post(
        f"{api_url()}/api/services",
        json={
            "name": name,
            "price_cents": price_cents,
            "duration_minutes": duration_minutes,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def signup_customer(*, full_name: str, email: str, username: str, password: str) -> dict:
    response = requests.post(
        f"{api_url()}/api/auth/signup/customer",
        json={
            "full_name": full_name,
            "email": email,
            "username": username,
            "password": password,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def login_customer(*, username_or_email: str, password: str) -> dict:
    response = requests.post(
        f"{api_url()}/api/auth/login/customer",
        json={"username_or_email": username_or_email, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def login_owner(*, username_or_email: str, password: str) -> dict:
    response = requests.post(
        f"{api_url()}/api/auth/login/owner",
        json={"username_or_email": username_or_email, "password": password},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def create_owner_user(*, full_name: str, email: str, username: str) -> None:
    require_database_access()
    import psycopg

    with psycopg.connect(db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (full_name, email, username, hashed_password, role, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (email) DO NOTHING
                """,
                (
                    full_name,
                    email,
                    username,
                    TEST_OWNER_PASSWORD_HASH,
                    "owner",
                    True,
                ),
            )
        conn.commit()


def cleanup_test_data(
    *,
    emails: list[str] | None = None,
    usernames: list[str] | None = None,
    service_names: list[str] | None = None,
) -> None:
    require_database_access()
    import psycopg

    emails = emails or []
    usernames = usernames or []
    service_names = service_names or []

    with psycopg.connect(db_url()) as conn:
        with conn.cursor() as cur:
            for email in emails:
                cur.execute("DELETE FROM appointments WHERE customer_email = %s", (email,))

            for username in usernames:
                cur.execute("DELETE FROM users WHERE username = %s", (username,))

            for email in emails:
                cur.execute("DELETE FROM users WHERE email = %s", (email,))

            for service_name in service_names:
                cur.execute(
                    """
                    DELETE FROM services
                    WHERE name = %s
                    AND NOT EXISTS (
                        SELECT 1
                        FROM appointments a
                        WHERE a.service_id = services.id
                    )
                    """,
                    (service_name,),
                )

        conn.commit()
