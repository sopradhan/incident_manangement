import sys
from pathlib import Path
from importlib import import_module
from incident_iq.database.db.connection import get_connection
from incident_iq.database.seeders.seed_incident_log import auto_run
import time

# --- Ensure consistent project root ---
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "src" / "incident_iq" / "database"

sys.path.append(str(DATABASE_DIR))

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

        with open(file, 'r') as f:
            code = f.read()

        namespace = {'conn' :conn}
        exec(code, namespace)

        if 'table_name' in namespace:
            table_name = namespace['table_name']
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]

            if count > 0:
                continue

        if 'run' in namespace:
            namespace['run'](conn)
    
    print("Seeders complete.\n")

def run():
    conn = get_connection()

    run_migrations(conn)
    run_seeders(conn)

    # Show record counts
    # print("📊 Final counts:")
    # for table in [
    #     "companies",
    #     "departments",
    #     "users",
    #     "roles",
    #     "user_roles",
    #     "company_users",
    #     "department_users",
    #     "incident_logs",
    #     "classifier_outputs",
    #     "severity_rules",
    #     "queue",
    #     "report",
    #     "knowledge_base"
    # ]:
    #     try:
    #         count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    #         print(f"{table}: {count}")
    #     except Exception:
    #         pass

    # conn.close()


if __name__ == "__main__":
    run()
    # conn = get_connection()
    # while True:
    #     auto_run(conn)
    #     time.sleep(10)
