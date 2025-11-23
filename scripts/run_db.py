import sys
import os
from pathlib import Path
from importlib import import_module, reload
import time
import sqlite3

# --- Ensure consistent project root ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "src" / "incident_iq" / "database"
CORRECT_DB_PATH = DATABASE_DIR / "data" / "incident_iq.db"

# Set environment variable BEFORE importing connection module
os.environ["INCIDENT_IQ_DB_PATH"] = str(CORRECT_DB_PATH)

# Now import - but it might already be in sys.modules, so reload it
import incident_iq.database.db.connection as connection_module
reload(connection_module)
from incident_iq.database.db.connection import get_connection
# from incident_iq.database.seeders.seed_incident_logs import auto_run

sys.path.append(str(DATABASE_DIR))

print(f"[OK] Script location: {Path(__file__).resolve()}")
print(f"[OK] BASE_DIR: {BASE_DIR}")
print(f"[OK] DATABASE_DIR: {DATABASE_DIR}")
print(f"[OK] CORRECT_DB_PATH: {CORRECT_DB_PATH}")

def run_migrations(conn):
    
    migrations_dir = DATABASE_DIR / "migration"

    for file in sorted(migrations_dir.glob("*.py")):
        with open(file, 'r') as f:
            code = f.read()
        
        namespace = {'conn' :conn}
        exec(code, namespace)

        if 'run' in namespace:
            namespace['run'](conn)

    print("Migration completed.\n")

def run_seeders(conn):
    seeders_dir = DATABASE_DIR / "seeders"

    for file in sorted(seeders_dir.glob("*.py")):
        filename = file.name
        
        with open(file, 'r') as f:
            code = f.read()

        namespace = {'conn' :conn}
        exec(code, namespace)

        # Skip table_name check for unified sync seeder (000_sync_tables_one_company)
        # It handles its own idempotency internally
        if 'table_name' in namespace:
            if namespace['table_name'] == "unified_sync":
                # Always run unified sync seeder
                if 'run' in namespace:
                    namespace['run'](conn)
            else:
                # Other seeders: skip if table already has data
                table_name = namespace['table_name']
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]

                if count > 0:
                    continue
                    
                if 'run' in namespace:
                    namespace['run'](conn)
        elif 'run' in namespace:
            namespace['run'](conn)
    
    print("Seeders complete.\n")

def run():
    conn = get_connection()

    run_migrations(conn)
    run_seeders(conn)

    conn.commit()
    conn.close()
    
    print("\n[OK] Database setup complete!")
    print("[OK] Database saved to: src/incident_iq/database/data/incident_iq.db")


if __name__ == "__main__":
    run()