from __future__ import annotations

import os
import random
import time
from datetime import datetime, timedelta

import psycopg
import requests


def frontend_url() -> str:
    return os.getenv("E2E_FRONTEND_URL", "http://localhost:5173")


def api_url() -> str:
    return os.getenv("E2E_API_URL", "http://127.0.0.1:8000")


def _normalize_db_url(raw: str | None) -> str:
    if not raw:
        return "postgresql://salon:salonpass@127.0.0.1:5433/salon_db"
    return raw.replace("postgresql+psycopg://", "postgresql://")


def db_url() -> str:
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
