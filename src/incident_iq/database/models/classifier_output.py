from datetime import datetime
from pydoc import text
from typing import List, Dict, Any, Optional
from .base_model import BaseModel
from datetime import datetime

class ClassifierOutputsModel(BaseModel):
    table = 'classifier_outputs'
    fields = ['id', 'payload_id', 'subscription_id', 'resource_group', 'resource_type', 'resource_name', 'environment', 'severity_id', 'bert_score', 'rule_score', 'combined_score', 'matched_pattern', 'is_incident', 'source_type', 'payload', 'processed_at', 'corrective_action', 'approved_corrective_action', 'is_llm_correction_approved', 'approved_by', 'approved_at', 'approved_severity', 'created_at', 'updated_at']


    def find_unprocessed(self) -> List[Dict[str, Any]]:
        """
        Fetch all rows where processed_at IS NULL.
        """
        cur = self.conn.execute(f"SELECT * FROM {self.table} WHERE processed_at IS NULL")
        return [dict(row) for row in cur.fetchall()]

    def update_by_id(self, id: int, 
                    approved_corrective_action: str = None, 
                    approved_by: str = None, 
                    approved_at: datetime = None,
                    is_llm_correction_approved: int = 0
                    ) -> None:
        """
        Update columns for a record identified by `id`.
        Only updates the fields provided (non-None).
        """
        
        # Collect fields to update
        update_fields = {}
        if approved_corrective_action is not None:
            update_fields["approved_corrective_action"] = approved_corrective_action
        if approved_by is not None:
            update_fields["approved_by"] = approved_by
        if approved_at is not None:
            update_fields["approved_at"] = approved_at    
        if is_llm_correction_approved is not None:
            update_fields["is_llm_correction_approved"] = is_llm_correction_approved    

        if not update_fields:
            print("No fields provided to update.")
            return

        # Prepare SQL
        assignments = ', '.join([f"{k} = ?" for k in update_fields.keys()])
        values = tuple(update_fields.values()) + (id,)
        sql = f"UPDATE {self.table} SET {assignments} WHERE id = ?"
        
        print("Executing SQL:", sql)
        print("With values:", values)

        self.conn.execute(sql, values)
        self.conn.commit()

    def get_by_payload_id(self, payload_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single record from the table by payload_id.
        Returns a dictionary of column values if found, else None.
        """
        sql = f"SELECT * FROM {self.table} WHERE payload_id = ?"
        cursor = self.conn.execute(sql, (payload_id,))
        row = cursor.fetchone()
        if row:
            # Convert sqlite3.Row or tuple to dict
            col_names = [description[0] for description in cursor.description]
            return dict(zip(col_names, row))
        return None


    def severity_count_by_environment(self) -> List[Dict[str, Any]]:
        sql = f"""
        SELECT 
            environment,
            COUNT(CASE WHEN severity_id = 'S1' THEN 1 END) AS s1,
            COUNT(CASE WHEN severity_id = 'S2' THEN 1 END) AS s2,
            COUNT(CASE WHEN severity_id = 'S3' THEN 1 END) AS s3,
            COUNT(CASE WHEN severity_id = 'S4' THEN 1 END) AS s4
        FROM 
            classifier_outputs
        WHERE 
            environment != 'unknown'
        GROUP BY 
            environment
        ORDER BY 
            environment DESC
        """
        cur = self.conn.execute(sql)
        return [dict(row) for row in cur.fetchall()]

    def severity_count_by_environment_and_resource(self) -> List[Dict[str, Any]]:
        sql = f"""
        SELECT 
            environment,
            resource_type,
            COUNT(CASE WHEN severity_id = 'S1' THEN 1 END) AS s1,
            COUNT(CASE WHEN severity_id = 'S2' THEN 1 END) AS s2,
            COUNT(CASE WHEN severity_id = 'S3' THEN 1 END) AS s3,
            COUNT(CASE WHEN severity_id = 'S4' THEN 1 END) AS s4
        FROM 
            classifier_outputs
        WHERE 
            environment != 'unknown'
            AND is_incident = 1
        GROUP BY 
            environment, resource_type
        ORDER BY 
            environment DESC, resource_type ASC
        """
        cur = self.conn.execute(sql)
        return [dict(row) for row in cur.fetchall()]


    def detailed_incident_counts(self) -> List[Dict[str, Any]]:
        sql = text("""
        SELECT 
            environment,
            resource_type,
            severity_id,
            is_incident,
            COUNT(*) AS count
        FROM 
            classifier_outputs
        WHERE 
            environment != 'unknown'
        GROUP BY 
            environment, resource_type, severity_id, is_incident
        ORDER BY 
            environment DESC, resource_type ASC, severity_id ASC, is_incident DESC
        """)
        cur = self.conn.execute(sql)
        return [dict(row) for row in cur.fetchall()]
    
    def find_unapproved_inc(self) -> List[Dict[str, Any]]:
        """
        Fetch all rows where is_llm_correction_approved IS NULL
        (i.e., pending approvals).
        """
        sql = f"""
            SELECT *
            FROM {self.table}
            WHERE approved_at IS NULL
        """
        cur = self.conn.execute(sql)
        return [dict(row) for row in cur.fetchall()]
