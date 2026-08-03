def get_bedrock_llm():
    from langchain_aws import ChatBedrock

    return ChatBedrock(
        model_id="us.anthropic.claude-sonnet-4-6",
        region_name="us-east-1",
        model_kwargs={
            "temperature": 0.2,
            "max_tokens": 1200,
        },
    )
