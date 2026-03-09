from __future__ import annotations

import os
import random
import time
from datetime import datetime, timedelta

import psycopg


def frontend_url() -> str:
    return os.getenv("E2E_FRONTEND_URL", "http://127.0.0.1:5173")


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
