from __future__ import annotations

import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

import pytest
from playwright.sync_api import sync_playwright

from e2e.utils import api_url, frontend_url

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
BACKEND_DIR = ROOT / "backend"


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


@pytest.fixture(scope="session", autouse=True)
def services_up():
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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture()
def page(browser):
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()
