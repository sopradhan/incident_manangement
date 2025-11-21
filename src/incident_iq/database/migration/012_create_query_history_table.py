"""Create query_history table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS query_history (
        query_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        query_text TEXT,
        response_text TEXT,
        num_results INTEGER,
        execution_time_ms INTEGER,
        timestamp TEXT DEFAULT (datetime('now'))
    );
    ''')
    conn.commit()
