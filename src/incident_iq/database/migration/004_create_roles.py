"""Create roles table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    guard TEXT DEFAULT 'web',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
    );
    ''')
    conn.commit()