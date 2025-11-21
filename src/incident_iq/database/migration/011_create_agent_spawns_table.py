"""Create agent_spawns table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS agent_spawns (
        spawn_id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_agent_id TEXT,
        child_agent_id TEXT NOT NULL,
        spawn_reason TEXT,
        timestamp TEXT DEFAULT (datetime('now'))
    );
    ''')
    conn.commit()
