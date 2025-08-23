import os
from typing import Dict, Any
from config.settings import HN_URL

from app.models import ClusterModel
from app.models.cluster import ClusterDisplayModel
from app.redis_client import redis_client
from app import sql_engine, together_client
from app.engine.builder import TrieBuilder
from app.middleware.redis_cache import db_cache_wrapper

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

template = Jinja2Templates(directory="views")
    
engine = sql_engine.SQLEngine(
    host= os.getenv("POSTGRESQL_URL"),
    database= "postgres",
    user= "postgres",
    password= os.getenv("POSTGRESQL_PWD"),
    minconn= 1,
    maxconn= 5
)

@router.get("/", response_class=HTMLResponse)
def get_homepage(request: Request):
    query = \
    """
    SELECT * FROM hn_cluster_titles
    ORDER BY hn_cluster_idx ASC
    """
    
    results = db_cache_wrapper(engine=engine, query=query)
    cluster_data = {r[0]:r[1] for r in results}
    return template.TemplateResponse("homepage.html", {"request": request, "cluster_data": cluster_data})

@router.get("/answer", response_class=HTMLResponse)
def get_answer(request: Request, answer: str):
    return template.TemplateResponse("answer.html", {"request": request, "answer": answer})

@router.get("/suggestion/", response_class=HTMLResponse)
def get_suggestion(request: Request, prefix: str):
    trie_builder = TrieBuilder()
    suggestions = trie_builder.trie_tree.search(queries=prefix)
    return template.TemplateResponse(
        "suggestions.html", {
            "request": request,
            "suggestions": suggestions
        }
    )

@router.post("/retrieve", response_class=HTMLResponse)
def retrieve_answer(request: Request, cluster_data: ClusterModel):
    client = together_client.TogetherClient()
    results = client.get_records_by_cluster_idx(cluster_idx=cluster_data.hn_cluster_idx)
    sources = {r["title"]:f"https://news.ycombinator.com/item?id={r['hn_post_id']}" for r in results}
    answer = client.retrieve_answer(question=cluster_data.question, titles=list(sources.keys()))
    return template.TemplateResponse(
        "answer.html", {
            "request": request,
            "answer": answer,
            "question": cluster_data.question,
            "sources": sources,
        }
    )

