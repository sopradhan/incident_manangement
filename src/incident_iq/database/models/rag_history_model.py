"""
RAGHistoryModel: Maps to optimized rag_history_and_optimization table
Unified historical log for queries, healing operations, and synthetic tests
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


class RAGHistoryModel:
    """Model for rag_history_and_optimization table in optimized schema"""
    
    def __init__(self, db_path: str = None):
        """
        Initialize with database connection
        
        Args:
            db_path: Path to SQLite database. If None, uses chroma_db/rag.db
        """
        if db_path is None:
            # Use optimized schema path: chroma_db/rag.db
            # File is at: src/incident_iq/database/models/rag_history_model.py
            # Go up 5 levels: models → database → incident_iq → src → PROJECT_ROOT
            project_root = Path(__file__).parent.parent.parent.parent.parent
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
    
    def log_query(self, query_text: str, target_doc_id: str, 
                  metrics_json: str, context_json: str = None,
                  agent_id: str = "langgraph_agent", user_id: str = None,
                  session_id: str = None) -> int:
        """
        Log a query event
        
        Args:
            query_text: The query text
            target_doc_id: Document ID being queried
            metrics_json: Metrics as JSON (frequency, accuracy, latency, etc.)
            context_json: Additional context as JSON
            agent_id: Agent ID
            user_id: User ID
            session_id: Session ID
            
        Returns:
            history_id of the created record, or -1 if failed
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                INSERT INTO rag_history_and_optimization
                (event_type, query_text, target_doc_id, metrics_json, 
                 context_json, timestamp, agent_id, user_id, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "QUERY",
                query_text,
                target_doc_id,
                metrics_json,
                context_json or json.dumps({}),
                datetime.now().isoformat(),
                agent_id,
                user_id,
                session_id
            ))
            
            self.conn.commit()
            return self.cursor.lastrowid
            
        except Exception as e:
            print(f"Error logging query: {e}")
            return -1
    
    def log_healing(self, target_doc_id: str, target_chunk_id: str,
                    metrics_json: str, context_json: str = None,
                    action_taken: str = None, reward_signal: float = None,
                    agent_id: str = "langgraph_agent", session_id: str = None) -> int:
        """
        Log a healing/optimization event
        
        Args:
            target_doc_id: Document ID being healed
            target_chunk_id: Chunk ID being healed
            metrics_json: Metrics as JSON
            context_json: Additional context
            action_taken: Action taken by RL agent
            reward_signal: Reward signal for RL
            agent_id: Agent ID
            session_id: Session ID
            
        Returns:
            history_id of the created record
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                INSERT INTO rag_history_and_optimization
                (event_type, target_doc_id, target_chunk_id, metrics_json,
                 context_json, action_taken, reward_signal, timestamp,
                 agent_id, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "HEAL",
                target_doc_id,
                target_chunk_id,
                metrics_json,
                context_json or json.dumps({}),
                action_taken,
                reward_signal,
                datetime.now().isoformat(),
                agent_id,
                session_id
            ))
            
            self.conn.commit()
            return self.cursor.lastrowid
            
        except Exception as e:
            print(f"Error logging healing: {e}")
            return -1
    
    def log_synthetic_test(self, query_text: str, target_doc_id: str,
                          metrics_json: str, context_json: str = None,
                          agent_id: str = "langgraph_agent", session_id: str = None) -> int:
        """
        Log a synthetic test event
        
        Args:
            query_text: Test query
            target_doc_id: Document ID being tested
            metrics_json: Test metrics
            context_json: Additional context
            agent_id: Agent ID
            session_id: Session ID
            
        Returns:
            history_id of the created record
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                INSERT INTO rag_history_and_optimization
                (event_type, query_text, target_doc_id, metrics_json,
                 context_json, timestamp, agent_id, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "SYNTHETIC_TEST",
                query_text,
                target_doc_id,
                metrics_json,
                context_json or json.dumps({}),
                datetime.now().isoformat(),
                agent_id,
                session_id
            ))
            
            self.conn.commit()
            return self.cursor.lastrowid
            
        except Exception as e:
            print(f"Error logging synthetic test: {e}")
            return -1
    
    def get_by_id(self, history_id: int) -> dict:
        """
        Get history record by ID
        
        Args:
            history_id: History record ID
            
        Returns:
            Dictionary with history data
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                SELECT history_id, event_type, timestamp, query_text, target_doc_id,
                       target_chunk_id, metrics_json, context_json, reward_signal,
                       action_taken, state_before, state_after, agent_id, user_id, session_id
                FROM rag_history_and_optimization
                WHERE history_id = ?
            """, (history_id,))
            
            row = self.cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None
            
        except Exception as e:
            print(f"Error getting history record: {e}")
            return None
    
    def get_by_event_type(self, event_type: str, limit: int = 100) -> List[Dict]:
        """
        Get history records by event type
        
        Args:
            event_type: Event type (QUERY, HEAL, SYNTHETIC_TEST)
            limit: Maximum records to return
            
        Returns:
            List of history dictionaries
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                SELECT history_id, event_type, timestamp, query_text, target_doc_id,
                       target_chunk_id, metrics_json, context_json, reward_signal,
                       action_taken, state_before, state_after, agent_id, user_id, session_id
                FROM rag_history_and_optimization
                WHERE event_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (event_type, limit))
            
            rows = self.cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            print(f"Error getting history by event type: {e}")
            return []
    
    def get_by_doc_id(self, doc_id: str, limit: int = 100) -> List[Dict]:
        """
        Get all history records for a document
        
        Args:
            doc_id: Document ID
            limit: Maximum records
            
        Returns:
            List of history dictionaries
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                SELECT history_id, event_type, timestamp, query_text, target_doc_id,
                       target_chunk_id, metrics_json, context_json, reward_signal,
                       action_taken, state_before, state_after, agent_id, user_id, session_id
                FROM rag_history_and_optimization
                WHERE target_doc_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (doc_id, limit))
            
            rows = self.cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            print(f"Error getting history by doc_id: {e}")
            return []
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """
        Get all history for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of history dictionaries
        """
        try:
            self._ensure_connection()
            
            self.cursor.execute("""
                SELECT history_id, event_type, timestamp, query_text, target_doc_id,
                       target_chunk_id, metrics_json, context_json, reward_signal,
                       action_taken, state_before, state_after, agent_id, user_id, session_id
                FROM rag_history_and_optimization
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            
            rows = self.cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            print(f"Error getting session history: {e}")
            return []
    
    def get_statistics(self, event_type: str = None) -> Dict[str, Any]:
        """
        Get statistics about history records
        
        Args:
            event_type: Optional event type filter
            
        Returns:
            Dictionary with statistics
        """
        try:
            self._ensure_connection()
            
            if event_type:
                self.cursor.execute("""
                    SELECT COUNT(*), event_type FROM rag_history_and_optimization
                    WHERE event_type = ?
                    GROUP BY event_type
                """, (event_type,))
            else:
                self.cursor.execute("""
                    SELECT COUNT(*), event_type FROM rag_history_and_optimization
                    GROUP BY event_type
                """)
            
            rows = self.cursor.fetchall()
            stats = {"total": 0}
            
            for row in rows:
                count, evt_type = row
                stats[evt_type] = count
                stats["total"] += count
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    @staticmethod
    def _row_to_dict(row) -> Dict:
        """Convert SQLite row to dictionary"""
        return {
            "history_id": row[0],
            "event_type": row[1],
            "timestamp": row[2],
            "query_text": row[3],
            "target_doc_id": row[4],
            "target_chunk_id": row[5],
            "metrics_json": row[6],
            "context_json": row[7],
            "reward_signal": row[8],
            "action_taken": row[9],
            "state_before": row[10],
            "state_after": row[11],
            "agent_id": row[12],
            "user_id": row[13],
            "session_id": row[14]
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
