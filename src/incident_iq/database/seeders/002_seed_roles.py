table_name = "roles"

def run(conn):
    # Skip if already synced by unified sync seeder
    cursor = conn.execute("SELECT COUNT(*) as count FROM roles")
    row = cursor.fetchone()
    if row and row['count'] > 0:
        print("✓ Roles already synced. Skipping 002_seed_roles.")
        return
    
    roles = ['admin', 'manager','developer', 'employee',]
    for r in roles:
        conn.execute('INSERT OR IGNORE INTO roles (name) VALUES (?)', (r,))
    conn.commit()
