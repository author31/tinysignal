import json
import time
from typing import Any, Optional

from app.infrastructure import duckdb_connection


def _init_cache_table():
    """Initialize the cache table if it doesn't exist"""
    conn = duckdb_connection.get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key VARCHAR PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at TIMESTAMP DEFAULT NULL
        )
    """)


def set(key: str, value: Any, ttl: int = None) -> None:
    """Cache value to key with optional TTL in seconds"""
    conn = duckdb_connection.get_conn()
    _init_cache_table()
    
    serialized_value = json.dumps(value)
    
    if ttl:
        expires_at = time.time() + ttl
        conn.execute("""
            INSERT OR REPLACE INTO cache (key, value, expires_at)
            VALUES (?, ?, to_timestamp(?))
        """, [key, serialized_value, expires_at])
    else:
        conn.execute("""
            INSERT OR REPLACE INTO cache (key, value, expires_at)
            VALUES (?, ?, NULL)
        """, [key, serialized_value])


def get(key: str) -> Any:
    """Get cached value by key, returns None if not found or expired"""
    conn = duckdb_connection.get_conn()
    _init_cache_table()
    
    result = conn.execute("""
        SELECT value, expires_at
        FROM cache
        WHERE key = ?
        AND (expires_at IS NULL OR expires_at > current_timestamp)
    """, [key]).fetchone()
    
    if not result:
        return None
    
    try:
        return json.loads(result[0])
    except (json.JSONDecodeError, IndexError):
        return None


def delete(key: str) -> bool:
    """Delete cached value by key, returns True if deleted"""
    conn = duckdb_connection.get_conn()
    _init_cache_table()
    
    result = conn.execute("DELETE FROM cache WHERE key = ?", [key])
    return result.rowcount > 0


def clear() -> int:
    """Clear all cached values, returns number of cleared entries"""
    conn = duckdb_connection.get_conn()
    _init_cache_table()
    
    result = conn.execute("DELETE FROM cache")
    return result.rowcount


def clear_expired() -> int:
    """Clear expired cached values, returns number of cleared entries"""
    conn = duckdb_connection.get_conn()
    _init_cache_table()
    
    result = conn.execute("DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at <= current_timestamp")
    return result.rowcount