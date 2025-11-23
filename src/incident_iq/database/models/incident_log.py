import json
from typing import List, Dict, Any
import json
from .base_model import BaseModel

class IncidentLogsModel(BaseModel):
    table = 'incident_logs'
    fields = ['payload_id', 'payload', 'source_type', 'status', 'created_at', 'processed_at']

    def find(self, payload_id: str) -> Dict[str, Any] | None:
        cur = self.conn.execute(f"SELECT * FROM {self.table} WHERE payload_id = ?", (payload_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def update(self, payload_id: str, payload: Dict[str, Any]) -> None:
        assignments = ', '.join([f"{k} = ?" for k in payload.keys()])
        values = tuple(payload.values()) + (payload_id,)
        # Note: No `updated_at` column update since table does not have it
        self.conn.execute(f"UPDATE {self.table} SET {assignments} WHERE payload_id = ?", values)
        self.conn.commit()

    def delete(self, payload_id: str) -> None:
        self.conn.execute(f"DELETE FROM {self.table} WHERE payload_id = ?", (payload_id,))
        self.conn.commit()

    def find_unprocessed(self) -> List[Dict[str, Any]]:
        cur = self.conn.execute(f"SELECT * FROM {self.table} WHERE processed_at IS NULL")
        return [dict(row) for row in cur.fetchall()]
    

    def bulk_insert(self, records: List[Dict[str, Any]]) -> None:
        """
        Bulk insert multiple records into the incident_logs table.

        Each record must be a dict containing:
            payload_id, payload, source_type, status, created_at, processed_at
        """
        sql = f"""
            INSERT INTO {self.table} 
            (payload_id, payload, source_type, status, created_at, processed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        values_list = []

        for rec in records:
            values_list.append((
                rec["payload_id"],
                json.dumps(rec["payload"]),
                rec["source_type"],
                rec["status"],
                rec["created_at"],
                rec["processed_at"]
            ))

        self.conn.executemany(sql, values_list)
        self.conn.commit()
