import os
import sqlite3
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "incident_iq_2.db")
DB_PATH = Path(__file__).resolve().parent.parent / "data" / DB_NAME

def get_connection():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


