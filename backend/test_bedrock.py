from langchain_aws import ChatBedrock

llm = ChatBedrock(
    model_id="us.anthropic.claude-sonnet-4-6",
    region_name="us-east-1",
    model_kwargs={
        "temperature": 0.2,
        "max_tokens": 200,
    },
)

response = llm.invoke("Say hello like an AI SDET assistant.")

print(response.content)