"""
Phase I: RBAC Policy Service (RPS)
Dynamic, fine-grained Role-Based Access Control microservice
Decoupled from RAG agents - can be called independently

This service queries Employee/Role/Dept tables and maps user attributes
to fine-grained access tags
"""
import json
import sqlite3
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict


@dataclass
class UserPermissions:
    """User's held tags based on Employee/Role/Dept data"""
    user_id: str
    role: str
    department: str
    level: str
    held_tags: Dict[str, List[str]]
    
    def to_dict(self):
        return asdict(self)


class RBACPolicyService:
    """
    Microservice for dynamic RBAC - queries external tables to generate access tags
    
    Decoupling Benefit: IngestionAgent and RetrievalAgent don't need to know about
    Employee/Role/Dept table schemas. They just call RPS endpoints.
    """
    
    def __init__(self, db_path: str = None):
        """Initialize RPS with database connection"""
        self.db_path = db_path or "app.db"
        self.cache = {}  # Simple cache for user permissions
    
    # =========================================================================
    # ENDPOINT 1: Get User Permissions
    # =========================================================================
    
    def get_user_permissions(self, user_id: str) -> Dict:
        """
        GET /user-permissions/{user_id}
        
        Query Employee/Role/Dept tables and return user's held tags
        
        Args:
            user_id: User identifier
            
        Returns:
            {
                "user_id": "user_123",
                "role": "Manager",
                "department": "Finance",
                "level": "L3",
                "held_tags": {
                    "policy:role": ["Manager"],
                    "policy:dept": ["Finance"],
                    "policy:level": ["confidential", "internal"],
                    "policy:classification": ["Financial"],
                    "policy:status": ["active"]
                }
            }
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Query Employee/Role/Dept tables
            user_data = self._query_user_data(conn, user_id)
            
            if not user_data:
                return {"error": f"User {user_id} not found", "access_granted": False}
            
            # Map user data to held tags
            held_tags = self._map_user_to_tags(user_data)
            
            conn.close()
            
            permissions = UserPermissions(
                user_id=user_id,
                role=user_data.get('role', 'Unknown'),
                department=user_data.get('department', 'Unknown'),
                level=user_data.get('level', 'L1'),
                held_tags=held_tags
            )
            
            return permissions.to_dict()
            
        except Exception as e:
            return {"error": str(e), "access_granted": False}
    
    # =========================================================================
    # ENDPOINT 2: Evaluate Access
    # =========================================================================
    
    def evaluate_access(self, user_id: str, document_access_tags: Dict, 
                       operator: str = "AND") -> Dict:
        """
        POST /evaluate-access
        
        Check if user can access document based on tags
        
        Args:
            user_id: User identifier
            document_access_tags: Required tags for document (from embedding_metadata.access_tags)
            operator: "AND" = all tags required, "OR" = any tag required
            
        Returns:
            {
                "access_granted": true,
                "user_id": "user_123",
                "matched_tags": ["policy:dept", "policy:level"],
                "missing_tags": [],
                "reason": "User has all required tags"
            }
        """
        try:
            # Get user's held tags
            user_perms = self.get_user_permissions(user_id)
            
            if "error" in user_perms:
                return {
                    "access_granted": False,
                    "reason": user_perms["error"]
                }
            
            held_tags = user_perms['held_tags']
            
            # Evaluate access based on document tags
            matched_tags = []
            missing_tags = []
            
            for tag_key, required_values in document_access_tags.items():
                if isinstance(required_values, str):
                    required_values = [required_values]
                
                held_values = held_tags.get(tag_key, [])
                
                # Check if user has any of the required values
                if any(val in held_values for val in required_values):
                    matched_tags.append(tag_key)
                else:
                    missing_tags.append(tag_key)
            
            # Determine final access based on operator
            if operator == "AND":
                access_granted = len(missing_tags) == 0
            elif operator == "OR":
                access_granted = len(matched_tags) > 0
            else:
                access_granted = False
            
            return {
                "access_granted": access_granted,
                "user_id": user_id,
                "matched_tags": matched_tags,
                "missing_tags": missing_tags,
                "reason": f"Matched {len(matched_tags)} tags, missing {len(missing_tags)}" 
                          if not access_granted else "Access granted"
            }
            
        except Exception as e:
            return {
                "access_granted": False,
                "reason": str(e)
            }
    
    # =========================================================================
    # ENDPOINT 3: Get Document Tags
    # =========================================================================
    
    def get_document_tags(self, doc_id: str) -> Dict:
        """
        GET /document-tags/{doc_id}
        
        Get required access tags for a document from embedding_metadata
        
        Args:
            doc_id: Document identifier
            
        Returns:
            {
                "document_id": "doc_123",
                "required_tags": {
                    "policy:dept": ["Finance", "HR"],
                    "policy:level": ["confidential"],
                    "policy:classification": ["Financial"]
                }
            }
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Query embedding_metadata for access_tags
            query = """
                SELECT DISTINCT access_tags 
                FROM embedding_metadata 
                WHERE document_id = ? 
                LIMIT 1
            """
            rows = conn.execute(query, (doc_id,)).fetchall()
            
            conn.close()
            
            if not rows or not rows[0]['access_tags']:
                return {
                    "document_id": doc_id,
                    "required_tags": {}
                }
            
            # Parse JSON tags
            access_tags = json.loads(rows[0]['access_tags'])
            
            return {
                "document_id": doc_id,
                "required_tags": access_tags
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # =========================================================================
    # INTERNAL HELPER METHODS
    # =========================================================================
    
    def _query_user_data(self, conn: sqlite3.Connection, user_id: str) -> Optional[Dict]:
        """
        Query Employee/Role/Dept tables to get user data
        
        Assumes schema:
          - employees (employee_id, name, department_id, level)
          - roles (role_id, role_name, permissions)
          - departments (department_id, name, classification)
        """
        try:
            # This is a template - adjust query based on your actual schema
            query = """
                SELECT 
                    e.employee_id as user_id,
                    e.name,
                    r.role_name as role,
                    d.name as department,
                    e.level,
                    d.classification,
                    r.permissions
                FROM employees e
                LEFT JOIN roles r ON e.role_id = r.role_id
                LEFT JOIN departments d ON e.department_id = d.department_id
                WHERE e.employee_id = ?
            """
            
            rows = conn.execute(query, (user_id,)).fetchall()
            
            if rows:
                return dict(rows[0])
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Failed to query user data: {e}")
            return None
    
    def _map_user_to_tags(self, user_data: Dict) -> Dict[str, List[str]]:
        """
        Map user attributes to fine-grained access tags
        
        User attributes (from Employee/Role/Dept) → Access tags
        """
        tags = {
            "policy:role": [],
            "policy:dept": [],
            "policy:level": [],
            "policy:classification": [],
            "policy:status": []
        }
        
        # Map role
        if user_data.get('role'):
            tags["policy:role"].append(user_data['role'])
            # Add permissions as additional tags
            if user_data.get('role') == 'Manager':
                tags["policy:role"].append('Supervisor')
            elif user_data.get('role') == 'Director':
                tags["policy:role"].extend(['Manager', 'Supervisor'])
        
        # Map department
        if user_data.get('department'):
            tags["policy:dept"].append(user_data['department'])
        
        # Map level to classification tags
        level = user_data.get('level', 'L1')
        if level in ['L3', 'L4', 'L5']:  # Senior levels
            tags["policy:level"].extend(['confidential', 'internal'])
            tags["policy:classification"].append('Financial')
        elif level in ['L2']:  # Mid level
            tags["policy:level"].append('internal')
        else:  # L1
            tags["policy:level"].append('public')
        
        # Map department-specific classifications
        dept = user_data.get('department', '')
        if 'Finance' in dept:
            tags["policy:classification"].append('Financial')
        elif 'HR' in dept:
            tags["policy:classification"].append('HR_Personnel')
        elif 'Legal' in dept:
            tags["policy:classification"].append('Legal')
        elif 'Engineering' in dept:
            tags["policy:classification"].append('Technical')
        
        # Add status
        tags["policy:status"].append('active')
        
        # Remove empty lists
        return {k: v for k, v in tags.items() if v}


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_usage():
    """Example usage of RBAC Policy Service"""
    
    rps = RBACPolicyService(db_path="app.db")
    
    # Example 1: Get user permissions
    print("\n=== Example 1: Get User Permissions ===")
    user_perms = rps.get_user_permissions("user_123")
    print(json.dumps(user_perms, indent=2))
    
    # Example 2: Evaluate access to document
    print("\n=== Example 2: Evaluate Access ===")
    document_tags = {
        "policy:dept": ["Finance"],
        "policy:level": ["confidential"],
        "policy:classification": ["Financial"]
    }
    access_result = rps.evaluate_access("user_123", document_tags, operator="AND")
    print(json.dumps(access_result, indent=2))
    
    # Example 3: Get document tags
    print("\n=== Example 3: Get Document Tags ===")
    doc_tags = rps.get_document_tags("doc_456")
    print(json.dumps(doc_tags, indent=2))


if __name__ == "__main__":
    example_usage()
