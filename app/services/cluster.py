from collections import defaultdict

from sklearn.cluster import KMeans
from tqdm import tqdm

from ..config import settings
from ..logger import setup_logger
from ..models.cluster import ClusterDisplayModel
from ..repositories.cluster import ClusterRepository
from .llm import call_llm

logger = setup_logger(__name__)

cluster_repo = ClusterRepository()

def execute_cluster():
    """Execute clustering and generate titles"""
    clusters = cluster_repo.get_clusters()
    cluster_titles = cluster_repo.get_cluster_titles()
    
    # Check if both clusters and titles exist
    if len(clusters) > 0 and len(cluster_titles) > 0:
        return

    assert "N_CLUSTERS" in settings.keys(), "Missing N_CLUSTERS."
    records = cluster_repo.get_records()
    embeddings = [record["embedding"] for record in records]
    cluster_result = KMeans(
        n_clusters=settings["N_CLUSTERS"], random_state=0
    ).fit(embeddings)

    cluster_labels = cluster_result.labels_
    cluster_to_ids = defaultdict(list)
    for i, record in enumerate(records):
        record["cluster_idx"] = int(cluster_labels[i])
        cluster_to_ids[cluster_labels[i]].append(record["title"])

    # Use transaction to ensure data consistency
    try:
        cluster_repo.insert_to_cluster_table(records)
        
        # Clear existing titles if any
        cluster_repo.clear_cluster_titles()

        # Generate titles for each cluster
        messages = [
            {
                "role": "system",
                "content": (
                    "You are given a list of titles that belong to the same semantic cluster. "
                    "Your task is to assign a single, concise title that captures the shared semantic meaning of the titles. "
                    "Strictly return the result as a valid JSON object. "
                    "Do not include explanations, extra text, or code blocks. "
                    "Return only this format:\n\n"
                    "{ \"title\": \"YOUR_ANSWER_HERE\" }"
                ),
            }
        ] 
        titles_to_insert = []
        logger.info(f"Generating titles for {len(cluster_to_ids)} clusters")
        for i, titles in tqdm(cluster_to_ids.items(), desc="Processing clusters", total=len(cluster_to_ids)):
            messages_copy = messages.copy()
            messages_copy.append({"role": "user", "content": f"List of titles: {','.join(titles)}"})
            result = call_llm(messages=messages_copy, model=settings["LLM_MODEL"])
            assert isinstance(result, dict), f"LLM repsonse must be a dictionary, Got: {type(result)=}"
            assert "title" in result, "LLM response must contains title field"
            titles_to_insert.append([int(i), result["title"]])
            logger.info(f"Generated title for cluster {i}: {result['title']}")

        # Batch insert all titles
        cluster_repo.insert_to_cluster_title_table(titles_to_insert)
        
    except Exception as e:
        # Rollback on failure - clear any partial data
        cluster_repo.clear_cluster_table()
        cluster_repo.clear_cluster_titles()
        raise e

def get_cluster_display_data() -> list[ClusterDisplayModel]:
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
