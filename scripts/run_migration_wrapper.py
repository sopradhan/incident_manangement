#!/usr/bin/env python3
"""
Advanced Migration Wrapper: Execute optimized schema migrations
Purpose: Provide command-line interface for running migrations with various options
Usage: python run_migration_wrapper.py [options]

Options:
  --skip-drop          Skip dropping old tables (use for fresh DB)
  --db-path PATH       Custom database path
  --verify-only        Only verify schema, don't migrate
  --verbose            Enable verbose output
  --help               Show this help message
"""
import sys
import os
import sqlite3
import argparse
from pathlib import Path
from typing import Dict, Any


def get_migration_script_path() -> Path:
    """Get path to the optimized schema migration script"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    migration_script = project_root / "src" / "incident_iq" / "database" / "migration" / "optimized_schema" / "run_migration.py"
    return migration_script


def get_default_db_path() -> Path:
    """Get default database path"""
    # Try to get from config
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from incident_iq.config import get_database_dir, get_database_name
        db_dir_name = get_database_dir()
        db_name = get_database_name()
        db_path = Path(__file__).parent.parent / db_dir_name / db_name
        return db_path
    except Exception:
        # Fallback to default
        return Path(__file__).parent.parent / "chroma_db" / "rag.db"


def run_migrations(db_path: str, skip_drop: bool = False, verbose: bool = False) -> Dict[str, Any]:
    """
    Run migrations from the optimized schema directory
    
    Args:
        db_path: Path to SQLite database
        skip_drop: Skip dropping old tables
        verbose: Enable verbose logging
        
    Returns:
        Dictionary with results
    """
    migration_dir = Path(__file__).parent.parent / "src" / "incident_iq" / "database" / "migration" / "optimized_schema"
    
    if not migration_dir.exists():
        return {
            "success": False,
            "error": f"Migration directory not found: {migration_dir}"
        }
    
    results = {
        "success": False,
        "migrations_run": [],
        "errors": [],
        "warnings": [],
        "database": str(db_path),
        "migration_dir": str(migration_dir)
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
        
        if not migration_files:
            results["warnings"].append("No SQL migration files found")
            results["success"] = True
            return results
        
        # Skip drop migration if requested
        if skip_drop and migration_files and migration_files[0] == '001_drop_old_tables.sql':
            if verbose:
                print("⚠️  Skipping table drop (skip_drop=True)")
            results["warnings"].append("Skipping table drop (skip_drop=True)")
            migration_files = migration_files[1:]
        
        print(f"\n{'='*70}")
        print(f"📦 Running {len(migration_files)} migrations")
        print(f"{'='*70}")
        print(f"Database: {db_path}")
        print(f"Migration Dir: {migration_dir}\n")
        
        # Execute migrations
        for migration_file in migration_files:
            migration_path = migration_dir / migration_file
            
            if verbose:
                print(f"▶️  Running: {migration_file}")
            else:
                print(f"▶️  {migration_file}...", end=" ", flush=True)
            
            try:
                # Read SQL file
                with open(migration_path, 'r') as f:
                    sql_content = f.read()
                
                # Split into individual statements
                statements = [
                    stmt.strip()
                    for stmt in sql_content.split(';')
                    if stmt.strip() and not stmt.strip().startswith('--')
                ]
                
                # Execute each statement
                for stmt in statements:
                    if stmt:
                        cursor.execute(stmt)
                
                conn.commit()
                results["migrations_run"].append(migration_file)
                
                if verbose:
                    print(f"✅ Complete\n")
                else:
                    print("✅")
                
            except sqlite3.Error as e:
                error_msg = f"{migration_file}: {str(e)}"
                results["errors"].append(error_msg)
                if verbose:
                    print(f"❌ Failed: {e}\n")
                else:
                    print(f"❌")
                conn.rollback()
                raise
        
        # Verify schema
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n{'='*70}")
        print("📊 Schema Summary")
        print(f"{'='*70}")
        print(f"Tables created: {len(tables)}")
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"  • {table} ({len(columns)} columns)")
        
        results["success"] = True
        results["final_tables"] = tables
        
        print(f"\n✅ Migration complete!")
        print(f"✅ All {len(migration_files)} migrations executed successfully\n")
        
    except Exception as e:
        results["errors"].append(str(e))
        print(f"\n❌ Migration failed: {e}\n")
    
    finally:
        if conn:
            conn.close()
    
    return results


def verify_schema(db_path: str) -> Dict[str, Any]:
    """
    Verify the schema is correctly implemented
    
    Args:
        db_path: Path to database
        
    Returns:
        Verification results
    """
    verification = {
        "valid": False,
        "tables": {},
        "relationships": [],
        "issues": []
    }
    
    try:
        if not os.path.exists(db_path):
            verification["issues"].append(f"Database not found: {db_path}")
            return verification
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Expected tables from optimized schema
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
                    "column_count": len(columns),
                    "columns": list(columns.keys())
                }
            else:
                verification["issues"].append(f"Missing table: {table}")
        
        # Check foreign keys
        for table in ['chunk_embedding_data', 'rag_history_and_optimization']:
            try:
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                fk_rows = cursor.fetchall()
                if fk_rows:
                    for fk in fk_rows:
                        verification["relationships"].append(
                            f"{table}.{fk[3]} → {fk[2]}.{fk[4]}"
                        )
            except:
                pass
        
        # Overall validation
        verification["valid"] = (
            len(expected_tables) == len(actual_tables) and
            len(verification["issues"]) == 0
        )
        
        conn.close()
        
    except Exception as e:
        verification["issues"].append(f"Verification error: {str(e)}")
    
    return verification


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run optimized schema migrations",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--skip-drop',
        action='store_true',
        help='Skip dropping old tables (use for fresh database)'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='Custom database path'
    )
    
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify schema, do not migrate'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Determine database path
    if args.db_path:
        db_path = args.db_path
    else:
        db_path = str(get_default_db_path())
    
    print(f"\n{'='*70}")
    print("🚀 Optimized Schema Migration Wrapper")
    print(f"{'='*70}")
    print(f"Database: {db_path}")
    print(f"Skip Drop: {args.skip_drop}")
    print(f"Verify Only: {args.verify_only}\n")
    
    # Verify if database exists
    db_path_obj = Path(db_path)
    if not db_path_obj.exists():
        print(f"⚠️  Database not found at: {db_path}")
        print("📝 Creating new database...")
        skip_drop = True
    else:
        skip_drop = args.skip_drop
    
    # If verify only, just verify
    if args.verify_only:
        print("🔍 Verifying schema...\n")
        verification = verify_schema(db_path)
        
        print(f"✅ Valid: {verification['valid']}")
        print(f"📊 Tables found: {len(verification['tables'])}")
        for table_name, info in verification['tables'].items():
            print(f"  • {table_name} ({info['column_count']} columns)")
        
        if verification['relationships']:
            print("\n🔗 Relationships:")
            for rel in verification['relationships']:
                print(f"  • {rel}")
        
        if verification['issues']:
            print("\n⚠️  Issues:")
            for issue in verification['issues']:
                print(f"  • {issue}")
        
        sys.exit(0 if verification['valid'] else 1)
    
    # Run migrations
    results = run_migrations(db_path, skip_drop=skip_drop, verbose=args.verbose)
    
    if not results['success']:
        print(f"\n❌ Migration failed!")
        for error in results['errors']:
            print(f"  ❌ {error}")
        sys.exit(1)
    
    # Verify after migration
    print("\n🔍 Verifying schema after migration...\n")
    verification = verify_schema(db_path)
    
    if verification['valid']:
        print(f"✅ Schema verification passed!")
        print(f"✅ Optimized schema successfully created!")
    else:
        print(f"⚠️  Schema verification issues:")
        for issue in verification['issues']:
            print(f"  • {issue}")
    
    print(f"\n{'='*70}")
    if results['success'] and verification['valid']:
        print("✅ MIGRATION COMPLETED SUCCESSFULLY")
    else:
        print("⚠️  MIGRATION COMPLETED WITH ISSUES")
    print(f"{'='*70}\n")
    
    sys.exit(0 if (results['success'] and verification['valid']) else 1)


if __name__ == "__main__":
    main()
