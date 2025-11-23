import os
import sys
from pathlib import Path

# Set environment variable FIRST
BASE_DIR = Path.cwd()
DB_PATH = str(BASE_DIR / 'src' / 'incident_iq' / 'database' / 'data' / 'incident_iq_direct.db')
os.environ['INCIDENT_IQ_DB_PATH'] = DB_PATH

print(f"Setting INCIDENT_IQ_DB_PATH={DB_PATH}")

from incident_iq.database.db.connection import get_connection, DB_PATH as IMPORTED_DB_PATH

print(f"Imported DB_PATH={IMPORTED_DB_PATH}")
print(f"Environment variable set to={os.environ['INCIDENT_IQ_DB_PATH']}")
print(f"Match: {str(IMPORTED_DB_PATH) == DB_PATH}")

conn = get_connection()
conn.execute('CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)')
conn.execute('INSERT INTO test (id) VALUES (1)')
conn.commit()
conn.close()

# Verify file exists
path = Path(str(IMPORTED_DB_PATH))
print(f"File exists: {path.exists()}")
print(f"File path: {path}")
if path.exists():
    print(f"File size: {path.stat().st_size} bytes")
