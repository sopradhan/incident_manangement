"""Create departments table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE
    );
    ''')
    conn.commit()