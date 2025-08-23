from pydantic import BaseModel

class ClusterModel(BaseModel):
    hn_cluster_idx: int
    question: str

class ClusterDisplayModel(BaseModel):
    cluster_idx: int
    title: str
    posts: list[dict]
