table_name = "departments"

def run(conn):
    cur = conn.execute("SELECT id FROM companies WHERE name = ?", ('Acme Corp',))
    row = cur.fetchone()
    if row:
        company_id = row['id']
        conn.execute('INSERT OR IGNORE INTO departments (company_id, name) VALUES (?, ?)', (company_id, 'Engineering'))
        conn.execute('INSERT OR IGNORE INTO departments (company_id, name) VALUES (?, ?)', (company_id, 'HR'))
        conn.commit()
