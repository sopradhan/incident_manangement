"""Create embedding_metadata table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS embedding_metadata (
        embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id TEXT NOT NULL,
        chunk_id TEXT NOT NULL,
        chunk_strategy TEXT,
        chunk_size INTEGER,
        overlap INTEGER,
        embedding_model TEXT,
        embedding_version TEXT,
        quality_score REAL DEFAULT 0.5,
        reindex_count INTEGER DEFAULT 0,
        last_modified TEXT DEFAULT (datetime('now')),
        UNIQUE(chunk_id),
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    ''')
    conn.commit()
