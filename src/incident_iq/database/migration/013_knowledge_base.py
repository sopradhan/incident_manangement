def run(conn):
    conn.execute('''
    CREATE TABLE if not exists knowledge_base (
        id TEXT PRIMARY KEY,
        cause TEXT NOT NULL,
        description TEXT NOT NULL,
        impact TEXT NOT NULL,
        remediation_steps TEXT NOT NULL,
        rca TEXT NOT NULL,
        business_impact TEXT NOT NULL,
        estimated_recovery_time TEXT NOT NULL,
        environment TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    ''')
    conn.commit()