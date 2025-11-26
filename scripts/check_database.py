#!/usr/bin/env python3
"""
Database Inspector: Check tables and schema in the database
"""
import sys
import sqlite3
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def check_database(db_path: str = None):
    """Check database tables and schema"""
    
    if db_path is None:
        db_path = str(project_root / "chroma_db" / "rag.db")
    
    db_path_obj = Path(db_path)
    
    print("=" * 70)
    print("DATABASE INSPECTOR")
    print("=" * 70)
    print(f"\nDatabase Path: {db_path}")
    print(f"Database Exists: {db_path_obj.exists()}")
    
    if not db_path_obj.exists():
        print("\n❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"\n{'='*70}")
        print(f"📊 TABLES ({len(tables)})")
        print(f"{'='*70}\n")
        
        if not tables:
            print("❌ No tables found in database\n")
            conn.close()
            return True
        
        for table_name, in tables:
            # Skip SQLite internal tables
            if table_name.startswith('sqlite_'):
                continue
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fk_list = cursor.fetchall()
            
            print(f"📋 {table_name}")
            print(f"   Rows: {row_count}")
            print(f"   Columns: {len(columns)}")
            
            # Show columns
            print(f"   Columns:")
            for col_id, col_name, col_type, not_null, default, pk in columns:
                pk_str = " [PRIMARY KEY]" if pk else ""
                nn_str = " [NOT NULL]" if not_null else ""
                print(f"      - {col_name}: {col_type}{pk_str}{nn_str}")
            
            # Show foreign keys
            if fk_list:
                print(f"   Foreign Keys:")
                for fk_id, seq, table, from_col, to_col, on_delete, on_update, match in fk_list:
                    print(f"      - {from_col} → {table}.{to_col}")
            
            print()
        
        # Summary
        print(f"{'='*70}")
        print("📈 SUMMARY")
        print(f"{'='*70}")
        print(f"Total tables: {len([t for t in tables if not t[0].startswith('sqlite_')])}")
        
        # Check for expected optimized schema tables
        expected_tables = [
            'document_metadata',
            'chunk_embedding_data',
            'rag_history_and_optimization'
        ]
        
        actual_table_names = [t[0] for t in tables if not t[0].startswith('sqlite_')]
        found_tables = [t for t in expected_tables if t in actual_table_names]
        missing_tables = [t for t in expected_tables if t not in actual_table_names]
        
        print(f"\nExpected optimized schema tables: {len(expected_tables)}")
        print(f"Found: {len(found_tables)}")
        print(f"Missing: {len(missing_tables)}")
        
        if found_tables:
            print(f"\n✅ Found tables:")
            for t in found_tables:
                print(f"   - {t}")
        
        if missing_tables:
            print(f"\n❌ Missing tables:")
            for t in missing_tables:
                print(f"   - {t}")
        
        # Check for old tables (pre-optimized schema)
        old_tables = ['embedding_metadata', 'query_heatmap', 'healing_operations', 'synthetic_queries']
        old_found = [t for t in old_tables if t in actual_table_names]
        
        if old_found:
            print(f"\n⚠️  Found old schema tables (pre-optimization):")
            for t in old_found:
                print(f"   - {t}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check database tables and schema")
    parser.add_argument('--db-path', type=str, default=None, help='Path to database file')
    args = parser.parse_args()
    
    success = check_database(args.db_path)
    sys.exit(0 if success else 1)
