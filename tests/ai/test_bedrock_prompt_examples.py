from __future__ import annotations

from types import SimpleNamespace

from tests.ai.pandas_validator import validate_generated_test_case_schema
from tests.ai.test_case_generator import (
    build_booking_prompt,
    build_owner_status_prompt,
    build_signup_prompt,
    generate_booking_test_cases,
    generate_owner_status_test_cases,
    generate_signup_test_cases,
)


class FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.prompts: list[str] = []

    def invoke(self, prompt: str):
        self.prompts.append(prompt)
        return SimpleNamespace(content=self.content)


def test_signup_prompt_contains_endpoint_and_expected_status_hints():
    prompt = build_signup_prompt()

    assert "POST /api/auth/signup/customer" in prompt
    assert "Duplicate username or email returns 409." in prompt
    assert "FastAPI request validation errors return 422." in prompt


def test_booking_prompt_contains_authenticated_booking_rules():
    prompt = build_booking_prompt()

    assert "POST /api/appointments/me" in prompt
    assert "Unknown service returns 404." in prompt
    assert "Overlapping slot returns 409." in prompt


def test_owner_status_prompt_contains_owner_authorization_rules():
    prompt = build_owner_status_prompt()

    assert "PATCH /api/appointments/owner/{appointment_id}/status" in prompt
    assert "Customer access returns 403." in prompt
    assert "Invalid status returns 400." in prompt


def test_bedrock_signup_generation_can_be_validated_with_dataframe(monkeypatch):
    fake_llm = FakeLLM(
        """
        [
          {
            "title": "Positive signup",
            "request": {"body": {"full_name": "A", "email": "a@example.com", "username": "a", "password": "Pass123!"}},
            "expected_response": {"status_code": 200}
          }
        ]
        """
    )
    monkeypatch.setattr("tests.ai.test_case_generator.get_bedrock_llm", lambda: fake_llm)

    generated_cases = generate_signup_test_cases()
    dataframe = validate_generated_test_case_schema(generated_cases)

    assert len(generated_cases) == 1
    assert fake_llm.prompts
    assert "POST /api/auth/signup/customer" in fake_llm.prompts[0]
    assert dataframe.iloc[0]["title"] == "Positive signup"


def test_bedrock_booking_and_owner_status_generators_return_structured_cases(monkeypatch):
    fake_llm = FakeLLM(
        """
        [
          {
            "title": "Generated case",
            "request": {"body": {"status": "completed"}},
            "expected_response": {"status_code": 200}
          }
        ]
        """
    )
    monkeypatch.setattr("tests.ai.test_case_generator.get_bedrock_llm", lambda: fake_llm)

    booking_cases = generate_booking_test_cases()
    owner_cases = generate_owner_status_test_cases()

    assert booking_cases[0]["expected_response"]["status_code"] == 200
    assert owner_cases[0]["expected_response"]["status_code"] == 200
    assert any("POST /api/appointments/me" in prompt for prompt in fake_llm.prompts)
    assert any("PATCH /api/appointments/owner/{appointment_id}/status" in prompt for prompt in fake_llm.prompts)
