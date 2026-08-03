import time
import pytest

from tests.ai.test_case_generator import generate_signup_test_cases


BASE_URL = "http://localhost:8000"


def make_unique_payload(payload):
    unique = int(time.time() * 1000)

    new_payload = payload.copy()

    if "email" in new_payload:
        new_payload["email"] = f"ai_user_{unique}@example.com"

    if "username" in new_payload:
        new_payload["username"] = f"ai_user_{unique}"

    return new_payload


def test_ai_generated_signup_scenarios():
    requests = pytest.importorskip("requests")
    pytest.importorskip("langchain_aws")
    test_cases = generate_signup_test_cases()

    for case in test_cases:
        original_payload = case["request"]["body"]
        expected_status = case["expected_response"]["status_code"]
        title = case["title"].lower()

        if "invalid email" in title:
            payload = original_payload.copy()
        else:
            payload = make_unique_payload(original_payload)

        if "duplicate" in title:

            setup_response = requests.post(
                f"{BASE_URL}/api/auth/signup/customer",
                json=payload,
            )
            print(f"\nPrecondition setup for duplicate test: {setup_response.status_code}")

            response = requests.post(
                f"{BASE_URL}/api/auth/signup/customer",
                json=payload,
            )
        else:
            response = requests.post(
                f"{BASE_URL}/api/auth/signup/customer",
                json=payload,
            )

        print(f"\nRunning AI-generated test: {case['title']}")
        print(f"Payload: {payload}")
        print(f"Expected: {expected_status}, Actual: {response.status_code}")
        print(f"Response: {response.text}")

        assert response.status_code == expected_status
