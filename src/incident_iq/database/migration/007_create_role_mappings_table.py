"""Create role_mappings table"""

def run(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS role_mappings (
        mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        department_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        cdr_code TEXT NOT NULL UNIQUE,
        company_name TEXT,
        department_name TEXT,
        role_name TEXT,
        access_level INTEGER,
        UNIQUE(company_id, department_id, role_id)
    );
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_role_cdr ON role_mappings(cdr_code);')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_role_company ON role_mappings(company_id);')
    conn.commit()
