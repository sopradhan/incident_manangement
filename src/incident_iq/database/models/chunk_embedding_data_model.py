"""
ChunkEmbeddingDataModel: Maps to optimized chunk_embedding_data table
Tracks per-chunk embedding health, versioning, and quality for RL healing agent
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path


class ChunkEmbeddingDataModel:
    """Model for chunk_embedding_data table in optimized schema"""
    
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
    
    def create(self, chunk_id: str, doc_id: str, embedding_model: str,
               embedding_version: str = "1.0", quality_score: float = 0.8,
               reindex_count: int = 0, healing_suggestions: str = None) -> bool:
        """
        Create or update a chunk embedding record
        
        Args:
            chunk_id: Unique chunk identifier
            doc_id: Parent document ID
            embedding_model: Model used for embedding
            embedding_version: Version of embedding model
            quality_score: Quality score (0.0-1.0)
            reindex_count: Number of times reindexed
            healing_suggestions: Healing suggestions as JSON string
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                INSERT OR REPLACE INTO chunk_embedding_data
                (chunk_id, doc_id, embedding_model, embedding_version, 
                 quality_score, reindex_count, healing_suggestions, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk_id,
                doc_id,
                embedding_model,
                embedding_version,
                quality_score,
                reindex_count,
                healing_suggestions or json.dumps({}),
                datetime.now().isoformat()
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error creating chunk embedding data: {e}")
            return False
    
    def get_by_id(self, chunk_id: str) -> dict:
        """
        Get chunk embedding data by chunk_id
        
        Args:
            chunk_id: Chunk ID
            
        Returns:
            Dictionary with chunk data or None
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                SELECT chunk_id, doc_id, embedding_model, embedding_version,
                       quality_score, reindex_count, healing_suggestions, 
                       created_at, last_healed
                FROM chunk_embedding_data
                WHERE chunk_id = ?
            """, (chunk_id,))
            
            row = self.cursor.fetchone()
            if row:
                return {
                    "chunk_id": row[0],
                    "doc_id": row[1],
                    "embedding_model": row[2],
                    "embedding_version": row[3],
                    "quality_score": row[4],
                    "reindex_count": row[5],
                    "healing_suggestions": row[6],
                    "created_at": row[7],
                    "last_healed": row[8]
                }
            return None
            
        except Exception as e:
            print(f"Error getting chunk embedding data: {e}")
            return None
    
    def get_by_doc_id(self, doc_id: str) -> list:
        """
        Get all chunks for a specific document
        
        Args:
            doc_id: Document ID
            
        Returns:
            List of chunk data dictionaries
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                SELECT chunk_id, doc_id, embedding_model, embedding_version,
                       quality_score, reindex_count, healing_suggestions, 
                       created_at, last_healed
                FROM chunk_embedding_data
                WHERE doc_id = ?
                ORDER BY created_at ASC
            """, (doc_id,))
            
            rows = self.cursor.fetchall()
            results = []
            
            for row in rows:
                results.append({
                    "chunk_id": row[0],
                    "doc_id": row[1],
                    "embedding_model": row[2],
                    "embedding_version": row[3],
                    "quality_score": row[4],
                    "reindex_count": row[5],
                    "healing_suggestions": row[6],
                    "created_at": row[7],
                    "last_healed": row[8]
                })
            
            return results
            
        except Exception as e:
            print(f"Error getting chunks by doc_id: {e}")
            return []
    
    def get_low_quality_chunks(self, threshold: float = 0.6) -> list:
        """
        Get chunks with quality score below threshold
        
        Args:
            threshold: Quality threshold (default 0.6)
            
        Returns:
            List of low quality chunk data
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                SELECT chunk_id, doc_id, embedding_model, embedding_version,
                       quality_score, reindex_count, healing_suggestions, 
                       created_at, last_healed
                FROM chunk_embedding_data
                WHERE quality_score < ?
                ORDER BY quality_score ASC
            """, (threshold,))
            
            rows = self.cursor.fetchall()
            results = []
            
            for row in rows:
                results.append({
                    "chunk_id": row[0],
                    "doc_id": row[1],
                    "embedding_model": row[2],
                    "embedding_version": row[3],
                    "quality_score": row[4],
                    "reindex_count": row[5],
                    "healing_suggestions": row[6],
                    "created_at": row[7],
                    "last_healed": row[8]
                })
            
            return results
            
        except Exception as e:
            print(f"Error getting low quality chunks: {e}")
            return []
    
    def update_quality_score(self, chunk_id: str, quality_score: float) -> bool:
        """
        Update quality score for a chunk
        
        Args:
            chunk_id: Chunk ID
            quality_score: New quality score
            
        Returns:
            True if successful
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                UPDATE chunk_embedding_data
                SET quality_score = ?
                WHERE chunk_id = ?
            """, (quality_score, chunk_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating quality score: {e}")
            return False
    
    def increment_reindex_count(self, chunk_id: str) -> bool:
        """
        Increment reindex count for a chunk
        
        Args:
            chunk_id: Chunk ID
            
        Returns:
            True if successful
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                UPDATE chunk_embedding_data
                SET reindex_count = reindex_count + 1,
                    last_healed = ?
                WHERE chunk_id = ?
            """, (datetime.now().isoformat(), chunk_id))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Error incrementing reindex count: {e}")
            return False
    
    def get_statistics(self, doc_id: str = None) -> dict:
        """
        Get statistics for chunks
        
        Args:
            doc_id: Optional document ID to filter by
            
        Returns:
            Dictionary with statistics
        """
        try:
            self._ensure_connection()
            
            if doc_id:
                self.cursor.execute("""
                    SELECT COUNT(*), AVG(quality_score), MIN(quality_score), MAX(quality_score)
                    FROM chunk_embedding_data
                    WHERE doc_id = ?
                """, (doc_id,))
            else:
                self.cursor.execute("""
                    SELECT COUNT(*), AVG(quality_score), MIN(quality_score), MAX(quality_score)
                    FROM chunk_embedding_data
                """)
            
            row = self.cursor.fetchone()
            
            return {
                "total_chunks": row[0] or 0,
                "avg_quality": row[1] or 0.0,
                "min_quality": row[2] or 0.0,
                "max_quality": row[3] or 0.0
            }
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
