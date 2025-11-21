"""
RBAC Model - Handles all role-based access control operations
"""
from typing import List, Dict, Any, Optional, Set
import json
from .base_model import BaseModel


class RBACModel(BaseModel):
    """Model for RBAC operations (user_roles and document_permissions tables)"""
    
    # User Roles Table
    user_roles_table = 'user_roles'
    
    # Document Permissions Table
    permissions_table = 'document_permissions'
    
    def __init__(self, conn):
        """Initialize RBAC model with connection"""
        super().__init__(conn)
        self.table = self.permissions_table  # Default table for BaseModel methods
    
    def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get all CDR codes (roles) for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of CDR codes
        """
        rows = self.raw_execute(
            "SELECT cdr_code FROM user_roles WHERE user_id = ?",
            (user_id,)
        )
        return [row['cdr_code'] for row in rows] if rows else []
    
    def get_document_permissions(self, doc_id: str) -> List[str]:
        """
        Get required CDR codes for document access
        
        Args:
            doc_id: Document identifier
            
        Returns:
            List of required CDR codes
        """
        rows = self.raw_execute(
            "SELECT cdr_code FROM document_permissions WHERE doc_id = ?",
            (doc_id,)
        )
        return [row['cdr_code'] for row in rows] if rows else []
    
    def get_document_permissions_detailed(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Get detailed permission records for document
        
        Args:
            doc_id: Document identifier
            
        Returns:
            List of permission records with all details
        """
        return self.raw_execute(
            "SELECT * FROM document_permissions WHERE doc_id = ?",
            (doc_id,)
        )
    
    def assign_document_permission(self, doc_id: str, cdr_code: str,
                                  sensitivity: str, subject: str,
                                  assigned_by: str = 'llm_inference') -> int:
        """
        Assign RBAC permission to document (INSERT OR REPLACE)
        
        Args:
            doc_id: Document identifier
            cdr_code: CDR code for the role
            sensitivity: Sensitivity level (public, internal, confidential, etc.)
            subject: Subject area (engineering, hr, finance, legal, general)
            assigned_by: Who assigned this permission
            
        Returns:
            Last inserted row ID
        """
        cur = self.conn.execute("""
            INSERT OR REPLACE INTO document_permissions
            (doc_id, cdr_code, sensitivity, subject, assigned_by)
            VALUES (?, ?, ?, ?, ?)
        """, (doc_id, cdr_code, sensitivity, subject, assigned_by))
        self.conn.commit()
        return cur.lastrowid
    
    def assign_multiple_permissions(self, doc_id: str, cdr_codes: List[str],
                                   sensitivity: str, subject: str,
                                   assigned_by: str = 'llm_inference') -> None:
        """
        Assign multiple permissions to a document at once
        
        Args:
            doc_id: Document identifier
            cdr_codes: List of CDR codes
            sensitivity: Sensitivity level
            subject: Subject area
            assigned_by: Who assigned these permissions
        """
        for cdr_code in cdr_codes:
            self.assign_document_permission(doc_id, cdr_code, sensitivity, subject, assigned_by)
    
    def add_user_role(self, user_id: str, cdr_code: str) -> int:
        """
        Add a role (CDR code) to a user
        
        Args:
            user_id: User identifier
            cdr_code: CDR code to add
            
        Returns:
            Last inserted row ID
        """
        cur = self.conn.execute("""
            INSERT OR IGNORE INTO user_roles (user_id, cdr_code)
            VALUES (?, ?)
        """, (user_id, cdr_code))
        self.conn.commit()
        return cur.lastrowid
    
    def remove_user_role(self, user_id: str, cdr_code: str) -> None:
        """
        Remove a role from a user
        
        Args:
            user_id: User identifier
            cdr_code: CDR code to remove
        """
        self.conn.execute(
            "DELETE FROM user_roles WHERE user_id = ? AND cdr_code = ?",
            (user_id, cdr_code)
        )
        self.conn.commit()
    
    def check_permission(self, user_id: str, doc_id: str) -> bool:
        """
        Check if user has permission to access document
        
        Args:
            user_id: User identifier
            doc_id: Document identifier
            
        Returns:
            True if user has permission
        """
        user_roles = set(self.get_user_roles(user_id))
        required_roles = set(self.get_document_permissions(doc_id))
        
        # User needs at least one matching role
        has_access = bool(user_roles & required_roles)
        
        # Log access attempt
        self.log_access_attempt(user_id, doc_id, has_access, user_roles, required_roles)
        
        return has_access
    
    def log_access_attempt(self, user_id: str, doc_id: str, granted: bool,
                          user_roles: Set[str], required_roles: Set[str]):
        """
        Log access attempt for audit trail
        
        Args:
            user_id: User ID
            doc_id: Document ID
            granted: Whether access was granted
            user_roles: User's roles
            required_roles: Document's required roles
        """
        self.conn.execute("""
            INSERT INTO access_audit 
            (user_id, doc_id, granted, user_roles, required_roles)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            doc_id,
            1 if granted else 0,
            json.dumps(list(user_roles)),
            json.dumps(list(required_roles))
        ))
        self.conn.commit()
    
    def get_documents_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents accessible to a user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of accessible documents
        """
        return self.raw_execute("""
            SELECT DISTINCT d.* FROM documents d
            INNER JOIN document_permissions dp ON d.id = dp.doc_id
            WHERE dp.cdr_code IN (
                SELECT cdr_code FROM user_roles WHERE user_id = ?
            )
        """, (user_id,))
    
    def get_access_audit_log(self, user_id: Optional[str] = None,
                            doc_id: Optional[str] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get access audit log
        
        Args:
            user_id: Optional user filter
            doc_id: Optional document filter
            limit: Maximum records to return
            
        Returns:
            List of audit log entries
        """
        query = "SELECT * FROM access_audit WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if doc_id:
            query += " AND doc_id = ?"
            params.append(doc_id)
        
        query += " ORDER BY access_time DESC LIMIT ?"
        params.append(limit)
        
        return self.raw_execute(query, tuple(params))
    
    def clear_document_permissions(self, doc_id: str) -> None:
        """
        Clear all permissions for a document
        
        Args:
            doc_id: Document identifier
        """
        self.conn.execute(
            "DELETE FROM document_permissions WHERE doc_id = ?",
            (doc_id,)
        )
        self.conn.commit()
    
    def get_total_users_count(self) -> int:
        """
        Get total number of distinct users
        
        Returns:
            Count of distinct users
        """
        rows = self.raw_execute("SELECT COUNT(DISTINCT user_id) as count FROM user_roles")
        return rows[0]['count'] if rows else 0
