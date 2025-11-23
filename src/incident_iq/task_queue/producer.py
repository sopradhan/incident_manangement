import threading
import time
import uuid

from incident_iq.database.db.connection import get_connection
from incident_iq.database.models.queue import QueueModel
import json

class Producer(threading.Thread):
    """Producer thread that adds items to the queue."""
    
    def __init__(self, producer_id: str, items: list):
        super().__init__(daemon=True)
        self.producer_id = producer_id
        self.items = items

    def get_model():
        conn = get_connection()
        queue_model = QueueModel(conn)
        return queue_model    
        
    def run(self):
        """Produce items into the queue."""
        conn = get_connection()
        queue_model = QueueModel(conn)

        for item in self.items:
            payload ={
                "id": str(uuid.uuid4()),
                "data": json.dumps(item),
                "status": "pending"
            }
            queue_model.insert(payload)
            time.sleep(0.5)
        
        print(f"[{self.producer_id}] Finished producing")
