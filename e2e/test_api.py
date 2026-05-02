from __future__ import annotations

import requests

from e2e.utils import (
    TEST_OWNER_PASSWORD,
    api_url,
    business_time_iso,
    cleanup_test_data,
    create_owner_user,
    create_service,
    future_iso,
    login_customer,
    login_owner,
    signup_customer,
    unique_marker,
)


def test_api_create_and_overlap_conflict():
    marker = unique_marker("api")
    service_name = f"E2E Service {marker}"
    email_a = f"qa+{marker}-a@example.com"
    email_b = f"qa+{marker}-b@example.com"

    try:
        service = create_service(name=service_name)

        payload = {
            "customer_name": f"API User {marker}",
            "customer_email": email_a,
            "service_id": service["id"],
            "start_time": business_time_iso(days_from_now=1, hour=10, minute=0),
            "notes": f"api-booking-{marker}",
        }

        create_res = requests.post(f"{api_url()}/api/appointments", json=payload, timeout=10)
        assert create_res.status_code == 200
        created = create_res.json()
        assert created["customer_email"] == email_a

        overlap_payload = {
            **payload,
            "customer_name": f"API User 2 {marker}",
            "customer_email": email_b,
        }
        overlap_res = requests.post(
            f"{api_url()}/api/appointments", json=overlap_payload, timeout=10
        )
        assert overlap_res.status_code == 409

        list_res = requests.get(f"{api_url()}/api/appointments", timeout=10)
        assert list_res.status_code == 401
    finally:
        cleanup_test_data(emails=[email_a, email_b], service_names=[service_name])


def test_api_rejects_duplicate_service_name():
    marker = unique_marker("svc")
    service_name = f"Duplicate Service {marker}"

    try:
        first_res = requests.post(
            f"{api_url()}/api/services",
            json={"name": service_name, "price_cents": 3500, "duration_minutes": 30},
            timeout=10,
        )
        assert first_res.status_code == 200

        duplicate_res = requests.post(
            f"{api_url()}/api/services",
            json={"name": service_name, "price_cents": 3600, "duration_minutes": 45},
            timeout=10,
        )
        assert duplicate_res.status_code == 409
        assert duplicate_res.json()["detail"] == "Service already exists"
    finally:
        cleanup_test_data(service_names=[service_name])


def test_api_rejects_appointment_for_unknown_service():
    marker = unique_marker("missing-service")
    email = f"qa+{marker}@example.com"

    res = requests.post(
        f"{api_url()}/api/appointments",
        json={
            "customer_name": f"Missing Service {marker}",
            "customer_email": email,
            "service_id": 99999999,
            "start_time": future_iso(180),
            "notes": "should-fail",
        },
        timeout=10,
    )

    assert res.status_code == 404
    assert res.json()["detail"] == "Service not found"


def test_api_rejects_booking_in_the_past():
    marker = unique_marker("past")
    service_name = f"Past Booking Service {marker}"
    email = f"qa+{marker}@example.com"

    try:
        service = create_service(name=service_name, duration_minutes=60)

        res = requests.post(
            f"{api_url()}/api/appointments",
            json={
                "customer_name": f"Past User {marker}",
                "customer_email": email,
                "service_id": service["id"],
                "start_time": future_iso(-30),
                "notes": "past-booking",
            },
            timeout=10,
        )

        assert res.status_code == 400
        assert res.json()["detail"] == "Cannot book in the past"
    finally:
        cleanup_test_data(emails=[email], service_names=[service_name])


def test_api_customer_can_book_and_list_their_own_appointments():
    marker = unique_marker("auth-api")
    service_name = f"Customer Service {marker}"
    email = f"qa+{marker}@example.com"
    username = f"user_{marker.replace('-', '_')}"
    password = "CustomerPass123!"

    try:
        service = create_service(name=service_name, duration_minutes=50)
        signup_customer(
            full_name=f"Customer {marker}",
            email=email,
            username=username,
            password=password,
        )
        login_data = login_customer(username_or_email=username, password=password)
        token = login_data["access_token"]

        create_res = requests.post(
            f"{api_url()}/api/appointments/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "service_id": service["id"],
                "start_time": business_time_iso(days_from_now=1, hour=11, minute=0),
                "notes": f"member-booking-{marker}",
            },
            timeout=10,
        )
        assert create_res.status_code == 200
        created = create_res.json()
        assert created["customer_email"] == email
        assert created["customer_name"] == f"Customer {marker}"
        assert created["status"] == "pending"

        list_res = requests.get(
            f"{api_url()}/api/appointments/me/list",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        assert list_res.status_code == 200
        appointments = list_res.json()
        assert any(appt["id"] == created["id"] for appt in appointments)
    finally:
        cleanup_test_data(
            emails=[email],
            usernames=[username],
            service_names=[service_name],
        )


def test_api_customer_cannot_access_owner_appointments():
    marker = unique_marker("owner-guard")
    email = f"qa+{marker}@example.com"
    username = f"user_{marker.replace('-', '_')}"
    password = "CustomerPass123!"

    try:
        signup_customer(
            full_name=f"Customer {marker}",
            email=email,
            username=username,
            password=password,
        )
        login_data = login_customer(username_or_email=email, password=password)
        token = login_data["access_token"]

        owner_res = requests.get(
            f"{api_url()}/api/appointments/owner/all",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )

        assert owner_res.status_code == 403
        assert owner_res.json()["detail"] == "Only owners can view all appointments"
    finally:
        cleanup_test_data(emails=[email], usernames=[username])


def test_api_owner_can_update_appointment_status():
    marker = unique_marker("owner-status")
    service_name = f"Owner Service {marker}"
    customer_email = f"qa+{marker}@example.com"
    owner_email = f"owner+{marker}@example.com"
    owner_username = f"owner_{marker.replace('-', '_')}"

    try:
        service = create_service(name=service_name, duration_minutes=30)
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

        create_res = requests.post(
            f"{api_url()}/api/appointments",
            json={
                "customer_name": f"Owner Review {marker}",
                "customer_email": customer_email,
                "service_id": service["id"],
                "start_time": business_time_iso(days_from_now=1, hour=12, minute=0),
                "notes": "status-update-target",
            },
            timeout=10,
        )
        assert create_res.status_code == 200
        appointment_id = create_res.json()["id"]

        update_res = requests.patch(
            f"{api_url()}/api/appointments/owner/{appointment_id}/status",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"status": "confirmed"},
            timeout=10,
        )
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["id"] == appointment_id
        assert updated["status"] == "confirmed"
    finally:
        cleanup_test_data(
            emails=[customer_email, owner_email],
            usernames=[owner_username],
            service_names=[service_name],
        )


def test_api_forgot_username_returns_username_for_existing_email():
    marker = unique_marker("forgot-username")
    email = f"qa+{marker}@example.com"
    username = f"user_{marker.replace('-', '_')}"
    missing_email = f"missing-{marker}@example.com"
    password = "CustomerPass123!"

    try:
        signup_customer(
            full_name=f"Forgot Username {marker}",
            email=email,
            username=username,
            password=password,
        )

        existing_res = requests.post(
            f"{api_url()}/api/auth/forgot-username",
            json={"email": email},
            timeout=10,
        )
        assert existing_res.status_code == 200
        existing_data = existing_res.json()

        missing_res = requests.post(
            f"{api_url()}/api/auth/forgot-username",
            json={"email": missing_email},
            timeout=10,
        )
        assert missing_res.status_code == 200
        missing_data = missing_res.json()

        assert (
            existing_data["message"]
            == "If an account with that email exists, username details have been generated."
        )
        assert missing_data["message"] == existing_data["message"]
        assert "username" not in existing_data
        assert "username" not in missing_data
    finally:
        cleanup_test_data(
            emails=[email],
            usernames=[username],
        )


def test_api_rejects_booking_outside_business_hours():
    marker = unique_marker("business-hours")
    service_name = f"Business Hours Service {marker}"
    email = f"qa+{marker}@example.com"

    try:
        service = create_service(name=service_name, duration_minutes=45)

        res = requests.post(
            f"{api_url()}/api/appointments",
            json={
                "customer_name": f"Outside Hours {marker}",
                "customer_email": email,
                "service_id": service["id"],
                "start_time": business_time_iso(days_from_now=1, hour=7, minute=30),
                "notes": "before-open",
            },
            timeout=10,
        )

        assert res.status_code == 400
        assert res.json()["detail"] == "Appointments must be within business hours (08:00 to 19:00)."
    finally:
        cleanup_test_data(emails=[email], service_names=[service_name])


def test_api_availability_returns_business_hour_slots():
    marker = unique_marker("availability")
    service_name = f"Availability Service {marker}"
    email = f"qa+{marker}@example.com"
    username = f"user_{marker.replace('-', '_')}"
    password = "CustomerPass123!"
    start_time = business_time_iso(days_from_now=1, hour=10, minute=0)
    booking_date = start_time[:10]

    try:
        service = create_service(name=service_name, duration_minutes=30)
        signup_customer(
            full_name=f"Availability User {marker}",
            email=email,
            username=username,
            password=password,
        )
        login_data = login_customer(username_or_email=username, password=password)
        token = login_data["access_token"]

        create_res = requests.post(
            f"{api_url()}/api/appointments/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "service_id": service["id"],
                "start_time": start_time,
                "notes": "availability-check",
            },
            timeout=10,
        )
        assert create_res.status_code == 200

        availability_res = requests.get(
            f"{api_url()}/api/appointments/availability",
            headers={"Authorization": f"Bearer {token}"},
            params={"service_id": service["id"], "booking_date": booking_date},
            timeout=10,
        )
        assert availability_res.status_code == 200
        payload = availability_res.json()
        slots = payload["slots"]
        assert len(slots) > 0
        assert slots[0]["start_time"] == "08:00"
        assert all("08:00" <= slot["start_time"] < "19:00" for slot in slots)
        ten_am_slot = next(slot for slot in slots if slot["start_time"] == "10:00")
        assert ten_am_slot["available"] is False
    finally:
        cleanup_test_data(
            emails=[email],
            usernames=[username],
            service_names=[service_name],
        )


def test_api_forgot_password_does_not_expose_reset_link():
    marker = unique_marker("forgot-password")
    email = f"qa+{marker}@example.com"
    username = f"user_{marker.replace('-', '_')}"
    password = "CustomerPass123!"
    missing_email = f"missing-{marker}@example.com"

    try:
        signup_customer(
            full_name=f"Forgot Password {marker}",
            email=email,
            username=username,
            password=password,
        )

        existing_res = requests.post(
            f"{api_url()}/api/auth/forgot-password",
            json={"email": email},
            timeout=10,
        )
        missing_res = requests.post(
            f"{api_url()}/api/auth/forgot-password",
            json={"email": missing_email},
            timeout=10,
        )

        assert existing_res.status_code == 200
        assert missing_res.status_code == 200

        existing_data = existing_res.json()
        missing_data = missing_res.json()
        assert (
            existing_data["message"]
            == "If an account with that email exists, a reset link has been generated."
        )
        assert existing_data["message"] == missing_data["message"]
        assert "reset_link" not in existing_data
        assert "reset_link" not in missing_data
    finally:
        cleanup_test_data(
            emails=[email],
            usernames=[username],
        )
