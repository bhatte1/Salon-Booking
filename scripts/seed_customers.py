from __future__ import annotations

import csv
import os
import random
import time
from pathlib import Path

import requests
from faker import Faker


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
SIGNUP_URL = f"{BASE_URL}/api/auth/signup/customer"
TOTAL_CUSTOMERS = 1000
OUTPUT_PATH = Path("test_data/generated_customers.csv")
REQUEST_TIMEOUT_SECONDS = 10
MIN_DELAY_SECONDS = 0.05
MAX_DELAY_SECONDS = 0.20


def build_customer(fake: Faker, sequence: int) -> dict[str, str]:
    suffix = f"{sequence:04d}-{fake.unique.uuid4()[:8]}"
    first_name = fake.first_name()
    last_name = fake.last_name()
    username = f"{first_name}.{last_name}.{suffix}".lower().replace(" ", "")
    email = f"{username}@example.com"

    return {
        "full_name": f"{first_name} {last_name}",
        "username": username,
        "email": email,
        "password": f"SeedPass!{random.randint(100000, 999999)}",
    }


def signup_customer(payload: dict[str, str]) -> tuple[str, str]:
    try:
        response = requests.post(SIGNUP_URL, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        return "failed", str(exc)

    if response.status_code == 200:
        return "created", ""

    detail = ""
    try:
        body = response.json()
        detail = body.get("detail", "")
    except ValueError:
        detail = response.text.strip()

    if response.status_code == 409:
        return "skipped", detail or "Duplicate user"

    return "failed", detail or f"HTTP {response.status_code}"


def main() -> None:
    fake = Faker()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    created_count = 0
    skipped_count = 0
    failed_count = 0

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "full_name",
                "username",
                "email",
                "password",
                "status",
                "message",
            ],
        )
        writer.writeheader()

        for sequence in range(1, TOTAL_CUSTOMERS + 1):
            payload = build_customer(fake, sequence)
            status, message = signup_customer(payload)

            writer.writerow(
                {
                    **payload,
                    "status": status,
                    "message": message,
                }
            )

            if status == "created":
                created_count += 1
            elif status == "skipped":
                skipped_count += 1
            else:
                failed_count += 1

            print(
                f"[{sequence}/{TOTAL_CUSTOMERS}] "
                f"{payload['username']} -> {status}"
                f"{f' ({message})' if message else ''}"
            )

            time.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))

    print("\nSeeding complete")
    print(f"Created: {created_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Failed: {failed_count}")
    print(f"CSV: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
