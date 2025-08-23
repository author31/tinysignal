import hashlib
import json
import os
from typing import Callable, Dict

from fastapi import Request

from app import sql_engine
from app.services import cache


async def cache_middleware(request: Request, call_next):
    cache_key = f"cache-{request.url.path}"
    cached_response = cache.get(cache_key)
    
    if cached_response is not None:
        return cached_response

    response = await call_next(request)
    cache.set(cache_key, response)

def db_cache_wrapper(engine: sql_engine.SQLEngine, query: str, select_data: tuple=None):
    _hash = hashlib.md5(query.encode("utf-8")).hexdigest()
    cache_key = f"cache-{_hash}"
    cached_response = cache.get(cache_key)
    
    if cached_response is not None: return cached_response

    response = engine.execute_select_query(query, select_data=select_data)
    cache.set(cache_key, response, ttl=30)
    return response
