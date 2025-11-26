"""
Migration Runner: Execute optimized schema migrations
Purpose: Drop old tables and create new optimized 3-table schema
Date: 2025-11-26

WARNING: This will delete all existing metadata tables!
Backup your database before running.
"""
import os
import sqlite3
from pathlib import Path


def run_migration(db_path: str, migration_dir: str, skip_drop: bool = False) -> dict:
    """
    Run all SQL migration files in sequence
    
    Args:
        db_path: Path to SQLite database
        migration_dir: Directory containing SQL migration files
        skip_drop: If True, skip dropping old tables (useful for fresh DB)
    
    Returns:
        Dictionary with migration results
    """
    results = {
        "success": False,
        "migrations_run": [],
        "errors": [],
        "warnings": []
    }
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Get migration files in order
        migration_files = sorted([
            f for f in os.listdir(migration_dir)
            if f.endswith('.sql') and not f.startswith('advanced_')
        ])
        
        # Skip drop migration if requested
        if skip_drop and migration_files[0] == '001_drop_old_tables.sql':
            results["warnings"].append(
                "Skipping table drop (skip_drop=True). Use only for fresh databases!"
            )
            migration_files = migration_files[1:]
        
        print(f"\n📦 Running {len(migration_files)} migrations...")
        print(f"Database: {db_path}")
        print(f"Migration Dir: {migration_dir}\n")
        
        for migration_file in migration_files:
            migration_path = os.path.join(migration_dir, migration_file)
            
            print(f"▶️  Running: {migration_file}")
            
            try:
                # Read SQL file
                with open(migration_path, 'r') as f:
                    sql_content = f.read()
                
                # Split into individual statements (handle multi-statement migrations)
                statements = [
                    stmt.strip()
                    for stmt in sql_content.split(';')
                    if stmt.strip()
                ]
                
                # Execute each statement
                for stmt in statements:
                    if stmt and not stmt.startswith('--'):
                        cursor.execute(stmt)
                
                conn.commit()
                results["migrations_run"].append(migration_file)
                print(f"✅ {migration_file} - Complete\n")
                
            except sqlite3.Error as e:
                results["errors"].append({
                    "file": migration_file,
                    "error": str(e)
                })
                print(f"❌ {migration_file} - Failed: {e}\n")
                conn.rollback()
                raise
        
        # Verify schema
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        print("📊 Final Schema:")
        print(f"  - Tables created: {len(tables)}")
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"    • {table} ({len(columns)} columns)")
        
        # Summary
        results["success"] = True
        results["final_tables"] = tables
        
        print(f"\n✅ Migration complete!")
        print(f"✅ All {len(migration_files)} migrations executed successfully")
        
    except Exception as e:
        results["errors"].append({"general": str(e)})
        print(f"\n❌ Migration failed: {e}")
    
    finally:
        if conn:
            conn.close()
    
    return results


def verify_schema(db_path: str) -> dict:
    """
    Verify the new schema is correctly implemented
    """
    verification = {
        "valid": False,
        "tables": {},
        "relationships": [],
        "issues": []
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Expected tables
        expected_tables = [
            'document_metadata',
            'chunk_embedding_data',
            'rag_history_and_optimization'
        ]
        
        # Get actual tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        actual_tables = [row[0] for row in cursor.fetchall()]
        
        # Check each expected table
        for table in expected_tables:
            if table in actual_tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = {row[1]: row[2] for row in cursor.fetchall()}
                verification["tables"][table] = {
                    "exists": True,
                    "columns": columns
                }
            else:
                verification["issues"].append(f"Missing table: {table}")
        
        # Check foreign key relationships
        cursor.execute("PRAGMA foreign_key_list(chunk_embedding_data)")
        fk_rows = cursor.fetchall()
        if fk_rows:
            verification["relationships"].append(
                f"chunk_embedding_data → document_metadata (via doc_id)"
            )
        
        cursor.execute("PRAGMA foreign_key_list(rag_history_and_optimization)")
        fk_rows = cursor.fetchall()
        if fk_rows:
            verification["relationships"].append(
                f"rag_history_and_optimization → document_metadata (via target_doc_id)"
            )
        
        # Overall validation
        verification["valid"] = (
            len(expected_tables) == len(actual_tables) and
            len(verification["issues"]) == 0
        )
        
        conn.close()
        
    except Exception as e:
        verification["issues"].append(f"Verification error: {str(e)}")
    
    return verification


if __name__ == "__main__":
    import sys
    
    # Default paths
    db_path = os.getenv(
        "CHROMA_DB_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "chroma_db", "rag.db")
    )
    
    migration_dir = os.path.dirname(__file__)
    
    print("=" * 70)
    print("🚀 SQLite Schema Migration: 5 Tables → 3 Tables (Optimized)")
    print("=" * 70)
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"\n⚠️  Database not found at: {db_path}")
        print("Creating new database...")
        skip_drop = True
    else:
        print(f"\n⚠️  WARNING: This will drop all existing metadata tables!")
        confirm = input("Type 'YES' to proceed with migration: ")
        if confirm != 'YES':
            print("Migration cancelled.")
            sys.exit(0)
        skip_drop = False
    
    # Run migration
    results = run_migration(db_path, migration_dir, skip_drop=skip_drop)
    
    # Verify schema
    print("\n" + "=" * 70)
    print("🔍 Schema Verification")
    print("=" * 70)
    verification = verify_schema(db_path)
    
    print(f"\n✅ Schema valid: {verification['valid']}")
    
    if verification['relationships']:
        print("\n🔗 Table Relationships:")
        for rel in verification['relationships']:
            print(f"  • {rel}")
    
    if verification['issues']:
        print("\n⚠️  Issues found:")
        for issue in verification['issues']:
            print(f"  • {issue}")
    
    # Report
    print("\n" + "=" * 70)
    if results['success']:
        print("✅ MIGRATION SUCCESSFUL")
        print(f"   Migrations run: {len(results['migrations_run'])}")
        print(f"   Tables created: {len(verification['tables'])}")
    else:
        print("❌ MIGRATION FAILED")
        print(f"   Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"   - {error}")
    print("=" * 70)
