"""Create company_users pivot table"""


def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS company_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(company_id, user_id)
    );
    ''')
    conn.commit()