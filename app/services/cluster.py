import json
from collections import defaultdict
from typing import List

from sklearn.cluster import KMeans

from ..config import settings
from ..repositories.cluster import ClusterRepository
from ..models.cluster import ClusterDisplayModel
from .llm import call_llm

cluster_repo = ClusterRepository()

def execute_cluster():
    """Execute clustering and generate titles"""
    clusters = cluster_repo.get_clusters()
    if len(clusters) > 0: 
        return

    assert "N_CLUSTERS" in settings.keys(), "Missing N_CLUSTERS."
    records = cluster_repo.get_records()
    embeddings = [json.loads(record["embedding"]) for record in records]
    cluster_result = KMeans(
        n_clusters=settings["N_CLUSTERS"], random_state=0
    ).fit(embeddings)

    cluster_labels = cluster_result.labels_
    cluster_to_ids = defaultdict(list)
    for i, record in enumerate(records):
        record["cluster_idx"] = int(cluster_labels[i])
        cluster_to_ids[cluster_labels[i]].append(record["title"])

    cluster_repo.insert_to_cluster_table(records)

    # Generate titles for each cluster
    messages = [
        {"role": "system", "content": "You are given a list of titles that belong to the same semantic cluster. Your task is to assign a single, concise title that captures the shared semantic meaning of the titles. Return the title in JSON format: {'title': 'YOUR_ANSWER_HERE'}."},
    ]
    for i, titles in cluster_to_ids.items():
        messages_copy = messages.copy()
        messages_copy.append({"role": "user", "content": f"list of titles: {','.join(titles)}"})
        result = call_llm(messages=messages_copy, model=settings["LLM_MODEL"])
        assert "title" in result, "LLM's response is missing 'title' field"

        cluster_repo.insert_to_cluster_title_table([i, result['title']])

def get_cluster_display_data() -> List[ClusterDisplayModel]:
    """Get complete cluster data with titles and posts"""
    clusters = cluster_repo.get_clusters()
    if len(clusters) == 0:
        execute_cluster()
    
    cluster_data = []
    cluster_idxs = cluster_repo.get_unqiue_cluster_idx()
    
    for cluster_idx in cluster_idxs:
        # Get cluster title
        title_query = "SELECT title FROM hn_cluster_titles WHERE hn_cluster_idx = ?"
        cursor = cluster_repo.conn.cursor()
        title_result = cursor.execute(title_query, [cluster_idx]).fetchone()
        title = title_result[0] if title_result else f"Cluster {cluster_idx}"
        
        # Get posts for this cluster
        posts = cluster_repo.get_posts_by_cluster_idx(cluster_idx, limit=5)
        
        cluster_data.append(ClusterDisplayModel(
            cluster_idx=cluster_idx,
            title=title,
            posts=posts
        ))
    
    return cluster_data
