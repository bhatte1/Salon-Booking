from __future__ import annotations

import os
import uuid
from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from tests.api.api_client import APIClient

if TYPE_CHECKING:
    from playwright.sync_api import APIRequestContext, Playwright


def _normalize_db_url(raw: str | None) -> str:
    if not raw:
        return "postgresql://salon:salonpass@127.0.0.1:5433/salon_db"
    return raw.replace("postgresql+psycopg://", "postgresql://")


@dataclass
class CleanupRegistry:
    emails: set[str] = field(default_factory=set)
    usernames: set[str] = field(default_factory=set)
    service_names: set[str] = field(default_factory=set)

    def track_user(self, *, email: str, username: str) -> None:
        self.emails.add(email)
        self.usernames.add(username)

    def track_service(self, *, service_name: str) -> None:
        self.service_names.add(service_name)


TEST_OWNER_PASSWORD = "OwnerPass123!"
TEST_OWNER_PASSWORD_HASH = (
    "$2b$12$l8tab5MBcvijnTJhJCF1ce5FyJvNbtuVtJ6lGeL4DM6PFTptOaS4i"
)


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("TEST_API_BASE_URL") or os.getenv("E2E_API_URL") or "http://127.0.0.1:8000"


@pytest.fixture(scope="session")
def database_url() -> str:
    return _normalize_db_url(os.getenv("TEST_DATABASE_URL") or os.getenv("E2E_DATABASE_URL") or os.getenv("DATABASE_URL"))


@pytest.fixture(scope="session")
def playwright_instance() -> Generator["Playwright", None, None]:
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as playwright:
        yield playwright


@pytest.fixture()
def request_context(
    playwright_instance: "Playwright",
    base_url: str,
) -> Generator["APIRequestContext", None, None]:
    context = playwright_instance.request.new_context(
        base_url=base_url.rstrip("/"),
        extra_http_headers={"Accept": "application/json"},
    )
    yield context
    context.dispose()


@pytest.fixture()
def api_client(request_context: "APIRequestContext") -> APIClient:
    return APIClient(request_context)


@pytest.fixture()
def cleanup_registry(database_url: str) -> Generator[CleanupRegistry, None, None]:
    psycopg = pytest.importorskip("psycopg")
    registry = CleanupRegistry()
    yield registry

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for email in registry.emails:
                cur.execute("DELETE FROM appointments WHERE customer_email = %s", (email,))

            for username in registry.usernames:
                cur.execute("DELETE FROM users WHERE username = %s", (username,))

            for email in registry.emails:
                cur.execute("DELETE FROM users WHERE email = %s", (email,))

            for service_name in registry.service_names:
                cur.execute(
                    """
                    DELETE FROM services
                    WHERE name = %s
                    AND NOT EXISTS (
                        SELECT 1
                        FROM appointments
                        WHERE appointments.service_id = services.id
                    )
                    """,
                    (service_name,),
                )

        conn.commit()


@pytest.fixture()
def random_customer_payload() -> Callable[[], dict[str, str]]:
    def factory() -> dict[str, str]:
        suffix = uuid.uuid4().hex[:12]
        return {
            "full_name": f"API Customer {suffix}",
            "email": f"qa+{suffix}@example.com",
            "username": f"user_{suffix}",
            "password": "CustomerPass123!",
        }

    return factory


@pytest.fixture()
def random_service_payload() -> Callable[[], dict[str, int | str]]:
    def factory() -> dict[str, int | str]:
        suffix = uuid.uuid4().hex[:10]
        return {
            "name": f"API Service {suffix}",
            "price_cents": 4500,
            "duration_minutes": 45,
        }

    return factory


@pytest.fixture()
def future_booking_time() -> Callable[..., str]:
    def factory(*, days_from_now: int = 1, hour: int = 10, minute: int = 0) -> str:
        booking_time = datetime.now() + timedelta(days=days_from_now)
        booking_time = booking_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return booking_time.isoformat()

    return factory


@pytest.fixture(scope="session")
def session_cleanup_registry(database_url: str) -> Generator[CleanupRegistry, None, None]:
    psycopg = pytest.importorskip("psycopg")
    registry = CleanupRegistry()
    yield registry

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            for email in registry.emails:
                cur.execute("DELETE FROM appointments WHERE customer_email = %s", (email,))

            for username in registry.usernames:
                cur.execute("DELETE FROM users WHERE username = %s", (username,))

            for email in registry.emails:
                cur.execute("DELETE FROM users WHERE email = %s", (email,))

            for service_name in registry.service_names:
                cur.execute(
                    """
                    DELETE FROM services
                    WHERE name = %s
                    AND NOT EXISTS (
                        SELECT 1
                        FROM appointments
                        WHERE appointments.service_id = services.id
                    )
                    """,
                    (service_name,),
                )

        conn.commit()


@pytest.fixture(scope="session")
def shared_api_client(playwright_instance: "Playwright", base_url: str) -> Generator[APIClient, None, None]:
    context = playwright_instance.request.new_context(
        base_url=base_url.rstrip("/"),
        extra_http_headers={"Accept": "application/json"},
    )
    yield APIClient(context)
    context.dispose()


def _build_customer_credentials() -> dict[str, str]:
    suffix = uuid.uuid4().hex[:12]
    return {
        "full_name": f"API Customer {suffix}",
        "email": f"qa+{suffix}@example.com",
        "username": f"user_{suffix}",
        "password": "CustomerPass123!",
    }


@pytest.fixture(scope="session")
def authenticated_customer(
    shared_api_client: APIClient,
    session_cleanup_registry: CleanupRegistry,
) -> dict[str, str]:
    payload = _build_customer_credentials()
    session_cleanup_registry.track_user(email=payload["email"], username=payload["username"])

    signup_response = shared_api_client.signup_customer(payload)
    assert signup_response.status_code == 200

    login_response = shared_api_client.login_customer(payload["username"], payload["password"])
    assert login_response.status_code == 200

    login_body = login_response.json()
    return {
        **payload,
        "token": login_body["access_token"],
    }


@pytest.fixture(scope="session")
def authenticated_customer_two(
    shared_api_client: APIClient,
    session_cleanup_registry: CleanupRegistry,
) -> dict[str, str]:
    payload = _build_customer_credentials()
    session_cleanup_registry.track_user(email=payload["email"], username=payload["username"])

    signup_response = shared_api_client.signup_customer(payload)
    assert signup_response.status_code == 200

    login_response = shared_api_client.login_customer(payload["username"], payload["password"])
    assert login_response.status_code == 200

    login_body = login_response.json()
    return {
        **payload,
        "token": login_body["access_token"],
    }


@pytest.fixture()
def seed_owner_user(database_url: str, cleanup_registry: CleanupRegistry) -> Callable[..., dict[str, str]]:
    psycopg = pytest.importorskip("psycopg")

    def factory() -> dict[str, str]:
        suffix = uuid.uuid4().hex[:12]
        owner = {
            "full_name": f"API Owner {suffix}",
            "email": f"owner+{suffix}@example.com",
            "username": f"owner_{suffix}",
            "password": TEST_OWNER_PASSWORD,
        }
        cleanup_registry.track_user(email=owner["email"], username=owner["username"])

        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (full_name, email, username, hashed_password, role, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        owner["full_name"],
                        owner["email"],
                        owner["username"],
                        TEST_OWNER_PASSWORD_HASH,
                        "owner",
                        True,
                    ),
                )
            conn.commit()

        return owner

    return factory


@pytest.fixture(scope="session")
def authenticated_owner(
    database_url: str,
    shared_api_client: APIClient,
    session_cleanup_registry: CleanupRegistry,
) -> dict[str, str]:
    psycopg = pytest.importorskip("psycopg")
    suffix = uuid.uuid4().hex[:12]
    owner = {
        "full_name": f"API Owner {suffix}",
        "email": f"owner+{suffix}@example.com",
        "username": f"owner_{suffix}",
        "password": TEST_OWNER_PASSWORD,
    }
    session_cleanup_registry.track_user(email=owner["email"], username=owner["username"])

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (full_name, email, username, hashed_password, role, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    owner["full_name"],
                    owner["email"],
                    owner["username"],
                    TEST_OWNER_PASSWORD_HASH,
                    "owner",
                    True,
                ),
            )
        conn.commit()

    login_response = shared_api_client.login_owner(owner["username"], owner["password"])
    assert login_response.status_code == 200

    login_body = login_response.json()
    return {
        **owner,
        "token": login_body["access_token"],
    }
