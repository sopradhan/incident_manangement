
from .base_model import BaseModel

class QueueModel(BaseModel):
    table = 'queue'
    fields = ['id', 'data', 'status', 'created_at','processed_at','consumer_id']

    def find_by_consumer_id(self, consumer_id):
        cur = self.conn.execute('SELECT * FROM companies WHERE consumer_id = ?', (consumer_id))
        r = cur.fetchone()
        return dict(r) if r else None
    
    def get_first_pending_item(self):
        query = """SELECT id, data FROM queue
        WHERE status = 'pending'
        ORDER BY created_at ASC
        LIMIT 1"""

        cur = self.conn.execute(query)
        r = cur.fetchone()
        return dict(r) if r else None

    def set_processed(self, id):
        query = """
            UPDATE queue
            SET status = 'processed',
                processed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """

        self.conn.execute(query, (id,))
        self.conn.commit()
        
        return True
