import os
import sqlite3
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "incident_iq.db")

def get_db_path():
    """Get database path, checking environment variable first"""
    if "INCIDENT_IQ_DB_PATH" in os.environ:
        return Path(os.environ["INCIDENT_IQ_DB_PATH"])
    else:
        return Path(__file__).resolve().parent.parent / "data" / DB_NAME

def get_connection():
    db_path = get_db_path()
    os.makedirs(db_path.parent, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# For backwards compatibility, also create module-level DB_PATH
DB_PATH = Path(__file__).resolve().parent.parent / "data" / DB_NAME


