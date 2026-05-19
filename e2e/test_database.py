from __future__ import annotations

from datetime import datetime

import psycopg
import requests
import pytest

from e2e.utils import (
    TEST_OWNER_PASSWORD,
    api_url,
    business_time_iso,
    cleanup_test_data,
    create_owner_user,
    create_service,
    db_url,
    login_customer,
    login_owner,
    signup_customer,
    unique_marker,
)

pytestmark = pytest.mark.requires_db


def test_database_end_time_duration_matches_service_minutes():
    marker = unique_marker("db")
    service_name = f"DB Check {marker}"
    email = f"qa+{marker}@example.com"

    try:
        service = create_service(name=service_name, price_cents=5200, duration_minutes=30)

        appointment_res = requests.post(
            f"{api_url()}/api/appointments",
            json={
                "customer_name": f"DB User {marker}",
                "customer_email": email,
                "service_id": service["id"],
                "start_time": business_time_iso(days_from_now=1, hour=9, minute=0),
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
        assert diff_minutes == service["duration_minutes"]
    finally:
        cleanup_test_data(emails=[email], service_names=[service_name])


def test_database_authenticated_booking_links_user_and_defaults_status_pending():
    marker = unique_marker("db-auth")
    service_name = f"DB Auth Service {marker}"
    email = f"qa+{marker}@example.com"
    username = f"user_{marker.replace('-', '_')}"
    password = "CustomerPass123!"
    full_name = f"DB Auth User {marker}"

    try:
        service = create_service(name=service_name, duration_minutes=75)
        signup_customer(
            full_name=full_name,
            email=email,
            username=username,
            password=password,
        )
        login_data = login_customer(username_or_email=username, password=password)
        token = login_data["access_token"]
        user_id = login_data["user"]["id"]

        appointment_res = requests.post(
            f"{api_url()}/api/appointments/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "service_id": service["id"],
                "start_time": business_time_iso(days_from_now=1, hour=10, minute=0),
                "notes": f"db-auth-note-{marker}",
            },
            timeout=10,
        )
        assert appointment_res.status_code == 200
        appointment_id = appointment_res.json()["id"]

        with psycopg.connect(db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT user_id, customer_name, customer_email, status, notes
                    FROM appointments
                    WHERE id = %s
                    """,
                    (appointment_id,),
                )
                row = cur.fetchone()

        assert row is not None
        assert row[0] == user_id
        assert row[1] == full_name
        assert row[2] == email
        assert row[3] == "pending"
        assert row[4] == f"db-auth-note-{marker}"
    finally:
        cleanup_test_data(
            emails=[email],
            usernames=[username],
            service_names=[service_name],
        )


def test_database_owner_status_update_is_persisted():
    marker = unique_marker("db-status")
    service_name = f"DB Status Service {marker}"
    customer_email = f"qa+{marker}@example.com"
    owner_email = f"owner+{marker}@example.com"
    owner_username = f"owner_{marker.replace('-', '_')}"

    try:
        service = create_service(name=service_name, duration_minutes=45)
        create_owner_user(
            full_name=f"Owner {marker}",
            email=owner_email,
            username=owner_username,
        )
        owner_login = login_owner(
            username_or_email=owner_username,
            password=TEST_OWNER_PASSWORD,
        )
        owner_token = owner_login["access_token"]

        appointment_res = requests.post(
            f"{api_url()}/api/appointments",
            json={
                "customer_name": f"DB Status User {marker}",
                "customer_email": customer_email,
                "service_id": service["id"],
                "start_time": business_time_iso(days_from_now=1, hour=11, minute=0),
                "notes": "status-persistence-check",
            },
            timeout=10,
        )
        assert appointment_res.status_code == 200
        appointment_id = appointment_res.json()["id"]

        update_res = requests.patch(
            f"{api_url()}/api/appointments/owner/{appointment_id}/status",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"status": "completed"},
            timeout=10,
        )
        assert update_res.status_code == 200
        assert update_res.json()["status"] == "completed"

        with psycopg.connect(db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT status FROM appointments WHERE id = %s",
                    (appointment_id,),
                )
                status = cur.fetchone()

        assert status is not None
        assert status[0] == "completed"
    finally:
        cleanup_test_data(
            emails=[customer_email, owner_email],
            usernames=[owner_username],
            service_names=[service_name],
        )
