"""Create department_users pivot table"""


def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS department_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(department_id) REFERENCES departments(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(department_id, user_id)
    );
    ''')
    conn.commit()