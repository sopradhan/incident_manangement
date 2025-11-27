import sqlite3

db_path = 'chroma_db/rag.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print(f"\nDatabase: {db_path}")
print("="*60)
print(f"Total tables: {len(tables)}\n")

for table_name in tables:
    table = table_name[0]
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    row_count = cursor.fetchone()[0]
    
    print(f"Table: {table}")
    print(f"  Rows: {row_count}")
    print(f"  Columns: {len(columns)}")
    for col in columns:
        print(f"    - {col[1]} ({col[2]})")
    print()

conn.close()
