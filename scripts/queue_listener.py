import asyncio
import json

from pathlib import Path

import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..','src')))


#from ai_models.llm.corrective_action_rag import handle_message
from incident_iq.database.db.connection import get_connection  
from incident_iq.transport.main import Transporter 
from incident_iq.database.models.queue import QueueModel

POLL_INTERVAL = 1  # seconds between checks

def get_model():
    conn = get_connection()
    queue_model = QueueModel(conn)

    return queue_model

def get_pending_message():
    queue_model = get_model()
    row = queue_model.get_first_pending_item()
    if row:
        return {"id": row['id'], "data": json.loads(row['data'])}

    return None

def mark_message_processed(message_id):
    queue_modal = get_model()
    queue_modal.set_processed(message_id)

async def watch_queue():
    """Continuously poll the queue for new messages."""
    print("🚀 Queue watcher started. Waiting for messages...\n")

    while True:
        message = get_pending_message()

        if not message:
            print("No pending message found.")
            await asyncio.sleep(POLL_INTERVAL)
            continue

        # log = "Processing " + message['data']['task'] + " with id: " + message['id']
    
        if(message['data']['task'] == 'llm_invoke'):
            transporter = Transporter()
            await transporter.process(message['data']['data'])
        
        elif(message['data']['task'] == 'set_corrective_action'):
            mark_message_processed(message["id"])
            pass
    
        elif(message['data']['task'] == 'sourav-producer2'):
            print("Sourav Block 2")

        else:
            mark_message_processed(message["id"])
            
        await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(watch_queue())
