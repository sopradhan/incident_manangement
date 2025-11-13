def run(conn):
    dept = conn.execute("SELECT id FROM departments WHERE name = ?", ('Engineering',)).fetchone()
    user = conn.execute("SELECT id FROM users WHERE email = ?", ('svk@example.com',)).fetchone()
    if dept and user:
        conn.execute('INSERT OR IGNORE INTO department_users (department_id, user_id) VALUES (?, ?)', (dept['id'], user['id']))
        conn.commit()

    user = conn.execute("SELECT id FROM users WHERE email = ?", ('srv@example.com',)).fetchone()
    if dept and user:
        conn.execute('INSERT OR IGNORE INTO department_users (department_id, user_id) VALUES (?, ?)', (dept['id'], user['id']))
        conn.commit()

    user = conn.execute("SELECT id FROM users WHERE email = ?", ('prs@example.com',)).fetchone()
    if dept and user:
        conn.execute('INSERT OR IGNORE INTO department_users (department_id, user_id) VALUES (?, ?)', (dept['id'], user['id']))
        conn.commit()

    user = conn.execute("SELECT id FROM users WHERE email = ?", ('rpk@example.com',)).fetchone()
    if dept and user:
        conn.execute('INSERT OR IGNORE INTO department_users (department_id, user_id) VALUES (?, ?)', (dept['id'], user['id']))
        conn.commit()

    user = conn.execute("SELECT id FROM users WHERE email = ?", ('sdk@example.com',)).fetchone()
    if dept and user:
        conn.execute('INSERT OR IGNORE INTO department_users (department_id, user_id) VALUES (?, ?)', (dept['id'], user['id']))
        conn.commit()