import sqlite3

conn = sqlite3.connect('chroma_db/rag.db')
cursor = conn.cursor()

# Check table structure
cursor.execute("PRAGMA table_info(rag_history_and_optimization)")
cols = cursor.fetchall()
print("[rag_history_and_optimization columns]")
for col in cols:
    print(f"  {col}")

# Check foreign keys
cursor.execute("PRAGMA foreign_key_list(rag_history_and_optimization)")
fks = cursor.fetchall()
print(f"\n[Foreign Keys: {len(fks)}]")
for fk in fks:
    print(f"  {fk}")

# Check what documents exist
cursor.execute("SELECT COUNT(*) FROM document_metadata")
doc_count = cursor.fetchone()[0]
print(f"\n[document_metadata rows: {doc_count}]")

if doc_count > 0:
    cursor.execute("SELECT doc_id FROM document_metadata LIMIT 1")
    doc_id = cursor.fetchone()[0]
    print(f"[Sample doc_id: {doc_id}]")
