"""
Unified Table Sync Seeder - ONE COMPANY SYNC (No JSON Dependency)
==================================================================
Synchronizes all tables (companies, departments, roles, users, company_users, user_roles) 
based on role_mappings table as the source of truth.

All role mapping data is embedded in this seeder - no external JSON configuration needed.

Execution Flow:
1. Populate role_mappings table (source of truth - embedded data)
2. Extract unique companies, departments, roles from role_mappings
3. Create companies, departments, roles, users from extracted data
4. Link users to company and roles
5. Verify all connections

Run once during initial database setup.
"""

table_name = "unified_sync"


def get_default_role_mappings():
    """Default role mappings for single company setup - embedded, no JSON dependency"""
    return [
        {
            "cdr_code": "111",
            "company_id": 1,
            "company_name": "Acme Corp",
            "department_id": 1,
            "department_name": "General",
            "role_id": 1,
            "role_name": "Viewer",
            "access_level": 1
        },
        {
            "cdr_code": "112",
            "company_id": 1,
            "company_name": "Acme Corp",
            "department_id": 2,
            "department_name": "HR",
            "role_id": 2,
            "role_name": "Associate",
            "access_level": 2
        },
        {
            "cdr_code": "121",
            "company_id": 1,
            "company_name": "Acme Corp",
            "department_id": 3,
            "department_name": "Engineering",
            "role_id": 3,
            "role_name": "Engineer",
            "access_level": 3
        },
        {
            "cdr_code": "131",
            "company_id": 1,
            "company_name": "Acme Corp",
            "department_id": 4,
            "department_name": "Finance",
            "role_id": 4,
            "role_name": "Analyst",
            "access_level": 2
        },
        {
            "cdr_code": "141",
            "company_id": 1,
            "company_name": "Acme Corp",
            "department_id": 5,
            "department_name": "Security",
            "role_id": 5,
            "role_name": "Admin",
            "access_level": 5
        }
    ]


def run(conn):
    """
    Main synchronization function
    Synchronizes all tables based on role_mappings table as source of truth
    """
    
    print("\n" + "="*70)
    print("STARTING UNIFIED TABLE SYNC (One Company - Embedded Data)")
    print("="*70)
    
    # Always populate role_mappings (it's the source of truth)
    # DELETE existing mappings first to ensure fresh sync
    conn.execute("DELETE FROM role_mappings")
    conn.commit()
    
    # Load embedded role mappings (no JSON dependency)
    role_mappings_data = get_default_role_mappings()
    print(f"\n✓ Loaded {len(role_mappings_data)} role mappings from embedded defaults")
    
    # Step 1: Populate role_mappings table first (source of truth)
    print("\n[1/6] Populating role_mappings table (source of truth)...")
    for mapping in role_mappings_data:
        conn.execute("""
            INSERT OR IGNORE INTO role_mappings 
            (company_id, department_id, role_id, cdr_code, company_name, 
             department_name, role_name, access_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mapping['company_id'],
            mapping['department_id'],
            mapping['role_id'],
            mapping['cdr_code'],
            mapping['company_name'],
            mapping['department_name'],
            mapping['role_name'],
            mapping['access_level']
        ))
    conn.commit()
    print(f"  ✓ Populated role_mappings with {len(role_mappings_data)} CDR codes")
    
    # Extract unique companies, departments, and roles FROM role_mappings table
    print("\n[2/6] Extracting companies, departments, and roles from role_mappings...")
    
    cursor = conn.execute("""
        SELECT DISTINCT company_id, company_name FROM role_mappings ORDER BY company_id
    """)
    companies = cursor.fetchall()
    companies_count = len(companies)
    
    cursor = conn.execute("""
        SELECT DISTINCT company_id, department_id, department_name FROM role_mappings 
        ORDER BY company_id, department_id
    """)
    departments = cursor.fetchall()
    departments_count = len(departments)
    
    cursor = conn.execute("""
        SELECT DISTINCT role_id, role_name FROM role_mappings ORDER BY role_id
    """)
    roles = cursor.fetchall()
    roles_count = len(roles)
    
    print(f"  ✓ Found {companies_count} companies")
    print(f"  ✓ Found {departments_count} departments")
    print(f"  ✓ Found {roles_count} roles")
    
    # Step 3: Create companies
    print("\n[3/6] Creating companies...")
    for company in companies:
        conn.execute("""
            INSERT OR IGNORE INTO companies (name)
            VALUES (?)
        """, (company['company_name'],))
    conn.commit()
    print(f"  ✓ Created {companies_count} company/companies")
    
    # Step 4: Create departments
    print("\n[4/6] Creating departments...")
    for dept in departments:
        conn.execute("""
            INSERT OR IGNORE INTO departments (company_id, name)
            VALUES (?, ?)
        """, (dept['company_id'], dept['department_name']))
    conn.commit()
    print(f"  ✓ Created {departments_count} departments")
    
    # Step 5: Create roles
    print("\n[5/6] Creating roles...")
    for role in roles:
        conn.execute("""
            INSERT OR IGNORE INTO roles (name, guard)
            VALUES (?, ?)
        """, (role['role_name'], 'web'))
    conn.commit()
    print(f"  ✓ Created {roles_count} roles")
    
    # Step 6: Create test users and link to company and roles
    print("\n[6/6] Creating test users and assigning to roles...")
    
    # Get company id
    cursor = conn.execute("SELECT id FROM companies LIMIT 1")
    company_row = cursor.fetchone()
    company_id = company_row['id'] if company_row else 1
    
    # Create one test user per role
    users_created = 0
    for role in roles:
        role_name = role['role_name']
        user_email = f"test_{role_name.lower().replace(' ', '_')}@acme.local"
        user_name = f"Test {role_name}"
        
        conn.execute("""
            INSERT OR IGNORE INTO users (name, email, password)
            VALUES (?, ?, ?)
        """, (user_name, user_email, None))
        users_created += 1
    conn.commit()
    print(f"  ✓ Created {users_created} test users")
    
    # Get all users and roles
    cursor = conn.execute("SELECT id, name FROM users ORDER BY id")
    users = cursor.fetchall()
    
    # Link users to company
    for user in users:
        conn.execute("""
            INSERT OR IGNORE INTO company_users (company_id, user_id, role)
            VALUES (?, ?, ?)
        """, (company_id, user['id'], user['name']))
    conn.commit()
    print(f"  ✓ Linked {len(users)} users to company")
    
    # Assign roles to users (match by role name from "Test RoleName" -> "RoleName")
    roles_assigned = 0
    for user in users:
        user_name = user['name']
        role_name_from_user = user_name.replace("Test ", "").strip()
        
        cursor = conn.execute("""
            SELECT id FROM roles WHERE name = ?
        """, (role_name_from_user,))
        role_row = cursor.fetchone()
        
        if role_row:
            conn.execute("""
                INSERT OR IGNORE INTO user_roles (user_id, role_id, company_id)
                VALUES (?, ?, ?)
            """, (user['id'], role_row['id'], company_id))
            roles_assigned += 1
    
    conn.commit()
    print(f"  ✓ Assigned roles to {roles_assigned} users")
    
    # Verification
    print("\n" + "="*70)
    print("SYNCHRONIZATION COMPLETE - Summary:")
    print("="*70)
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM companies")
    companies_count = cursor.fetchone()['count']
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM departments")
    departments_count = cursor.fetchone()['count']
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM roles")
    roles_count = cursor.fetchone()['count']
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM users")
    users_count = cursor.fetchone()['count']
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM company_users")
    company_users_count = cursor.fetchone()['count']
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM user_roles")
    user_roles_count = cursor.fetchone()['count']
    
    cursor = conn.execute("SELECT COUNT(*) as count FROM role_mappings")
    role_mappings_count = cursor.fetchone()['count']
    
    print(f"\n✓ Companies:       {companies_count}")
    print(f"✓ Departments:     {departments_count}")
    print(f"✓ Roles:           {roles_count}")
    print(f"✓ Users:           {users_count}")
    print(f"✓ Company-Users:   {company_users_count}")
    print(f"✓ User-Roles:      {user_roles_count}")
    print(f"✓ Role-Mappings:   {role_mappings_count} (source of truth - embedded)")
    print("\n" + "="*70 + "\n")
