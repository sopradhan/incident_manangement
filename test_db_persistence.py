import sqlite3
from pathlib import Path

db_path = Path('src/incident_iq/database/data/incident_iq.db')
db_path.parent.mkdir(parents=True, exist_ok=True)

print(f'Creating database at: {db_path}')
conn = sqlite3.connect(str(db_path))
conn.execute('CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)')
conn.execute('INSERT INTO test_table (name) VALUES ("test")')
conn.commit()
conn.close()

print(f'File exists: {db_path.exists()}')
file_size = db_path.stat().st_size if db_path.exists() else 0
print(f'File size: {file_size} bytes')

# Read it back
conn = sqlite3.connect(str(db_path))
cursor = conn.execute('SELECT * FROM test_table')
data = cursor.fetchall()
print(f'Data: {data}')
conn.close()
