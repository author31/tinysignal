from dotenv import dotenv_values

settings = {
    "ARTIFACT_DIR": ".artifact",
    "SOURCE": "https://hacker-news.firebaseio.com/v0/",
    "HF_URL": "https://api-inference.huggingface.co/models/BAAI/bge-small-en-v1.5",
    "N_CLUSTERS": 5,
    "LLM_MODEL": "openrouter/z-ai/glm-4.5-air:free"
}

secrets = {
    **dotenv_values(".env")
}
