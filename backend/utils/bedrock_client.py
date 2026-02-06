import json
import boto3
from settings import BEDROCK_MODEL_ID

bedrock = boto3.client("bedrock-runtime")

def invoke_claude(payload: dict):
    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body={
            "anthropic_version": "bedrock-2023-05-31",
            "system": (
                "You are a ranking engine. "
                "Return a numeric priority score between 0 and 100."
            ),
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 5000,
            "temperature": 0.2
        }
    )

    body = json.loads(response["body"].read())
    return json.loads(body["content"][0]["text"])
