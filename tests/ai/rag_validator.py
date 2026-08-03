from tests.ai.bedrock_client import get_bedrock_llm

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