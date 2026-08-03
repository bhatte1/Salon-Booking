import json
import re
from textwrap import dedent

from tests.ai.bedrock_client import get_bedrock_llm


def extract_json_array(text: str):
    match = re.search(r"\[.*\]", text, re.DOTALL)

    if not match:
        raise ValueError(f"No JSON array found in LLM response: {text}")

    return json.loads(match.group(0))


def build_signup_prompt() -> str:
    return dedent(
        """
        You are an SDET AI assistant.

        Application:
        Salon booking app with customer signup API.

        Endpoint:
        POST /api/auth/signup/customer

        Request fields:
        full_name, email, username, password

        Generate 5 API test cases:
        - positive case
        - duplicate username
        - invalid email
        - weak password
        - missing required field

        Return only valid JSON list.
        Important application behavior:
        - Successful signup returns status code 200.
        - Duplicate username or email returns 409.
        - FastAPI request validation errors return 422.
        """
    ).strip()


def build_booking_prompt() -> str:
    return dedent(
        """
        You are an SDET AI assistant.

        Application:
        Salon booking app with authenticated appointment booking.

        Endpoint:
        POST /api/appointments/me

        Request fields:
        service_id, start_time, notes

        Generate 5 API test cases:
        - valid booking
        - unknown service
        - booking in the past
        - overlapping slot
        - missing auth token

        Return only valid JSON list.
        Important application behavior:
        - Successful booking returns status code 200 and status pending.
        - Unknown service returns 404.
        - Past booking returns 400.
        - Overlapping slot returns 409.
        - Missing auth returns 401.
        """
    ).strip()


def build_owner_status_prompt() -> str:
    return dedent(
        """
        You are an SDET AI assistant.

        Application:
        Salon booking app with owner appointment status updates.

        Endpoint:
        PATCH /api/appointments/owner/{appointment_id}/status

        Request fields:
        status

        Generate 4 API test cases:
        - owner marks appointment completed
        - customer attempts owner status update
        - invalid status value
        - missing appointment id

        Return only valid JSON list.
        Important application behavior:
        - Valid owner update returns status code 200.
        - Customer access returns 403.
        - Invalid status returns 400.
        - Missing appointment id returns 404.
        """
    ).strip()


def generate_signup_test_cases():
    llm = get_bedrock_llm()
    response = llm.invoke(build_signup_prompt())

    return extract_json_array(response.content)


def generate_booking_test_cases():
    llm = get_bedrock_llm()
    response = llm.invoke(build_booking_prompt())
    return extract_json_array(response.content)


def generate_owner_status_test_cases():
    llm = get_bedrock_llm()
    response = llm.invoke(build_owner_status_prompt())
    return extract_json_array(response.content)
