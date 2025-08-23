import json

from ..config import settings

import duckdb


class ClusterRepository:
    def __init__(
        self, 
        db_path: str = f"{settings['ARTIFACT_DIR']}/hn_data.duckdb"
    ) -> None:
        self.conn = duckdb.connect(db_path)
        
    def _tuple_to_dict(
        self, tuple_data: tuple, keys: list | None = None
    ) -> dict:
        if not keys: 
            keys = ["id", "title", "url", "embedding", "hn_post_id", "created_at"]
        return dict(zip(keys, tuple_data))
    
    def get_records(self) -> list[dict]:
        query = """
        SELECT * FROM hn_embeddings
        """
        cursor = self.conn.cursor()
        results = cursor.execute(query).fetchall()
        return [self._tuple_to_dict(result) for result in results]
    
    def create_cluster_table(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS hn_clusters (
            id BIGINT PRIMARY KEY,
            hn_embedding_id BIGINT REFERENCES hn_embeddings(id),
            cluster_idx INTEGER
        )
        """
        self.conn.execute(query)
    
    def create_cluster_title_table(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS hn_cluster_titles (
            hn_cluster_idx BIGINT PRIMARY KEY,
            title VARCHAR(255)
        )
        """
        self.conn.execute(query)

    def create_embeddings_table(self) -> None:
        query = \
        """
        CREATE TABLE IF NOT EXISTS hn_embeddings (
            id BIGINT PRIMARY KEY,
            title VARCHAR(255),
            url VARCHAR(255),
            embedding FLOAT[384],
            hn_post_id BIGINT,
            created_at TIMESTAMP
        )
        """
        self.conn.execute(query)

    def insert_to_cluster_table(self, data: list[dict]) -> None:
        query = """
        INSERT INTO hn_clusters (hn_embedding_id, cluster_idx)
        VALUES (?, ?)
        """
        cursor = self.conn.cursor()
        for record in data:
            cursor.execute(query, [record["id"], record["cluster_idx"]])
        self.conn.commit()

    def insert_to_cluster_title_table(self, data: list) -> None:
        query = """
        INSERT INTO hn_cluster_titles(hn_cluster_idx, title)
        VALUES (?, ?)
        ON CONFLICT (hn_cluster_idx)
        DO UPDATE SET title = EXCLUDED.title
        """
        cursor = self.conn.cursor()
        cursor.execute(query, [data[0], data[1]])
        self.conn.commit()

    def insert_into_embeddings_table(self, data: dict) -> None:
        check_query = """
        SELECT * FROM hn_embeddings WHERE hn_post_id = ?
        """
        cursor = self.conn.cursor()
        existed_record = cursor.execute(check_query, [data["hn_post_id"]]).fetchall()
        if len(existed_record) > 0:
            return

        query = """
        INSERT INTO hn_embeddings(title, url, embedding, hn_post_id, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, [
            data["title"], 
            data["url"], 
            data["embedding"], 
            data["hn_post_id"], 
            data["created_at"]
        ])
        self.conn.commit()

    def get_clusters(self) -> list[dict]:
        query = """
        SELECT * FROM hn_clusters
        """
        cursor = self.conn.cursor()
        results = cursor.execute(query).fetchall()
        return [self._tuple_to_dict(result) for result in results]

    def get_clustered_data(self) -> list[dict]:
        query = """
        SELECT * FROM hn_embeddings
        INNER JOIN hn_clusters ON hn_embeddings.id = hn_clusters.hn_embedding_id
        """
        cursor = self.conn.cursor()
        results = cursor.execute(query).fetchall()
        return [self._tuple_to_dict(result) for result in results]

    def get_unqiue_cluster_idx(self) -> list[int]:
        query = """
        SELECT DISTINCT cluster_idx FROM hn_clusters
        """
        cursor = self.conn.cursor()
        results = cursor.execute(query).fetchall()
        return [result[0] for result in results]

    def get_records_by_cluster_idx(self, cluster_idx: int, limit: int = 5) -> list[dict]:
        query = """
        SELECT * FROM hn_embeddings
        INNER JOIN hn_clusters ON hn_embeddings.id = hn_clusters.hn_embedding_id
        WHERE hn_clusters.cluster_idx = ?
        LIMIT ?
        """
        cursor = self.conn.cursor()
        results = cursor.execute(query, [cluster_idx, limit]).fetchall()
        return [self._tuple_to_dict(result) for result in results]

    def get_posts_by_cluster_idx(self, cluster_idx: int, limit: int = 5) -> list[dict]:
        query = """
        SELECT title, url, hn_post_id FROM hn_embeddings
        INNER JOIN hn_clusters ON hn_embeddings.id = hn_clusters.hn_embedding_id
        WHERE hn_clusters.cluster_idx = ?
        LIMIT ?
        """
        cursor = self.conn.cursor()
        results = cursor.execute(query, [cluster_idx, limit]).fetchall()
        return [{"title": row[0], "url": row[1], "hn_post_id": row[2]} for row in results]

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()
