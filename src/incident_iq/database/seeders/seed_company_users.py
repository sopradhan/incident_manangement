def run(conn):
    cur = conn.execute("SELECT id FROM companies WHERE name = ?", ('Acme Corp',))
    company = cur.fetchone()
    if not company:
        return
    cid = company['id']

    users = conn.execute("SELECT id, email FROM users").fetchall()
    for user in users:
        if 'sdk' in user['email'] or 'prs' in user['email']:
            role = 'employee'
        elif 'rpk' in user['email'] or 'srv' in user['email']:
            role = 'developer'
        elif 'svk' in user['email']:
            role = 'manager'

        conn.execute('INSERT OR IGNORE INTO company_users (company_id, user_id, role) VALUES (?, ?, ?)', (cid, user['id'], role))

    conn.commit()

