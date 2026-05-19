from __future__ import annotations

import logging

import pytest
import requests
from playwright.sync_api import expect

from e2e.utils import (
    api_url,
    frontend_url,
    is_aws_env,
    unique_marker,
)

LOGGER = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.aws,
    pytest.mark.smoke,
    pytest.mark.skipif(not is_aws_env(), reason="AWS smoke suite runs only with TEST_ENV=aws"),
]


def test_aws_frontend_landing_page_is_reachable(page):
    LOGGER.info("Opening deployed frontend landing page: %s", frontend_url())
    page.goto(frontend_url(), wait_until="domcontentloaded")

    expect(page).to_have_title("frontend")
    expect(page.get_by_role("heading", name="Salon Booking")).to_be_visible()
    expect(page.get_by_role("button", name="Customer Sign Up")).to_be_visible()
    expect(page.get_by_role("button", name="Customer Login")).to_be_visible()


def test_aws_backend_health_endpoint_is_reachable():
    health_url = f"{api_url()}/health"
    LOGGER.info("Checking backend health endpoint: %s", health_url)

    response = requests.get(health_url, timeout=15)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_aws_public_service_listing_endpoint_is_reachable():
    services_url = f"{api_url()}/api/services"
    LOGGER.info("Checking public services endpoint: %s", services_url)

    response = requests.get(services_url, timeout=15)

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    if payload:
        first_service = payload[0]
        assert "id" in first_service
        assert "name" in first_service
        assert "price_cents" in first_service
        assert "duration_minutes" in first_service


def test_aws_public_forgot_password_endpoint_is_reachable():
    marker = unique_marker("aws-forgot-password")
    forgot_password_url = f"{api_url()}/api/auth/forgot-password"
    payload = {"email": f"qa+{marker}@example.com"}
    LOGGER.info("Checking forgot-password endpoint with isolated email: %s", payload["email"])

    response = requests.post(forgot_password_url, json=payload, timeout=15)

    assert response.status_code == 200
    body = response.json()
    assert (
        body["message"]
        == "If an account with that email exists, a reset link has been generated."
    )


def test_aws_customer_signup_smoke_flow_creates_isolated_user():
    marker = unique_marker("aws-signup")
    signup_url = f"{api_url()}/api/auth/signup/customer"
    payload = {
        "full_name": f"AWS Smoke User {marker}",
        "email": f"qa+{marker}@example.com",
        "username": f"user_{marker.replace('-', '_')}",
        "password": "CustomerPass123!",
    }
    LOGGER.info("Creating isolated smoke-test customer: %s", payload["username"])

    response = requests.post(signup_url, json=payload, timeout=15)

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == payload["username"]
    assert body["email"] == payload["email"]
    assert body["full_name"] == payload["full_name"]
    assert body["role"] == "customer"
    assert body["is_active"] is True
