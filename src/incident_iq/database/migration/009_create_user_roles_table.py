"""Create user_roles table"""

def run(conn):
    try:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS user_roles (
            user_role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            cdr_code TEXT NOT NULL,
            company_id INTEGER,
            department_id INTEGER,
            role_id INTEGER,
            granted_date TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, cdr_code)
        );
        ''')
    except Exception as e:
        print(f"Error creating user_roles table: {e}")
        raise
    
    try:
        conn.execute('CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);')
    except:
        pass  # Index might already exist
    
    try:
        conn.execute('CREATE INDEX IF NOT EXISTS idx_user_roles_cdr ON user_roles(cdr_code);')
    except:
        pass  # Index might already exist
    
    conn.commit()