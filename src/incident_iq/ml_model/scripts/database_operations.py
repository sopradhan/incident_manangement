"""
Database operations layer for incident management system.
Handles all SQLite interactions with proper error handling and logging.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseOperations:
    """Centralized database operations for incident management."""
    
    def __init__(self, db_path: str):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._validate_db_path()
        # self._initialize_schema()
    
    def _validate_db_path(self) -> None:
        """Validate database file exists."""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        logger.info(f"Connected to database: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get database connection with WAL mode enabled.
        
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn
            
    def load_severity_rules(self) -> List[Tuple]:
        """
        Load all severity rules from database.
        
        Returns:
            List of tuples (pattern, severity_level, base_score, category, description, environment)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pattern, severity_level, base_score, category, description, environment
                FROM severity_rules
            """)
            rules = cursor.fetchall()
        
        logger.info(f"Loaded {len(rules)} severity rules")
        return rules
    
    def get_unprocessed_incidents(self, limit: Optional[int] = None) -> List[Tuple]:
        """
        Fetch unprocessed incident logs.
        
        Args:
            limit: Maximum number of records to fetch
            
        Returns:
            List of tuples (id, incident_json, source_type)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                    SELECT payload_id, payload, source_type 
                    FROM incident_logs 
                    WHERE status = 'new'
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            incidents = cursor.fetchall()
        
        logger.info(f"Fetched {len(incidents)} unprocessed incidents")
        return incidents
    
    def insert_severity_mapping(self, mapping_data: Dict[str, Any]) -> None:
        """
        Insert severity mapping record.
        
        Args:
            mapping_data: Dictionary containing mapping fields
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO classifier_outputs (
                    payload_id, subscription_id, resource_group, resource_type, 
                    resource_name, environment, severity_id, bert_score, rule_score, 
                    combined_score, matched_pattern, is_incident, source_type, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mapping_data.get('payload_id'),
                mapping_data.get('subscription_id'),
                mapping_data.get('resource_group'),
                mapping_data.get('resource_type'),
                mapping_data.get('resource_name'),
                mapping_data.get('environment'),
                mapping_data.get('severity_id'),
                mapping_data.get('bert_score'),
                mapping_data.get('rule_score'),
                mapping_data.get('combined_score'),
                mapping_data.get('matched_pattern'),
                mapping_data.get('is_incident', 1),
                mapping_data.get('source_type'),
                mapping_data.get('payload')
            ))
            
            conn.commit()
    
    def update_incident_status(self, incident_id: str, status: str = 'processed') -> None:
        """
        Update incident log status.
        
        Args:
            incident_id: Incident identifier (payload_id)
            status: New status value
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE incident_logs 
                SET status = ?, processed_at = CURRENT_TIMESTAMP 
                WHERE payload_id = ?
            """, (status, incident_id))
            conn.commit()
    
    def approve_corrective_action(self, payload_id: str, approved_action: str, 
                                  approved_by: str) -> None:
        """
        Approve LLM-generated corrective action.
        
        Args:
            payload_id: Payload identifier
            approved_action: Approved corrective action text
            approved_by: User who approved the action
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE classifier_outputs 
                SET approved_corrective_action = ?,
                    is_llm_correction_approved = 1,
                    approved_by = ?,
                    approved_ts = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE payload_id = ?
            """, (approved_action, approved_by, payload_id))
            conn.commit()
            
        logger.info(f"Approved corrective action for payload: {payload_id}")
    
    def get_severity_statistics(self) -> Dict[str, int]:
        """
        Get severity level distribution statistics.
        
        Returns:
            Dictionary mapping severity levels to counts
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT severity_id, COUNT(*) as count
                FROM classifier_outputs
                GROUP BY severity_id
            """)
            results = cursor.fetchall()
        
        stats = {row[0]: row[1] for row in results}
        logger.info(f"Severity statistics: {stats}")
        return stats
    
    def get_incidents_by_severity(self, severity_level: str, limit: int = 100) -> List[Dict]:
        """
        Get incidents filtered by severity level.
        
        Args:
            severity_level: Severity level (S1, S2, S3, S4)
            limit: Maximum number of records
            
        Returns:
            List of incident dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT payload_id, environment, resource_type, severity_id,
                       bert_score, rule_score, combined_score, matched_pattern,
                       processed_at
                FROM classifier_outputs
                WHERE severity_id = ?
                ORDER BY processed_at DESC
                LIMIT ?
            """, (severity_level, limit))
            
            results = cursor.fetchall()
        
        incidents = []
        for row in results:
            incidents.append({
                'payload_id': row[0],
                'environment': row[1],
                'resource_type': row[2],
                'severity_id': row[3],
                'bert_score': row[4],
                'rule_score': row[5],
                'combined_score': row[6],
                'matched_pattern': row[7],
                'processed_at': row[8]
            })
        
        return incidents