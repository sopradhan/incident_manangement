"""Create synthetic_queries table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS synthetic_queries (
        query_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id TEXT NOT NULL,
        question TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    ''')
    conn.commit()
