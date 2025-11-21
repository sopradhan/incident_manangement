"""Create query_heatmap table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS query_heatmap (
        heatmap_id INTEGER PRIMARY KEY AUTOINCREMENT,
        query_text TEXT,
        num_invocations INTEGER DEFAULT 0,
        avg_user_feedback REAL DEFAULT 0.0,
        retrieval_accuracy REAL DEFAULT 0.0,
        avg_response_time_ms REAL DEFAULT 0.0,
        last_queried TEXT DEFAULT (datetime('now')),
        created_at TEXT DEFAULT (datetime('now'))
    );
    ''')
    conn.commit()
