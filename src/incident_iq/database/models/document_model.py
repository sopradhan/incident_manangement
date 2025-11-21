"""
Document Model - Handles all document table operations
"""
from typing import List, Dict, Any, Optional
from .base_model import BaseModel


class DocumentModel(BaseModel):
    """Model for documents table"""
    
    table = 'documents'
    fields = ['id', 'title', 'source', 'content', 'doc_type', 'created_at', 'updated_at']
    
    def find_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Find document by document ID (not primary key)
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Document record or None
        """
        rows = self.raw_execute(
            "SELECT * FROM documents WHERE id = ?",
            (doc_id,)
        )
        return rows[0] if rows else None
    
    def exists_by_id(self, doc_id: str) -> bool:
        """
        Check if document exists by doc_id
        
        Args:
            doc_id: Document identifier
            
        Returns:
            True if document exists
        """
        return self.find_by_id(doc_id) is not None
    
    def find_by_source(self, source: str) -> List[Dict[str, Any]]:
        """
        Find all documents from a specific source
        
        Args:
            source: Source path or identifier
            
        Returns:
            List of documents from source
        """
        return self.raw_execute(
            "SELECT * FROM documents WHERE source = ?",
            (source,)
        )
    
    def get_by_title_prefix(self, prefix: str) -> List[Dict[str, Any]]:
        """
        Find documents by title prefix (for search)
        
        Args:
            prefix: Title prefix to search for
            
        Returns:
            List of matching documents
        """
        return self.raw_execute(
            "SELECT * FROM documents WHERE title LIKE ? ORDER BY updated_at DESC",
            (f"{prefix}%",)
        )
    
    def get_recent_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently created/updated documents
        
        Args:
            limit: Number of documents to return
            
        Returns:
            List of recent documents
        """
        return self.raw_execute(
            "SELECT * FROM documents ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
    
    def count_by_source(self, source: str) -> int:
        """
        Count documents from a specific source
        
        Args:
            source: Source identifier
            
        Returns:
            Number of documents from source
        """
        rows = self.raw_execute(
            "SELECT COUNT(*) as count FROM documents WHERE source = ?",
            (source,)
        )
        return rows[0]['count'] if rows else 0
    
    def get_content_by_id(self, doc_id: str) -> Optional[str]:
        """
        Get document content by ID
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Document content or None
        """
        rows = self.raw_execute(
            "SELECT content FROM documents WHERE id = ?",
            (doc_id,)
        )
        return rows[0]['content'] if rows else None
