import sys
import os
from pathlib import Path

# Add src to path for imports using relative path
script_dir = Path(__file__).parent
project_root = script_dir.parent
src_dir = project_root / 'src'
sys.path.insert(0, str(src_dir))

from incident_iq.database.db.connection import init_db, get_db_path


def main():
    print("=" * 60)
    print("Incident Management Database Initialization")
    print("=" * 60)
    
    try:
        print("\nInitializing database...")
        conn = init_db()
        
        db_path = get_db_path()
        print(f"\n✓ Database initialized successfully!")
        print(f"  Database location: {db_path}")
        print(f"  Database exists: {os.path.exists(db_path)}")
        print(f"  Database size: {os.path.getsize(db_path)} bytes")
        
        # Test connection
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n✓ {len(tables)} tables created:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} records")
        
        conn.close()
        print("\n" + "=" * 60)
        print("Database initialization complete!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
