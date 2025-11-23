"""
Role Mappings Seeder
Populates initial CDR (Company-Department-Role) code mappings from rbac_config.yaml
These are the role definitions that control access control in the system
Run once during initial database setup - uses INSERT OR IGNORE to prevent duplicates
"""
import yaml
from pathlib import Path

table_name = "role_mappings"


def load_rbac_config():
    """
    Load RBAC configuration from rbac_config.yaml
    
    Returns:
        Dictionary with role_mappings from config, or default mappings if file not found
    """
    # Construct path to rbac_config.yaml relative to this file
    try:
        config_path = Path(__file__).parent.parent.parent / "rag" / "config" / "rbac_config.yaml"
    except NameError:
        # If __file__ is not defined (e.g., in exec context), use current working directory
        config_path = Path.cwd() / "src" / "incident_iq" / "rag" / "config" / "rbac_config.yaml"
    
    if not config_path.exists():
        # Return default role mappings if config file not found
        print(f"⚠ RBAC config file not found at: {config_path}")
        print("  Using default role mappings...")
        return get_default_role_mappings()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config.get('role_mappings', {})
    except Exception as e:
        print(f"⚠ Error loading RBAC config: {str(e)}")
        print("  Using default role mappings...")
        return get_default_role_mappings()


def get_default_role_mappings():
    """
    Return default role mappings if config file not available
    """
    return {
        "CDR_ADMIN_ALL": {
            "company_id": 1,
            "department_id": 1,
            "role_id": 1,
            "company_name": "Global",
            "department_name": "Administration",
            "role_name": "Admin",
            "access_level": 5
        },
        "CDR_USER_ALL": {
            "company_id": 1,
            "department_id": 1,
            "role_id": 2,
            "company_name": "Global",
            "department_name": "Operations",
            "role_name": "User",
            "access_level": 3
        },
        "CDR_VIEWER_ALL": {
            "company_id": 1,
            "department_id": 1,
            "role_id": 3,
            "company_name": "Global",
            "department_name": "Operations",
            "role_name": "Viewer",
            "access_level": 1
        }
    }


def run(conn):
    """
    Seed initial CDR role mappings into the database from rbac_config.yaml
    Only inserts if CDR codes don't already exist (one-time population)
    
    Args:
        conn: SQLite database connection
    """
    # Check if role_mappings already has data (one-time check)
    cursor = conn.execute("SELECT COUNT(*) as count FROM role_mappings")
    row = cursor.fetchone()
    existing_count = row['count'] if row else 0
    
    if existing_count > 0:
        print(f"✓ role_mappings table already populated with {existing_count} entries. Skipping seeding.")
        return
    
    # Load CDR mappings from rbac_config.yaml
    role_configs = load_rbac_config()
    
    # Convert config format to database tuple format
    # Format: (company_id, department_id, role_id, cdr_code, company_name, department_name, role_name, access_level)
    cdr_mappings = []
    for cdr_code, config in role_configs.items():
        mapping = (
            config.get('company_id'),
            config.get('department_id'),
            config.get('role_id'),
            cdr_code,
            config.get('company_name'),
            config.get('department_name'),
            config.get('role_name'),
            config.get('access_level')
        )
        cdr_mappings.append(mapping)
    
    # Insert only if table is empty (one-time population)
    # Using INSERT OR IGNORE as backup to prevent duplicates on cdr_code UNIQUE constraint
    for mapping in cdr_mappings:
        conn.execute("""
            INSERT OR IGNORE INTO role_mappings 
            (company_id, department_id, role_id, cdr_code, company_name, department_name, role_name, access_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, mapping)
    
    conn.commit()
    print(f"✓ Populated role_mappings table with {len(cdr_mappings)} CDR code definitions from rbac_config.yaml")
