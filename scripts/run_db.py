import sys
from pathlib import Path
from importlib import import_module
from incident_iq.database.db.connection import get_connection
from incident_iq.database.seeders.seed_incident_log import auto_run
import time

# --- Ensure consistent project root ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

def run_migrations(conn):
    
    migrations_dir = BASE_DIR / "migrations"

    for file in sorted(migrations_dir.glob("*.py")):
        module_name = f"migrations.{file.stem}"
        module = import_module(module_name)
        if hasattr(module, "run"):
            module.run(conn)

def run_seeders(conn):
    seeders_dir = BASE_DIR / "seeders"

    for file in sorted(seeders_dir.glob("*.py")):
        module_name = f"seeders.{file.stem}"
        module = import_module(module_name)

        if hasattr(module, "run"):
            if hasattr(module,"table_name"):
                table_name = module.table_name
                cursor =conn.cursor()
                cursor.execute(f"select count(*) from {table_name}")
                count = cursor.fetchone() [0]

                if count > 0:
                    continue

                else:
                    module.run(conn)

            else:
                module.run(conn)

def run():
    conn = get_connection()

    run_migrations(conn)
    run_seeders(conn)

    # Show record counts
    print("📊 Final counts:")
    for table in [
        "companies",
        "departments",
        "users",
        "roles",
        "user_roles",
        "company_users",
        "department_users",
        "incident_logs",
        "classifier_outputs",
        "severity_rules",
        "queue",
        "report",
        "knowledge_base"
    ]:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {count}")
        except Exception:
            pass

    # conn.close()


if __name__ == "__main__":
    run()
    conn = get_connection()
    while True:
        auto_run(conn)
        time.sleep(30)
