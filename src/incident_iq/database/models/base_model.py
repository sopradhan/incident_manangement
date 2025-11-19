from typing import List, Dict, Any, Optional

class BaseModel:
    table: str = ''
    fields: List[str] = []

    def __init__(self, conn):
        self.conn = conn

    def all(self) -> List[Dict[str, Any]]:
        cur = self.conn.execute(f"SELECT * FROM {self.table}")
        return [dict(r) for r in cur.fetchall()]

    def find(self, record_id: int) -> Optional[Dict[str, Any]]:
        cur = self.conn.execute(f"SELECT * FROM {self.table} WHERE id = ?", (record_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def insert(self, payload: Dict[str, Any]) -> int:
        keys = ','.join(payload.keys())
        placeholders = ','.join('?' for _ in payload)
        values = tuple(payload.values())
        cur = self.conn.execute(f"INSERT INTO {self.table} ({keys}) VALUES ({placeholders})", values)
        self.conn.commit()
        return cur.lastrowid

    def update(self, record_id: int, payload: Dict[str, Any]) -> None:
        assignments = ','.join([f"{k} = ?" for k in payload.keys()])
        values = tuple(payload.values()) + (record_id,)
        self.conn.execute(f"UPDATE {self.table} SET {assignments}, updated_at = datetime('now') WHERE id = ?", values)
        self.conn.commit()

    def delete(self, record_id: int) -> None:
        self.conn.execute(f"DELETE FROM {self.table} WHERE id = ?", (record_id,))
        self.conn.commit()

    # def raw_execute(self, query_string, query_values):
    #     self.conn.execute(query_string, query_values)
    #     self.conn.commit()

    def raw_execute(self, query_string, query_values=()):
        cur = self.conn.execute(query_string, query_values)
        if query_string.strip().upper().startswith("SELECT"):
            return cur.fetchall()  # return all rows for select query
        else:
            self.conn.commit()
            return None