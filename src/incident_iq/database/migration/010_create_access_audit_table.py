"""Create access_audit table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS access_audit (
        audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        doc_id TEXT NOT NULL,
        granted BOOLEAN,
        user_roles TEXT,
        required_roles TEXT,
        timestamp TEXT DEFAULT (datetime('now'))
    );
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_access_audit_user ON access_audit(user_id);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_access_audit_doc ON access_audit(doc_id);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_access_audit_timestamp ON access_audit(timestamp);')
    conn.commit()
