"""
Base Model - Foundation for all table-specific model classes
Provides core CRUD operations (Create, Read, Update, Delete)
"""
from typing import List, Dict, Any, Optional, Tuple
import sqlite3


class BaseModel:
    """
    Base model class providing CRUD operations for database tables.
    Subclasses should set the 'table' and 'fields' class attributes.
    """
    
    table: str = ''
    fields: List[str] = []
    
    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize model with database connection
        
        Args:
            conn: sqlite3 connection with row_factory set to sqlite3.Row
        """
        self.conn = conn
    
    def all(self) -> List[Dict[str, Any]]:
        """
        Fetch all records from table
        
        Returns:
            List of dictionaries representing all rows
        """
        cur = self.conn.execute(f"SELECT * FROM {self.table}")
        return [dict(row) for row in cur.fetchall()]
    
    def find(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Find a single record by ID
        
        Args:
            record_id: Primary key value
            
        Returns:
            Dictionary of row data or None if not found
        """
        cur = self.conn.execute(f"SELECT * FROM {self.table} WHERE id = ?", (record_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    
    def insert(self, payload: Dict[str, Any]) -> int:
        """
        Insert a new record
        
        Args:
            payload: Dictionary of column names to values
            
        Returns:
            Last inserted row ID
        """
        keys = ','.join(payload.keys())
        placeholders = ','.join('?' for _ in payload)
        values = tuple(payload.values())
        cur = self.conn.execute(
            f"INSERT INTO {self.table} ({keys}) VALUES ({placeholders})",
            values
        )
        self.conn.commit()
        return cur.lastrowid
    
    def update(self, record_id: int, payload: Dict[str, Any]) -> None:
        """
        Update an existing record
        
        Args:
            record_id: Primary key value
            payload: Dictionary of columns to update
        """
        if not payload:
            return
        
        assignments = ','.join([f"{k} = ?" for k in payload.keys()])
        values = tuple(payload.values()) + (record_id,)
        self.conn.execute(
            f"UPDATE {self.table} SET {assignments}, updated_at = datetime('now') WHERE id = ?",
            values
        )
        self.conn.commit()
    
    def delete(self, record_id: int) -> None:
        """
        Delete a record
        
        Args:
            record_id: Primary key value
        """
        self.conn.execute(f"DELETE FROM {self.table} WHERE id = ?", (record_id,))
        self.conn.commit()
    
    def raw_execute(self, query_string: str, query_values: Tuple = ()) -> Any:
        """
        Execute raw SQL query
        
        Args:
            query_string: SQL query string
            query_values: Query parameter values
            
        Returns:
            For SELECT: list of all rows
            For INSERT/UPDATE/DELETE: None
        """
        cur = self.conn.execute(query_string, query_values)
        if query_string.strip().upper().startswith("SELECT"):
            return [dict(row) for row in cur.fetchall()]
        else:
            self.conn.commit()
            return None
    
    def count(self) -> int:
        """
        Count total records in table
        
        Returns:
            Total number of records
        """
        cur = self.conn.execute(f"SELECT COUNT(*) as count FROM {self.table}")
        row = cur.fetchone()
        return row['count'] if row else 0
    
    def exists(self, record_id: int) -> bool:
        """
        Check if record exists
        
        Args:
            record_id: Primary key value
            
        Returns:
            True if record exists, False otherwise
        """
        return self.find(record_id) is not None
