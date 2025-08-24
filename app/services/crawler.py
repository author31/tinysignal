import json
import random
import time
from datetime import datetime

import requests
from tqdm import tqdm

from ..config import settings
from ..repositories.cluster import ClusterRepository
from .hf import get_hf_embeddings

cluster_repo = ClusterRepository()


def fetch_top_stories() -> dict:
    assert "HN_URL" in settings.keys(), "Missing HN_URL."
    resp = requests.get(f"{settings['HN_URL']}/topstories.json")
    return json.loads(resp.text)

def fetch_by_post_id(post_id: int) -> dict:
    assert "HN_URL" in settings.keys(), "Missing HN_URL."
    try: 
        resp = requests.get(f"{settings['HN_URL']}/item/{post_id}.json")
        return json.loads(resp.text)
    except Exception as e:
        print("Fetching HN post failed: ", e)
        raise e

def fetch_and_insert():
    post_ids = fetch_top_stories()[:100]
    for post_id in tqdm(post_ids, desc="Fetching and processing"):
        fetch_result = fetch_by_post_id(post_id)
        if not fetch_result: continue

        try:
            insert_data = {
                "title": fetch_result["title"],
                "url": fetch_result["url"],
                "hn_post_id": fetch_result["id"],
                "embedding": get_hf_embeddings(fetch_result["title"]),
                "created_at": datetime.now()
            }
            cluster_repo.insert_into_embeddings_table(insert_data)

        except Exception as e:
            print("Inserting failed: ", e)
            continue
        
        time.sleep(random.random()*3)
