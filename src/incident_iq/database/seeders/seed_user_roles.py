def run(conn):
    assignments = [
        # email,        role,       company_id
        ('root@epoch.com', 'admin',     1),
        ('svk@epoch.com',  'manager',   2),
        ('srv@epoch.com',  'developer',  2),
        ('prs@epoch.com',  'employee',  2),
        ('rpk@epoch.com',  'developer',  2),
        ('sdk@epoch.com',  'employee',  2),
    ]

    for email, role_name, company_id in assignments:
        user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        role = conn.execute(
            "SELECT id FROM roles WHERE name = ?",
            (role_name,)
        ).fetchone()

        if user and role:
            conn.execute(
                "INSERT OR IGNORE INTO user_roles (user_id, role_id, company_id) VALUES (?, ?, ?)",
                (user['id'], role['id'], company_id)
            )

    conn.commit()
