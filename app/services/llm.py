import json
import requests
from ..config import secrets

def call_llm(messages: list, model: str):
    assert "OPENROUTER_API_KEY" in secrets.keys(), "Missing OPENROUTER_API_KEY"

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {secrets['OPENROUTER_API_KEY']}",
        },
        data=json.dumps({
            "model": model,
            "messages": messages
        })
        )
    return response.json()
