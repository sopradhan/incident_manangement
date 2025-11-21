"""
Embedding Metadata Model - Tracks embedding and chunking information
"""
from typing import List, Dict, Any, Optional
from .base_model import BaseModel


class EmbeddingMetadataModel(BaseModel):
    """Model for embedding_metadata table"""
    
    table = 'embedding_metadata'
    fields = ['embedding_id', 'document_id', 'chunk_id', 'chunk_strategy', 'chunk_size',
              'overlap', 'embedding_model', 'embedding_version', 'quality_score',
              'last_modified', 'reindex_count', 'rbac_namespace', 'metadata_tags', 'healing_suggestions']
    
    def find_by_chunk_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Find metadata by chunk ID
        
        Args:
            chunk_id: Chunk identifier
            
        Returns:
            Metadata record or None
        """
        rows = self.raw_execute(
            "SELECT * FROM embedding_metadata WHERE chunk_id = ?",
            (chunk_id,)
        )
        return rows[0] if rows else None
    
    def find_by_document_id(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Find all metadata records for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of metadata records
        """
        return self.raw_execute(
            "SELECT * FROM embedding_metadata WHERE document_id = ?",
            (document_id,)
        )
    
    def insert_metadata(self, document_id: str, chunk_id: str,
                       chunk_strategy: str, chunk_size: int,
                       overlap: int, embedding_model: str,
                       embedding_version: str, quality_score: float = 0.5) -> int:
        """
        Insert embedding metadata (INSERT OR REPLACE to handle re-ingestion)
        
        Args:
            document_id: Document identifier
            chunk_id: Chunk identifier
            chunk_strategy: Strategy used for chunking
            chunk_size: Size of chunk
            overlap: Overlap between chunks
            embedding_model: Model used for embeddings
            embedding_version: Version of embedding
            quality_score: Initial quality score
            
        Returns:
            Last inserted row ID
        """
        cur = self.conn.execute("""
            INSERT OR REPLACE INTO embedding_metadata
            (document_id, chunk_id, chunk_strategy, chunk_size, overlap,
             embedding_model, embedding_version, quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document_id, chunk_id, chunk_strategy, chunk_size, overlap,
            embedding_model, embedding_version, quality_score
        ))
        self.conn.commit()
        return cur.lastrowid
    
    def update_quality_score(self, chunk_id: str, quality_score: float) -> None:
        """
        Update quality score for a chunk
        
        Args:
            chunk_id: Chunk identifier
            quality_score: New quality score
        """
        self.raw_execute(
            "UPDATE embedding_metadata SET quality_score = ?, last_modified = datetime('now') WHERE chunk_id = ?",
            (quality_score, chunk_id)
        )
    
    def get_low_quality_chunks(self, threshold: float = 0.5, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get chunks below quality threshold
        
        Args:
            threshold: Quality score threshold
            limit: Maximum results
            
        Returns:
            List of low-quality chunks
        """
        return self.raw_execute("""
            SELECT * FROM embedding_metadata
            WHERE quality_score < ?
            ORDER BY quality_score ASC
            LIMIT ?
        """, (threshold, limit))
    
    def count_chunks_by_document(self, document_id: str) -> int:
        """
        Count chunks for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            Number of chunks
        """
        rows = self.raw_execute(
            "SELECT COUNT(*) as count FROM embedding_metadata WHERE document_id = ?",
            (document_id,)
        )
        return rows[0]['count'] if rows else 0
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get statistics about embeddings
        
        Returns:
            Dictionary with embedding statistics
        """
        stats = {}
        
        # Total chunks
        result = self.raw_execute("SELECT COUNT(*) as count FROM embedding_metadata")
        stats['total_chunks'] = result[0]['count'] if result else 0
        
        # Average quality score
        result = self.raw_execute("SELECT AVG(quality_score) as avg_quality FROM embedding_metadata")
        stats['avg_quality_score'] = result[0]['avg_quality'] if result and result[0]['avg_quality'] else 0.0
        
        # Embedding models used
        result = self.raw_execute("SELECT DISTINCT embedding_model FROM embedding_metadata")
        stats['embedding_models'] = [row['embedding_model'] for row in result] if result else []
        
        # Chunk strategies used
        result = self.raw_execute("SELECT DISTINCT chunk_strategy FROM embedding_metadata")
        stats['chunk_strategies'] = [row['chunk_strategy'] for row in result] if result else []
        
        return stats
    
    def delete_by_document_id(self, document_id: str) -> None:
        """
        Delete all metadata for a document (when document is deleted)
        
        Args:
            document_id: Document identifier
        """
        self.conn.execute(
            "DELETE FROM embedding_metadata WHERE document_id = ?",
            (document_id,)
        )
        self.conn.commit()
    
    def get_low_quality_documents(self, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Get documents with average quality score below threshold
        
        Args:
            threshold: Quality score threshold
            
        Returns:
            List of low-quality documents with their stats
        """
        return self.raw_execute("""
            SELECT DISTINCT document_id, AVG(quality_score) as avg_quality, COUNT(*) as num_chunks
            FROM embedding_metadata
            GROUP BY document_id
            HAVING avg_quality < ?
            ORDER BY avg_quality ASC
            LIMIT 20
        """, (threshold,))
    
    def increment_reindex_count(self, document_id: str, new_strategy: str = None) -> None:
        """
        Increment reindex count for a document and optionally update chunk strategy
        
        Args:
            document_id: Document identifier
            new_strategy: Optional new chunking strategy
        """
        if new_strategy:
            self.raw_execute("""
                UPDATE embedding_metadata
                SET reindex_count = reindex_count + 1,
                    chunk_strategy = ?,
                    last_modified = datetime('now')
                WHERE document_id = ?
            """, (new_strategy, document_id))
        else:
            self.raw_execute("""
                UPDATE embedding_metadata
                SET reindex_count = reindex_count + 1,
                    last_modified = datetime('now')
                WHERE document_id = ?
            """, (document_id,))

