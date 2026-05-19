from __future__ import annotations

import psycopg
import requests
import pytest
from playwright.sync_api import expect

from e2e.utils import (
    TEST_OWNER_PASSWORD,
    api_url,
    business_date_local,
    business_time_iso,
    cleanup_test_data,
    create_owner_user,
    create_service,
    db_url,
    frontend_url,
    signup_customer,
    unique_marker,
)

pytestmark = pytest.mark.requires_db


def test_frontend_customer_signup_login_and_booking_persists_to_db(page):
    marker = unique_marker("ui-customer")
    service_name = f"UI Customer Service {marker}"
    full_name = f"UI Customer {marker}"
    email = f"qa+{marker}@example.com"
    username = f"user_{marker.replace('-', '_')}"
    password = "CustomerPass123!"
    notes = f"Created by Playwright {marker}"

    try:
        create_service(name=service_name, duration_minutes=45)

        page.goto(frontend_url())

        expect(page.get_by_role("heading", name="Salon Booking")).to_be_visible()
        page.get_by_role("button", name="Customer Sign Up").click()

        expect(page.get_by_role("heading", name="Customer Sign Up Page")).to_be_visible()
        page.get_by_placeholder("Full Name").fill(full_name)
        page.get_by_placeholder("Email").fill(email)
        page.get_by_placeholder("Username").fill(username)
        page.get_by_placeholder("Password").fill(password)
        page.get_by_role("button", name="Create Account").click()

        expect(page.get_by_text(f"Signup successful for {username}")).to_be_visible()

        page.goto(f"{frontend_url()}/login/customer")
        page.get_by_placeholder("Username or Email").fill(username)
        page.get_by_placeholder("Password").fill(password)
        page.get_by_role("button", name="Login").click()

        expect(page).to_have_url(f"{frontend_url()}/dashboard/customer")
        expect(page.get_by_role("heading", name="Customer Dashboard")).to_be_visible()
        expect(page.get_by_text(f"Welcome, {full_name}")).to_be_visible()

        page.get_by_role("button", name=f"Select {service_name}").click()
        page.get_by_label("Appointment date").fill(business_date_local(1))
        page.locator(".timeSlotBtn:not([disabled])").first.click()
        page.get_by_placeholder("Notes").fill(notes)
        page.get_by_role("button", name="Book").click()

        expect(page.get_by_text("Appointment booked successfully!")).to_be_visible()
        appointment_list = page.locator("ul").nth(0)
        expect(appointment_list).to_contain_text(notes)
        expect(appointment_list).to_contain_text("Status: pending")

        with psycopg.connect(db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT customer_name, customer_email, notes, status
                    FROM appointments
                    WHERE customer_email = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (email,),
                )
                row = cur.fetchone()

        assert row is not None
        assert row[0] == full_name
        assert row[1] == email
        assert row[2] == notes
        assert row[3] == "pending"
    finally:
        cleanup_test_data(
            emails=[email],
            usernames=[username],
            service_names=[service_name],
        )


def test_frontend_owner_can_update_appointment_status(page):
    marker = unique_marker("ui-owner")
    service_name = f"UI Owner Service {marker}"
    customer_email = f"qa+{marker}@example.com"
    owner_email = f"owner+{marker}@example.com"
    owner_username = f"owner_{marker.replace('-', '_')}"
    customer_name = f"Owner Queue {marker}"
    appointment_note = f"owner-visible-{marker}"

    try:
        service = create_service(name=service_name, duration_minutes=30)
        create_owner_user(
            full_name=f"Owner {marker}",
            email=owner_email,
            username=owner_username,
        )

        create_res = requests.post(
            f"{api_url()}/api/appointments",
            json={
                "customer_name": customer_name,
                "customer_email": customer_email,
                "service_id": service["id"],
                "start_time": business_time_iso(days_from_now=1, hour=9, minute=0),
                "notes": appointment_note,
            },
            timeout=10,
        )
        assert create_res.status_code == 200
        appointment_id = create_res.json()["id"]

        page.goto(f"{frontend_url()}/login/owner")
        expect(page.get_by_role("heading", name="Owner Login")).to_be_visible()
        page.get_by_placeholder("Username or Email").fill(owner_username)
        page.get_by_placeholder("Password").fill(TEST_OWNER_PASSWORD)
        page.get_by_role("button", name="Login").click()

        expect(page).to_have_url(f"{frontend_url()}/dashboard/owner")
        expect(page.get_by_role("heading", name="Owner Dashboard")).to_be_visible()

        appointment_item = page.locator("li", has_text=appointment_note).first
        expect(appointment_item).to_contain_text(customer_name)
        expect(appointment_item).to_contain_text("Status: pending")

        appointment_item.get_by_role("button", name="Confirm").click()

        expect(page.get_by_text(f"Appointment #{appointment_id} updated to confirmed")).to_be_visible()
        expect(appointment_item).to_contain_text("Status: confirmed")

        with psycopg.connect(db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT status FROM appointments WHERE id = %s",
                    (appointment_id,),
                )
                row = cur.fetchone()

        assert row is not None
        assert row[0] == "confirmed"
    finally:
        cleanup_test_data(
            emails=[customer_email, owner_email],
            usernames=[owner_username],
            service_names=[service_name],
        )


def test_frontend_forgot_username_displays_username_for_existing_email(page):
    marker = unique_marker("ui-forgot-username")
    email = f"qa+{marker}@example.com"
    username = f"user_{marker.replace('-', '_')}"
    password = "CustomerPass123!"

    try:
        signup_customer(
            full_name=f"Forgot Username UI {marker}",
            email=email,
            username=username,
            password=password,
        )

        page.goto(f"{frontend_url()}/forgot-username")
        expect(page.get_by_role("heading", name="Forgot Username")).to_be_visible()

        page.get_by_placeholder("Enter your email").fill(email)
        page.get_by_role("button", name="Find Username").click()

        expect(
            page.get_by_text(
                "If an account with that email exists, username details have been generated."
            )
        ).to_be_visible()
        expect(page.get_by_text("Username (dev):")).to_have_count(0)
    finally:
        cleanup_test_data(
            emails=[email],
            usernames=[username],
        )


def test_frontend_home_icon_keeps_customer_logged_in(page):
    marker = unique_marker("ui-home")
    email = f"qa+{marker}@example.com"
    username = f"user_{marker.replace('-', '_')}"
    password = "CustomerPass123!"

    try:
        signup_customer(
            full_name=f"Home Session User {marker}",
            email=email,
            username=username,
            password=password,
        )

        page.goto(f"{frontend_url()}/login/customer")
        page.get_by_placeholder("Username or Email").fill(username)
        page.get_by_placeholder("Password").fill(password)
        page.get_by_role("button", name="Login").click()

        expect(page).to_have_url(f"{frontend_url()}/dashboard/customer")
        expect(page.get_by_role("heading", name="Customer Dashboard")).to_be_visible()

        page.get_by_role("link", name="Go to home page").click()
        expect(page).to_have_url(f"{frontend_url()}/")
        expect(page.get_by_role("button", name="Go to Customer Dashboard")).to_be_visible()

        page.get_by_role("button", name="Go to Customer Dashboard").click()
        expect(page).to_have_url(f"{frontend_url()}/dashboard/customer")
        expect(page.get_by_role("heading", name="Customer Dashboard")).to_be_visible()
    finally:
        cleanup_test_data(
            emails=[email],
            usernames=[username],
        )
