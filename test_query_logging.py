#!/usr/bin/env python
"""Test query logging to rag_history_and_optimization table"""

import json
from src.incident_iq.database.models.rag_history_model import RAGHistoryModel

def test_query_logging():
    model = RAGHistoryModel()
    
    # Get a valid doc_id from document_metadata
    model.cursor.execute("SELECT doc_id FROM document_metadata LIMIT 1")
    valid_doc_id = model.cursor.fetchone()[0]
    print(f"[*] Using doc_id: {valid_doc_id}")
    
    # Test log_query
    query_id = model.log_query(
        query_text='What are the incident priority levels?',
        target_doc_id=valid_doc_id,
        metrics_json=json.dumps({
            'frequency': 1,
            'avg_accuracy': 0.85,
            'cost_tokens': 150,
            'latency_ms': 245,
            'user_feedback': 0.8,
            'quality_category': 'warm',
            'sources_count': 3
        }),
        context_json=json.dumps({'contexts': 3, 'avg_score': 0.87}),
        session_id='session_abc123'
    )
    
    print(f'[✓] Query logged with ID: {query_id}')
    
    # Verify it was written
    model.cursor.execute("SELECT COUNT(*) as cnt FROM rag_history_and_optimization WHERE event_type = 'QUERY'")
    count = model.cursor.fetchone()
    print(f'[✓] Query events in table: {count[0]}')
    
    # Read back the record
    model.cursor.execute("SELECT history_id, query_text, metrics_json, session_id FROM rag_history_and_optimization WHERE event_type = 'QUERY' LIMIT 1")
    row = model.cursor.fetchone()
    if row:
        metrics = json.loads(row[2])
        print(f'[✓] Retrieved record:')
        print(f'  - History ID: {row[0]}')
        print(f'  - Text: {row[1]}')
        print(f'  - User Feedback: {metrics.get("user_feedback")}')
        print(f'  - Quality: {metrics.get("quality_category")}')
        print(f'  - Session: {row[3]}')

if __name__ == '__main__':
    test_query_logging()
