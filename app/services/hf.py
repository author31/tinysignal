import requests
from ..config import settings, secrets

def get_hf_embeddings(text: str) -> list:
    assert "HF_URL" in settings.keys(), "Missing HF_URL"
    assert "HF_API_KEY" in secrets.keys(), "Missing HuggingFace API KEY"

    headers = {"Authorization": f"Bearer {secrets['HF_API_KEY']}"}
    text = text.replace("\n", "")
    resp = requests.post(settings["HF_URL"], headers=headers, json={"inputs": text})
    return resp.json()
