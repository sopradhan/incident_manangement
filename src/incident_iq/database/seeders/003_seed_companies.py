table_name = "companies"

def run(conn):
    conn.execute("INSERT OR IGNORE INTO companies (id, name) VALUES (1, 'Root_Company')")
    conn.execute("INSERT OR IGNORE INTO companies (name) VALUES (?)", ('Acme Corp',))
    conn.commit()