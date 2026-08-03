from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.request import urlopen

import pytest

from e2e.utils import (
    api_url,
    current_environment_summary,
    database_access_enabled,
    frontend_url,
    is_aws_env,
    is_local_env,
)

if TYPE_CHECKING:
    from playwright.sync_api import Browser

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
BACKEND_DIR = ROOT / "backend"
LOGGER = logging.getLogger(__name__)


def _wait_for_http(url: str, timeout_seconds: int = 120) -> None:
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2) as resp:  # nosec B310
                if 200 <= resp.status < 500:
                    return
        except Exception as exc:  # pragma: no cover
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"Timed out waiting for {url}: {last_error}")


def _require_remote_urls() -> None:
    if not frontend_url():
        raise RuntimeError(
            "TEST_ENV=aws requires E2E_FRONTEND_URL to be set."
        )
    if not api_url():
        raise RuntimeError(
            "TEST_ENV=aws requires E2E_API_URL to be set."
        )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_db: test needs direct PostgreSQL access for setup, cleanup, or validation",
    )
    config.addinivalue_line(
        "markers",
        "smoke: lightweight smoke coverage intended for fast environment validation",
    )
    config.addinivalue_line(
        "markers",
        "aws: test is intended for deployed AWS execution mode",
    )
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
    )


def pytest_report_header(config):
    summary = current_environment_summary()
    return [
        f"TEST_ENV={summary['test_env']}",
        f"E2E_FRONTEND_URL={summary['frontend_url'] or '<unset>'}",
        f"E2E_API_URL={summary['api_url'] or '<unset>'}",
        f"DB access enabled={summary['database_access_enabled']}",
    ]


def pytest_collection_modifyitems(config, items):
    if not is_aws_env() or database_access_enabled():
        return

    skip_requires_db = pytest.mark.skip(
        reason=(
            "Skipping DB-coupled E2E test in aws mode because E2E_DATABASE_URL/DATABASE_URL "
            "is not configured."
        )
    )
    for item in items:
        if "requires_db" in item.keywords:
            item.add_marker(skip_requires_db)


@pytest.fixture(scope="session", autouse=True)
def services_up():
    summary = current_environment_summary()
    LOGGER.info("Running E2E framework in %s mode", summary["test_env"])
    LOGGER.info("Frontend target: %s", summary["frontend_url"] or "<unset>")
    LOGGER.info("API target: %s", summary["api_url"] or "<unset>")
    LOGGER.info("Direct DB access enabled: %s", summary["database_access_enabled"])

    if is_aws_env():
        _require_remote_urls()
        LOGGER.info("AWS mode detected: skipping local migrations and service startup.")
        _wait_for_http(frontend_url(), timeout_seconds=120)
        _wait_for_http(f"{api_url()}/health", timeout_seconds=120)
        yield
        return

    if not is_local_env():
        raise RuntimeError(
            "Unsupported TEST_ENV value. Use TEST_ENV=local or TEST_ENV=aws."
        )

    frontend_cmd = ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"]
    migrate_cmd = [str(BACKEND_DIR / ".venv/bin/alembic"), "upgrade", "head"]
    backend_cmd = [
        str(BACKEND_DIR / ".venv/bin/uvicorn"),
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]

    LOGGER.info("LOCAL mode detected: running Alembic migrations and starting local services.")
    subprocess.run(migrate_cmd, cwd=BACKEND_DIR, check=True)

    frontend_proc = subprocess.Popen(frontend_cmd, cwd=FRONTEND_DIR)
    backend_proc = subprocess.Popen(backend_cmd, cwd=BACKEND_DIR)

    try:
        _wait_for_http(frontend_url(), timeout_seconds=120)
        _wait_for_http(f"{api_url()}/health", timeout_seconds=120)
        yield
    finally:
        frontend_proc.terminate()
        backend_proc.terminate()
        frontend_proc.wait(timeout=20)
        backend_proc.wait(timeout=20)


@pytest.fixture(scope="session")
def browser():
    playwright_api = pytest.importorskip("playwright.sync_api")
    with playwright_api.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture()
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
