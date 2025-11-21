"""Create llm_token_usage table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS llm_token_usage (
        token_id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_id INTEGER,
        model_name TEXT,
        input_tokens INTEGER DEFAULT 0,
        output_tokens INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0,
        cost_usd REAL DEFAULT 0.0,
        timestamp TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (operation_id) REFERENCES agent_operations(operation_id) ON DELETE CASCADE
    );
    ''')
    conn.commit()
