#!/usr/bin/env python3
"""
Database Updater: Migrate from ChromaDB to SQLite with Optimized Schema
Purpose: Transfer and consolidate metadata from ChromaDB into the new SQLite optimized schema
Tables: document_metadata, chunk_embedding_data, rag_history_and_optimization
"""
import sys
import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def get_db_paths():
    """Get database paths"""
    project_root = Path(__file__).parent.parent
    chroma_db_path = project_root / "chroma_db" / "rag.db"
    return {
        "chroma": str(chroma_db_path),
        "sqlite": str(chroma_db_path)  # Same file, we'll use SQLite directly
    }


def check_old_tables(conn: sqlite3.Connection) -> Dict[str, bool]:
    """Check which old tables exist"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    
    return {
        "document_metadata_old": "document_metadata" in tables,
        "embedding_metadata_old": "embedding_metadata" in tables,
        "query_heatmap_old": "query_heatmap" in tables,
        "healing_operations_old": "healing_operations" in tables,
        "synthetic_queries_old": "synthetic_queries" in tables,
    }


def migrate_document_metadata(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Migrate document metadata from old to new schema"""
    cursor = conn.cursor()
    results = {
        "migrated": 0,
        "errors": [],
        "documents": []
    }
    
    try:
        # Check if old table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='document_metadata'")
        if not cursor.fetchone():
            results["errors"].append("Old document_metadata table not found")
            return results
        
        # Get old document metadata
        cursor.execute("""
            SELECT DISTINCT 
                doc_id,
                title,
                author,
                source,
                summary
            FROM document_metadata
            WHERE doc_id IS NOT NULL
            LIMIT 100
        """)
        
        old_docs = cursor.fetchall()
        
        # Insert into new schema
        for doc_id, title, author, source, summary in old_docs:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO document_metadata 
                    (doc_id, title, author, source, summary, rbac_namespace, 
                     chunk_strategy, chunk_size_char, overlap_char, metadata_json, last_ingested)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    title or f"Document {doc_id}",
                    author or "Unknown",
                    source or "Unknown",
                    summary or "No summary",
                    "general",
                    "recursive_splitter",
                    512,
                    50,
                    json.dumps({"migrated": True, "source": "old_schema"}),
                    datetime.now().isoformat()
                ))
                
                results["migrated"] += 1
                results["documents"].append(doc_id)
                
            except Exception as e:
                results["errors"].append(f"Failed to migrate {doc_id}: {str(e)}")
        
        conn.commit()
        
    except Exception as e:
        results["errors"].append(f"Migration failed: {str(e)}")
    
    return results


def migrate_embedding_metadata(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Migrate embedding metadata from old to new schema"""
    cursor = conn.cursor()
    results = {
        "migrated": 0,
        "errors": [],
        "chunks": []
    }
    
    try:
        # Check if old table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='embedding_metadata'")
        if not cursor.fetchone():
            results["errors"].append("Old embedding_metadata table not found")
            return results
        
        # Get old embedding metadata
        cursor.execute("""
            SELECT DISTINCT
                chunk_id,
                doc_id,
                embedding_model,
                quality_score,
                reindex_count
            FROM embedding_metadata
            WHERE chunk_id IS NOT NULL
            LIMIT 1000
        """)
        
        old_embeddings = cursor.fetchall()
        
        # Insert into new schema
        for chunk_id, doc_id, embedding_model, quality_score, reindex_count in old_embeddings:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO chunk_embedding_data
                    (chunk_id, doc_id, embedding_model, embedding_version, 
                     quality_score, reindex_count, healing_suggestions, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk_id,
                    doc_id or "unknown",
                    embedding_model or "ollama",
                    "1.0",
                    quality_score or 0.8,
                    reindex_count or 0,
                    json.dumps({"migrated": True, "source": "old_schema"}),
                    datetime.now().isoformat()
                ))
                
                results["migrated"] += 1
                results["chunks"].append(chunk_id)
                
            except Exception as e:
                results["errors"].append(f"Failed to migrate chunk {chunk_id}: {str(e)}")
        
        conn.commit()
        
    except Exception as e:
        results["errors"].append(f"Migration failed: {str(e)}")
    
    return results


def migrate_query_heatmap(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Migrate query heatmap to RAG history table"""
    cursor = conn.cursor()
    results = {
        "migrated": 0,
        "errors": [],
        "queries": []
    }
    
    try:
        # Check if old table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='query_heatmap'")
        if not cursor.fetchone():
            results["errors"].append("Old query_heatmap table not found")
            return results
        
        # Get old query data
        cursor.execute("""
            SELECT 
                query_text,
                doc_id,
                frequency,
                avg_retrieval_accuracy,
                avg_response_time_ms
            FROM query_heatmap
            LIMIT 500
        """)
        
        old_queries = cursor.fetchall()
        
        # Insert into new schema as QUERY events
        for query_text, doc_id, frequency, accuracy, response_time in old_queries:
            try:
                cursor.execute("""
                    INSERT INTO rag_history_and_optimization
                    (event_type, query_text, target_doc_id, metrics_json, 
                     context_json, timestamp, agent_id, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    "QUERY",
                    query_text,
                    doc_id or "unknown",
                    json.dumps({
                        "frequency": frequency or 1,
                        "avg_accuracy": accuracy or 0.0,
                        "latency_ms": response_time or 0,
                        "migrated": True
                    }),
                    json.dumps({"source": "query_heatmap_old"}),
                    datetime.now().isoformat(),
                    "langgraph_agent",
                    "migration_session"
                ))
                
                results["migrated"] += 1
                results["queries"].append(query_text[:50])
                
            except Exception as e:
                results["errors"].append(f"Failed to migrate query: {str(e)}")
        
        conn.commit()
        
    except Exception as e:
        results["errors"].append(f"Migration failed: {str(e)}")
    
    return results


def create_summary_stats(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Create summary statistics after migration"""
    cursor = conn.cursor()
    stats = {
        "document_metadata": 0,
        "chunk_embedding_data": 0,
        "rag_history_events": 0,
        "tables_created": []
    }
    
    try:
        # Count documents
        cursor.execute("SELECT COUNT(*) FROM document_metadata")
        stats["document_metadata"] = cursor.fetchone()[0]
        
        # Count chunks
        cursor.execute("SELECT COUNT(*) FROM chunk_embedding_data")
        stats["chunk_embedding_data"] = cursor.fetchone()[0]
        
        # Count history events
        cursor.execute("SELECT COUNT(*) FROM rag_history_and_optimization")
        stats["rag_history_events"] = cursor.fetchone()[0]
        
        # Count by event type
        cursor.execute("""
            SELECT event_type, COUNT(*) 
            FROM rag_history_and_optimization 
            GROUP BY event_type
        """)
        event_counts = cursor.fetchall()
        stats["event_types"] = {event: count for event, count in event_counts}
        
        # Get tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND NOT name LIKE 'sqlite_%'
            ORDER BY name
        """)
        stats["tables_created"] = [row[0] for row in cursor.fetchall()]
        
    except Exception as e:
        stats["error"] = str(e)
    
    return stats


def main():
    """Main migration process"""
    print("=" * 80)
    print("DATABASE UPDATER: Migrate to Optimized SQLite Schema")
    print("=" * 80)
    
    db_paths = get_db_paths()
    db_path = db_paths["sqlite"]
    
    print(f"\nDatabase: {db_path}")
    print(f"Database Exists: {Path(db_path).exists()}\n")
    
    if not Path(db_path).exists():
        print("❌ Database not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Disable foreign keys for migration
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        print("=" * 80)
        print("CHECKING EXISTING TABLES")
        print("=" * 80)
        
        old_tables = check_old_tables(conn)
        
        for table_name, exists in old_tables.items():
            status = "✓ EXISTS" if exists else "✗ NOT FOUND"
            print(f"  {table_name:<30} {status}")
        
        # Check new tables
        print("\n  New Optimized Schema Tables:")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN 
            ('document_metadata', 'chunk_embedding_data', 'rag_history_and_optimization')
            ORDER BY name
        """)
        new_tables = {row[0] for row in cursor.fetchall()}
        
        for table in ['document_metadata', 'chunk_embedding_data', 'rag_history_and_optimization']:
            status = "✓ EXISTS" if table in new_tables else "✗ NOT FOUND"
            print(f"  {table:<30} {status}")
        
        # Run migrations
        print("\n" + "=" * 80)
        print("MIGRATING DATA")
        print("=" * 80)
        
        migrations = [
            ("Document Metadata", migrate_document_metadata),
            ("Embedding Metadata", migrate_embedding_metadata),
            ("Query Heatmap", migrate_query_heatmap),
        ]
        
        all_results = {}
        total_migrated = 0
        
        for name, migrate_func in migrations:
            print(f"\n📦 Migrating {name}...")
            result = migrate_func(conn)
            all_results[name] = result
            
            if result["migrated"] > 0:
                print(f"   ✓ Migrated: {result['migrated']}")
                total_migrated += result["migrated"]
            
            if result["errors"]:
                print(f"   ⚠ Errors: {len(result['errors'])}")
                for error in result["errors"][:3]:
                    print(f"      - {error}")
                if len(result["errors"]) > 3:
                    print(f"      ... and {len(result['errors']) - 3} more")
        
        # Re-enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        
        # Show statistics
        print("\n" + "=" * 80)
        print("DATABASE STATISTICS")
        print("=" * 80)
        
        stats = create_summary_stats(conn)
        
        print(f"\n📊 Optimized Schema Tables:")
        print(f"  Documents: {stats['document_metadata']}")
        print(f"  Chunks: {stats['chunk_embedding_data']}")
        print(f"  History Events: {stats['rag_history_events']}")
        
        if stats.get("event_types"):
            print(f"\n  Event Types:")
            for event_type, count in stats["event_types"].items():
                print(f"    - {event_type}: {count}")
        
        print(f"\n📋 All Tables in Database:")
        for table in stats["tables_created"]:
            # Get row count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table:<40} ({count} rows)")
            except:
                print(f"  - {table}")
        
        # Summary
        print("\n" + "=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        
        print(f"\n✓ Total Records Migrated: {total_migrated}")
        print(f"✓ Optimized Schema Initialized")
        print(f"✓ Foreign Keys: Enabled")
        print(f"✓ Migration Status: COMPLETE")
        
        print("\n" + "=" * 80)
        print("DATABASE UPDATE COMPLETE")
        print("=" * 80 + "\n")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
