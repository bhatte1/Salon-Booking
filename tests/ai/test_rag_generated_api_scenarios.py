from __future__ import annotations

from types import SimpleNamespace

from tests.ai.rag_validator import (
    build_rag_prompt,
    generate_rag_test_cases,
    load_backend_route_context,
)


class FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.prompts: list[str] = []

    def invoke(self, prompt: str):
        self.prompts.append(prompt)
        return SimpleNamespace(content=self.content)


def test_rag_loader_reads_real_backend_route_context():
    context = load_backend_route_context()

    assert "customer_signup" in context
    assert 'detail="Service not found"' in context
    assert 'detail="Time slot already booked"' in context


def test_rag_prompt_includes_endpoint_objective_and_retrieved_context():
    context = "Retrieved route rules here"
    prompt = build_rag_prompt(
        endpoint="POST /api/appointments/me",
        objective="Generate negative booking tests",
        context=context,
    )

    assert "retrieval augmented generation" in prompt.lower()
    assert "POST /api/appointments/me" in prompt
    assert "Generate negative booking tests" in prompt
    assert context in prompt


def test_rag_generator_uses_retrieved_backend_context_to_shape_test_cases(monkeypatch):
    fake_llm = FakeLLM(
        """
        [
          {
            "title": "Reject unknown service",
            "request": {"body": {"service_id": 99999999}},
            "expected_response": {"status_code": 404, "detail": "Service not found"},
            "rationale": "The backend explicitly raises 404 when the service does not exist."
          }
        ]
        """
    )
    monkeypatch.setattr("tests.ai.rag_validator.get_bedrock_llm", lambda: fake_llm)

    generated_cases = generate_rag_test_cases(
        endpoint="POST /api/appointments/me",
        objective="Create one negative booking scenario from retrieved backend rules",
    )

    assert generated_cases[0]["title"] == "Reject unknown service"
    assert generated_cases[0]["expected_response"]["status_code"] == 404
    assert "POST /api/appointments/me" in fake_llm.prompts[0]
    assert "Service not found" in fake_llm.prompts[0]
