from __future__ import annotations

from datetime import datetime

import psycopg
import requests

from e2e.utils import api_url, cleanup_by_email_and_service, db_url, future_iso, unique_marker


def test_database_end_time_duration_matches_service_minutes():
    marker = unique_marker("db")
    service_name = f"DB Check {marker}"
    email = f"qa+{marker}@example.com"

    try:
        service_res = requests.post(
            f"{api_url()}/api/services",
            json={"name": service_name, "price_cents": 5200, "duration_minutes": 30},
            timeout=10,
        )
        assert service_res.status_code == 200
        service = service_res.json()

        appointment_res = requests.post(
            f"{api_url()}/api/appointments",
            json={
                "customer_name": f"DB User {marker}",
                "customer_email": email,
                "service_id": service["id"],
                "start_time": future_iso(300),
                "notes": f"db-check-{marker}",
            },
            timeout=10,
        )
        assert appointment_res.status_code == 200
        appointment_id = appointment_res.json()["id"]

        with psycopg.connect(db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT service_id, customer_email, start_time, end_time
                    FROM appointments
                    WHERE id = %s
                    """,
                    (appointment_id,),
                )
                row = cur.fetchone()

        assert row is not None
        assert row[0] == service["id"]
        assert row[1] == email

        start = row[2]
        end = row[3]
        assert isinstance(start, datetime)
        assert isinstance(end, datetime)

        diff_minutes = int((end - start).total_seconds() // 60)
        assert diff_minutes == 30
    finally:
        cleanup_by_email_and_service(email=email, service_name=service_name)
