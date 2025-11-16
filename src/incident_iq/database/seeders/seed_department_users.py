def run(conn):
    # Get department
    dept = conn.execute(
        "SELECT id FROM departments WHERE name = ?",
        ('Engineering',)
    ).fetchone()

    # if not dept:
    #     return

    # List of user emails to assign to the department
    emails = [
        'svk@epoch.com',
        'srv@epoch.com',
        'prs@epoch.com',
        'rpk@epoch.com',
        'sdk@epoch.com'
    ]

    for email in emails:
        user = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if user:
            conn.execute(
                'INSERT OR IGNORE INTO department_users (department_id, user_id) VALUES (?, ?)',
                (dept['id'], user['id'])
            )

    conn.commit()
