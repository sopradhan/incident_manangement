#!/usr/bin/env python3
"""
Migration Wrapper Script: Execute optimized schema migrations
Purpose: Run migrations from src/incident_iq/database/migration/optimized_schema
Usage: python run_optimized_migration.py [--skip-drop] [--db-path PATH]
"""
import sys
import os
import sqlite3
from pathlib import Path

# Add src to path to enable imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def run_migrations_directly():
    """Run migrations directly without executing external script"""
    
    migration_dir = project_root / "src" / "incident_iq" / "database" / "migration" / "optimized_schema"
    db_path = project_root / "chroma_db" / "rag.db"
    
    print(f"Starting Optimized Schema Migration Wrapper")
    print(f"Project Root: {project_root}")
    print(f"Migration Dir: {migration_dir}")
    print(f"Database: {db_path}")
    print()
    
    if not migration_dir.exists():
        print(f"Migration directory not found at: {migration_dir}")
        sys.exit(1)
    
    # Ensure database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = {
        "success": False,
        "migrations_run": [],
        "errors": [],
    }
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Disable foreign keys for migration
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Get migration files in order
        migration_files = sorted([
            f for f in os.listdir(migration_dir)
            if f.endswith('.sql') and not f.startswith('advanced_')
        ])
        
        if not migration_files:
            print("No SQL migration files found")
            conn.close()
            return results
        
        print(f"\nRunning {len(migration_files)} migrations...")
        print(f"Database: {db_path}\n")
        
        # Execute migrations
        for migration_file in migration_files:
            migration_path = migration_dir / migration_file
            
            print(f"Running: {migration_file}...", end=" ", flush=True)
            
            try:
                # Read SQL file with UTF-8 encoding
                with open(migration_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Split into individual statements, removing comments
                statements = []
                current_stmt = []
                
                for line in sql_content.split('\n'):
                    # Remove line comments
                    if '--' in line:
                        line = line[:line.index('--')]
                    
                    line = line.strip()
                    if line:
                        current_stmt.append(line)
                    
                    # Check if statement ends with semicolon
                    if line.endswith(';'):
                        stmt = ' '.join(current_stmt)
                        if stmt:
                            statements.append(stmt)
                        current_stmt = []
                
                # Execute each statement
                for stmt in statements:
                    if stmt and not stmt.startswith('--'):
                        cursor.execute(stmt)
                
                conn.commit()
                results["migrations_run"].append(migration_file)
                print("OK")
                
            except sqlite3.Error as e:
                error_msg = f"{migration_file}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"FAILED: {e}")
                conn.rollback()
                raise
        
        # Verify schema
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\nSchema Summary:")
        print(f"Tables created: {len(tables)}")
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"  - {table} ({len(columns)} columns)")
        
        results["success"] = True
        results["final_tables"] = tables
        
        print(f"\nMigration complete!")
        print(f"All {len(migration_files)} migrations executed successfully")
        
    except Exception as e:
        results["errors"].append(str(e))
        print(f"\nMigration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if conn:
            conn.close()
    
    return results


if __name__ == "__main__":
    print("=" * 70)
    print("SQLite Schema Migration: 5 Tables -> 3 Tables (Optimized)")
    print("=" * 70)
    print()
    
    results = run_migrations_directly()
    
    print("\n" + "=" * 70)
    if results['success']:
        print("MIGRATION SUCCESSFUL")
        print(f"Migrations run: {len(results['migrations_run'])}")
    else:
        print("MIGRATION FAILED")
        if results['errors']:
            print(f"Errors: {len(results['errors'])}")
            for error in results['errors']:
                print(f"  - {error}")
    print("=" * 70)
    
    sys.exit(0 if results['success'] else 1)
