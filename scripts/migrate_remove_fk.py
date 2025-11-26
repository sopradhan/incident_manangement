#!/usr/bin/env python
"""
Migration: Remove foreign key constraint from rag_history_and_optimization
to allow logging queries for any document ID, even if not in document_metadata
"""

import sqlite3
from pathlib import Path

db_path = "chroma_db/rag.db"

print("[Migration] Removing foreign key constraint from rag_history_and_optimization")
print(f"Database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Step 1: Disable foreign keys temporarily
    cursor.execute("PRAGMA foreign_keys = OFF")
    
    # Step 2: Rename old table
    cursor.execute("ALTER TABLE rag_history_and_optimization RENAME TO rag_history_and_optimization_old")
    
    # Step 3: Create new table WITHOUT foreign key constraint
    cursor.execute("""
        CREATE TABLE rag_history_and_optimization (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            query_text TEXT,
            target_doc_id TEXT,
            target_chunk_id TEXT,
            metrics_json TEXT NOT NULL,
            context_json TEXT,
            reward_signal FLOAT,
            action_taken TEXT,
            state_before TEXT,
            state_after TEXT,
            agent_id TEXT DEFAULT 'langgraph_agent',
            user_id TEXT,
            session_id TEXT
        )
    """)
    
    # Step 4: Copy data from old table
    cursor.execute("""
        INSERT INTO rag_history_and_optimization
        SELECT * FROM rag_history_and_optimization_old
    """)
    
    # Step 5: Drop old table
    cursor.execute("DROP TABLE rag_history_and_optimization_old")
    
    # Step 6: Re-enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    conn.commit()
    print("[✓] Migration completed successfully")
    
    # Verify
    cursor.execute("PRAGMA foreign_key_list(rag_history_and_optimization)")
    fks = cursor.fetchall()
    print(f"[✓] Foreign keys after migration: {len(fks)}")
    
    cursor.execute("SELECT COUNT(*) FROM rag_history_and_optimization")
    count = cursor.fetchone()[0]
    print(f"[✓] Rows preserved: {count}")
    
except Exception as e:
    print(f"[✗] Migration failed: {e}")
    conn.rollback()
    import traceback
    traceback.print_exc()

finally:
    conn.close()
