def run(conn):
    # Skip if already synced by unified sync seeder
    cursor = conn.execute("SELECT COUNT(*) as count FROM user_roles")
    row = cursor.fetchone()
    if row and row['count'] > 0:
        print("✓ User-roles already synced. Skipping seed_user_roles.")
        return
    
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
