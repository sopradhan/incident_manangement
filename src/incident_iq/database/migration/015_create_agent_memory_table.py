"""Create agent_memory table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS agent_memory (
        memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        memory_type TEXT,
        content TEXT,
        importance_score REAL DEFAULT 0.5,
        created_at TEXT DEFAULT (datetime('now')),
        last_accessed TEXT DEFAULT (datetime('now'))
    );
    ''')
    conn.commit()
