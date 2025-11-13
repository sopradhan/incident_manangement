def run(conn):
    # Root User → Admin
    cur_user = conn.execute("SELECT id FROM users WHERE email = ?", ('root@example.com',)).fetchone()
    cur_role = conn.execute("SELECT id FROM roles WHERE name = ?", ('admin',)).fetchone()
    if cur_user and cur_role:
        conn.execute('INSERT OR IGNORE INTO user_roles (user_id, role_id, company_id) VALUES (?, ?, ?)', (cur_user['id'], cur_role['id'], 1))

    # Alice → Employee
    cur_user = conn.execute("SELECT id FROM users WHERE email = ?", ('svk@example.com',)).fetchone()
    cur_role = conn.execute("SELECT id FROM roles WHERE name = ?", ('manager',)).fetchone()
    if cur_user and cur_role:
        conn.execute('INSERT OR IGNORE INTO user_roles (user_id, role_id, company_id) VALUES (?, ?, ?)', (cur_user['id'], cur_role['id'],2))
    
    cur_user = conn.execute("SELECT id FROM users WHERE email = ?", ('srv@example.com',)).fetchone()
    cur_role = conn.execute("SELECT id FROM roles WHERE name = ?", ('devloper',)).fetchone()
    if cur_user and cur_role:
        conn.execute('INSERT OR IGNORE INTO user_roles (user_id, role_id, company_id) VALUES (?, ?, ?)', (cur_user['id'], cur_role['id'],2))

    cur_user = conn.execute("SELECT id FROM users WHERE email = ?", ('prs@example.com',)).fetchone()
    cur_role = conn.execute("SELECT id FROM roles WHERE name = ?", ('employee',)).fetchone()
    if cur_user and cur_role:
        conn.execute('INSERT OR IGNORE INTO user_roles (user_id, role_id, company_id) VALUES (?, ?, ?)', (cur_user['id'], cur_role['id'],2))

    cur_user = conn.execute("SELECT id FROM users WHERE email = ?", ('rpk@example.com',)).fetchone()
    cur_role = conn.execute("SELECT id FROM roles WHERE name = ?", ('devloper',)).fetchone()
    if cur_user and cur_role:
        conn.execute('INSERT OR IGNORE INTO user_roles (user_id, role_id, company_id) VALUES (?, ?, ?)', (cur_user['id'], cur_role['id'],2))

    cur_user = conn.execute("SELECT id FROM users WHERE email = ?", ('sdk@example.com',)).fetchone()
    cur_role = conn.execute("SELECT id FROM roles WHERE name = ?", ('employee',)).fetchone()
    if cur_user and cur_role:
        conn.execute('INSERT OR IGNORE INTO user_roles (user_id, role_id, company_id) VALUES (?, ?, ?)', (cur_user['id'], cur_role['id'],2))

    conn.commit()
