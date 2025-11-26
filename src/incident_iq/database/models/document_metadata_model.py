"""
DocumentMetadataModel: Maps to optimized document_metadata table
Stores document-level metadata with chunking strategy and RBAC namespace
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path


class DocumentMetadataModel:
    """Model for document_metadata table in optimized schema"""
    
    def __init__(self, db_path: str = None):
        """
        Initialize with database connection
        
        Args:
            db_path: Path to SQLite database. If None, uses config-based default
        """
        if db_path is None:
            # Use config-based path: chroma_db/rag.db
            try:
                from ..config import get_database_dir, get_database_name
                db_dir_name = get_database_dir()
                db_name = get_database_name()
                project_root = Path(__file__).parent.parent.parent.parent
                db_path = str(project_root / db_dir_name / db_name)
            except Exception:
                # Fallback to default chroma_db/rag.db
                project_root = Path(__file__).parent.parent.parent.parent
                db_path = str(project_root / "chroma_db" / "rag.db")
        
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
    
    def _connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
    
    def _ensure_connection(self):
        """Ensure connection is still active"""
        try:
            self.cursor.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            self._connect()
    
    def create(self, doc_id: str, title: str, author: str = None, 
               source: str = None, summary: str = None, 
               rbac_namespace: str = "general",
               chunk_strategy: str = "recursive_splitter",
               chunk_size_char: int = 512, overlap_char: int = 50,
               metadata_json: str = None) -> bool:
        """
        Create or update a document metadata record
        
        Args:
            doc_id: Unique document identifier
            title: Document title
            author: Document author
            source: Document source/path
            summary: Document summary
            rbac_namespace: RBAC namespace for access control
            chunk_strategy: Chunking strategy used
            chunk_size_char: Chunk size in characters
            overlap_char: Overlap between chunks
            metadata_json: Additional metadata as JSON string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO document_metadata
                (doc_id, title, author, source, summary, rbac_namespace,
                 chunk_strategy, chunk_size_char, overlap_char, metadata_json, last_ingested)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                title,
                author or "Unknown",
                source or "Unknown",
                summary or "",
                rbac_namespace,
                chunk_strategy,
                chunk_size_char,
                overlap_char,
                metadata_json or json.dumps({}),
                datetime.now().isoformat()
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error creating document metadata: {e}")
            return False
    
    def get_by_id(self, doc_id: str) -> dict:
        """
        Get document metadata by doc_id
        
        Args:
            doc_id: Document ID
            
        Returns:
            Dictionary with document metadata or None
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                SELECT doc_id, title, author, source, summary, rbac_namespace,
                       chunk_strategy, chunk_size_char, overlap_char, metadata_json, last_ingested
                FROM document_metadata
                WHERE doc_id = ?
            """, (doc_id,))
            
            row = self.cursor.fetchone()
            if row:
                return {
                    "doc_id": row[0],
                    "title": row[1],
                    "author": row[2],
                    "source": row[3],
                    "summary": row[4],
                    "rbac_namespace": row[5],
                    "chunk_strategy": row[6],
                    "chunk_size_char": row[7],
                    "overlap_char": row[8],
                    "metadata_json": row[9],
                    "last_ingested": row[10]
                }
            return None
            
        except Exception as e:
            print(f"Error getting document metadata: {e}")
            return None
    
    def get_all(self) -> list:
        """
        Get all document metadata records
        
        Returns:
            List of document metadata dictionaries
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                SELECT doc_id, title, author, source, summary, rbac_namespace,
                       chunk_strategy, chunk_size_char, overlap_char, metadata_json, last_ingested
                FROM document_metadata
                ORDER BY last_ingested DESC
            """)
            
            rows = self.cursor.fetchall()
            results = []
            
            for row in rows:
                results.append({
                    "doc_id": row[0],
                    "title": row[1],
                    "author": row[2],
                    "source": row[3],
                    "summary": row[4],
                    "rbac_namespace": row[5],
                    "chunk_strategy": row[6],
                    "chunk_size_char": row[7],
                    "overlap_char": row[8],
                    "metadata_json": row[9],
                    "last_ingested": row[10]
                })
            
            return results
            
        except Exception as e:
            print(f"Error getting all document metadata: {e}")
            return []
    
    def get_by_namespace(self, rbac_namespace: str) -> list:
        """
        Get all documents in a specific RBAC namespace
        
        Args:
            rbac_namespace: RBAC namespace
            
        Returns:
            List of document metadata dictionaries
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                SELECT doc_id, title, author, source, summary, rbac_namespace,
                       chunk_strategy, chunk_size_char, overlap_char, metadata_json, last_ingested
                FROM document_metadata
                WHERE rbac_namespace = ?
                ORDER BY last_ingested DESC
            """, (rbac_namespace,))
            
            rows = self.cursor.fetchall()
            results = []
            
            for row in rows:
                results.append({
                    "doc_id": row[0],
                    "title": row[1],
                    "author": row[2],
                    "source": row[3],
                    "summary": row[4],
                    "rbac_namespace": row[5],
                    "chunk_strategy": row[6],
                    "chunk_size_char": row[7],
                    "overlap_char": row[8],
                    "metadata_json": row[9],
                    "last_ingested": row[10]
                })
            
            return results
            
        except Exception as e:
            print(f"Error getting documents by namespace: {e}")
            return []
    
    def update_last_ingested(self, doc_id: str) -> bool:
        """
        Update the last_ingested timestamp
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                UPDATE document_metadata
                SET last_ingested = ?
                WHERE doc_id = ?
            """, (datetime.now().isoformat(), doc_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating last_ingested: {e}")
            return False
    
    def delete(self, doc_id: str) -> bool:
        """
        Delete a document and its related chunks (cascading delete)
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if successful
        """
        try:
            self._ensure_connection()
            
            # Cascading delete is handled by foreign key ON DELETE CASCADE
            self.cursor.execute("""
                DELETE FROM document_metadata
                WHERE doc_id = ?
            """, (doc_id,))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    def count(self) -> int:
        """
        Get total number of documents
        
        Returns:
            Document count
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("SELECT COUNT(*) FROM document_metadata")
            return self.cursor.fetchone()[0]
            
        except Exception as e:
            print(f"Error counting documents: {e}")
            return 0
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
