"""Create healing_operations table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS healing_operations (
        operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_type TEXT,
        description TEXT,
        status TEXT,
        result TEXT,
        timestamp TEXT DEFAULT (datetime('now'))
    );
    ''')
    conn.commit()
