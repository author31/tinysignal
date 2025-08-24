import os
from dotenv import dotenv_values

settings = {
    "ARTIFACT_DIR": ".artifact",
    "SOURCE": "https://hacker-news.firebaseio.com/v0/",
    "HF_URL": "https://api-inference.huggingface.co/models/BAAI/bge-small-en-v1.5",
    "N_CLUSTERS": 5,
    "LLM_MODEL": "google/gemini-2.5-flash",
    "HN_URL": "https://hacker-news.firebaseio.com/v0/"
}

secrets = {
    **dotenv_values(".env")
}

os.makedirs(settings["ARTIFACT_DIR"], exist_ok=True)

