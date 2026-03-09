from __future__ import annotations

import psycopg
from playwright.sync_api import expect

from e2e.utils import cleanup_by_email_and_service, db_url, frontend_url, future_datetime_local, unique_marker


def test_frontend_booking_persists_to_db(page):
    marker = unique_marker("ui")
    customer_name = f"UI Test {marker}"
    customer_email = f"qa+{marker}@example.com"
    notes = f"Created by Playwright {marker}"

    try:
        page.goto(frontend_url())

        expect(page.get_by_role("heading", name="Salon Booking")).to_be_visible()
        expect(page.get_by_role("heading", name="Book an appointment")).to_be_visible()

        page.get_by_label("Name").fill(customer_name)
        page.get_by_label("Email").fill(customer_email)

        service_select = page.get_by_label("Service")
        expect(service_select.locator("option")).to_have_count(4)
        service_select.select_option(index=1)

        page.get_by_label("Start time").fill(future_datetime_local(180))
        page.get_by_label("Notes (optional)").fill(notes)

        page.get_by_role("button", name="Book").click()

        first_item = page.locator(".listItem").first
        expect(first_item).to_contain_text(customer_name)
        expect(first_item).to_contain_text(customer_email)
        expect(first_item).to_contain_text(notes)

        with psycopg.connect(db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT customer_name, customer_email, notes
                    FROM appointments
                    WHERE customer_email = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (customer_email,),
                )
                row = cur.fetchone()

        assert row is not None
        assert row[0] == customer_name
        assert row[1] == customer_email
        assert row[2] == notes
    finally:
        cleanup_by_email_and_service(email=customer_email)
