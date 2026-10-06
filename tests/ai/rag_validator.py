from tests.ai.bedrock_client import get_bedrock_llm
from pathlib import Path

from tests.ai.test_case_generator import extract_json_array


def load_backend_route_context():
    routes = Path(__file__).resolve().parents[2] / "backend/app/api"
    return "\n\n".join(
        f"# {path.name}\n{path.read_text()}"
        for path in sorted(routes.glob("*_routes.py"))
    )


def build_rag_prompt(*, endpoint, objective, context):
    return (
        "Use retrieval augmented generation to generate API test cases.\n"
        f"Endpoint: {endpoint}\nObjective: {objective}\n"
        f"Retrieved backend context:\n{context}\n"
        "Return only a JSON list of cases with title, request, expected_response, "
        "and rationale. Base expected behavior on the retrieved code."
    )


def generate_rag_test_cases(*, endpoint, objective):
    prompt = build_rag_prompt(
        endpoint=endpoint, objective=objective, context=load_backend_route_context()
    )
    response = get_bedrock_llm().invoke(prompt)
    return extract_json_array(response.content)

def validate_response_against_rules(api_response, business_rule_text):
    llm = get_bedrock_llm()

    prompt = f"""
    You are validating test output against business rules.

    Business rules:
    {business_rule_text}

    Actual API response:
    {api_response}

    Decide if the response follows the expected behavior.

    Return JSON only:
    {{
      "valid": true/false,
      "reason": "short explanation"
    }}
    """

    response = llm.invoke(prompt)
    return response.content
