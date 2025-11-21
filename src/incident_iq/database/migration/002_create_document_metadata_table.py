"""Create document_metadata table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS document_metadata (
        metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id TEXT NOT NULL,
        key TEXT,
        value TEXT,
        FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    ''')
    conn.commit()
