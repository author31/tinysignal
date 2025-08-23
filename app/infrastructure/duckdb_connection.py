import duckdb

conn = None

def init_conn():
    global conn
    
    if conn: return
    
    conn = duckdb.connect(":memory:")
    
    # Initialize cache table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key VARCHAR PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at TIMESTAMP DEFAULT NULL
        )
    """)
    
    return conn

def get_conn():
    global conn
    if not conn: return init_conn()
    
    return conn
