"""
Database Utility
Simple helper for database path and connection management
All actual database operations go through models in core/database/models/
"""
import sqlite3
from pathlib import Path


class DatabaseUtil:
    """Minimal database utility - models handle all operations"""
    
    def __init__(self, db_path: str):
        """
        Initialize database utility
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        print(f"[DatabaseUtil] Using database: {db_path}")
    
    def get_connection(self):
        """Get SQLite connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
