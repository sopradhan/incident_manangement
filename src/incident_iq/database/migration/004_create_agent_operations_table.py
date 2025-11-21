"""Create agent_operations table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS agent_operations (
        operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id TEXT NOT NULL,
        operation_type TEXT,
        status TEXT,
        input_data TEXT,
        output_data TEXT,
        error_message TEXT,
        timestamp TEXT DEFAULT (datetime('now')),
        execution_time_ms INTEGER
    );
    ''')
    conn.commit()
