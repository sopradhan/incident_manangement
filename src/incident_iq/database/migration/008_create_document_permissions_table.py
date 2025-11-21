"""Create document_permissions table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS document_permissions (
        permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_id TEXT NOT NULL,
        cdr_code TEXT NOT NULL,
        sensitivity TEXT,
        subject TEXT,
        assigned_by TEXT DEFAULT 'llm_inference',
        timestamp TEXT DEFAULT (datetime('now')),
        UNIQUE(doc_id, cdr_code),
        FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
    );
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_doc_perms_doc ON document_permissions(doc_id);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_doc_perms_cdr ON document_permissions(cdr_code);')
    conn.commit()
