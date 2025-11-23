"""
Document Metadata Model - Tracks document metadata for RAG ingestion
"""
from typing import List, Dict, Any, Optional
import json
from .base_model import BaseModel


class DocumentMetadataModel(BaseModel):
    """Model for document_metadata table"""
    
    table = 'document_metadata'
    fields = ['metadata_id', 'doc_id', 'key', 'value']
    
    def store_metadata(self, doc_id: str, key: str, value: str) -> int:
        """
        Store document metadata
        
        Args:
            doc_id: Document identifier
            key: Metadata key
            value: Metadata value
            
        Returns:
            Last inserted row ID
        """
        return self.insert({
            'doc_id': doc_id,
            'key': key,
            'value': value
        })
    
    def get_metadata(self, document_id: str, key: str) -> Optional[str]:
        """
        Retrieve metadata value for a document
        
        Args:
            document_id: Document identifier
            key: Metadata key
            
        Returns:
            Metadata value or None
        """
        rows = self.raw_execute("""
            SELECT value FROM document_metadata
            WHERE doc_id = ? AND key = ?
            LIMIT 1
        """, (document_id, key))
        
        return rows[0]['value'] if rows else None
    
    def get_all_metadata(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all metadata for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of metadata records
        """
        return self.raw_execute("""
            SELECT * FROM document_metadata
            WHERE doc_id = ?
        """, (document_id,))
    
    def get_metadata_by_type(self, document_id: str, metadata_type: str) -> List[Dict[str, Any]]:
        """
        Get metadata records by type for a document
        
        Args:
            document_id: Document identifier
            metadata_type: Type of metadata to filter
            
        Returns:
            List of metadata records
        """
        # Note: This table doesn't have a metadata_type column in current schema
        # This method kept for API compatibility
        return self.get_all_metadata(document_id)
    
    def update_metadata(self, document_id: str, key: str, value: str) -> None:
        """
        Update metadata value for a document
        
        Args:
            document_id: Document identifier
            key: Metadata key
            value: New metadata value
        """
        self.raw_execute("""
            UPDATE document_metadata
            SET value = ?
            WHERE doc_id = ? AND key = ?
        """, (value, document_id, key))
    
    def delete_metadata(self, document_id: str, key: str) -> None:
        """
        Delete metadata for a document
        
        Args:
            document_id: Document identifier
            key: Metadata key to delete
        """
        self.conn.execute(
            "DELETE FROM document_metadata WHERE doc_id = ? AND key = ?",
            (document_id, key)
        )
        self.conn.commit()
    
    def delete_all_metadata(self, document_id: str) -> None:
        """
        Delete all metadata for a document (when document is deleted)
        
        Args:
            document_id: Document identifier
        """
        self.conn.execute(
            "DELETE FROM document_metadata WHERE doc_id = ?",
            (document_id,)
        )
        self.conn.commit()
    
    def get_metadata_summary(self, document_id: str) -> Dict[str, Any]:
        """
        Get summary of all metadata for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            Dictionary mapping keys to values
        """
        rows = self.get_all_metadata(document_id)
        return {row['key']: row['value'] for row in rows}
    
    def batch_store_metadata(self, document_id: str, metadata_dict: Dict[str, str]) -> List[int]:
        """
        Store multiple metadata items for a document
        
        Args:
            document_id: Document identifier
            metadata_dict: Dictionary of key-value pairs
            
        Returns:
            List of inserted row IDs
        """
        ids = []
        for key, value in metadata_dict.items():
            row_id = self.store_metadata(document_id, key, value)
            ids.append(row_id)
        return ids
    
    def get_documents_with_metadata_key(self, key: str) -> List[Dict[str, Any]]:
        """
        Get all documents that have a specific metadata key
        
        Args:
            key: Metadata key to search for
            
        Returns:
            List of unique document IDs with this metadata
        """
        return self.raw_execute("""
            SELECT DISTINCT doc_id FROM document_metadata
            WHERE key = ?
            ORDER BY doc_id
        """, (key,))
