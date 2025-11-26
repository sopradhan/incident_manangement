#!/usr/bin/env python3
"""
Test query logging directly
"""
import sys
sys.path.insert(0, '.')

import json
from src.incident_iq.database.models.rag_history_model import RAGHistoryModel

print("[*] Testing RAGHistoryModel.log_query()...")

try:
    rag_history = RAGHistoryModel()
    
    # Log a test query
    query_id = rag_history.log_query(
        query_text="What is the response time for critical incidents?",
        target_doc_id="test_doc_001",
        metrics_json=json.dumps({
            "frequency": 1,
            "avg_accuracy": 0.85,
            "cost_tokens": 150,
            "latency_ms": 342,
            "user_feedback": 0.9,
            "quality_category": "warm",
            "sources_count": 3
        }),
        context_json=json.dumps({
            "retrieval_quality": 0.85,
            "sources": 3,
            "answer_length": 25
        }),
        agent_id="langgraph_agent",
        session_id="test_session_001"
    )
    
    print(f"[+] Query logged successfully: query_id={query_id}")
    
    # Check database
    import sqlite3
    conn = sqlite3.connect('chroma_db/rag.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM rag_history_and_optimization')
    count = cursor.fetchone()[0]
    print(f"[+] rag_history_and_optimization now has {count} rows")
    
    if count > 0:
        cursor.execute('''
            SELECT history_id, event_type, query_text, metrics_json 
            FROM rag_history_and_optimization 
            ORDER BY history_id DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        if row:
            print(f"[+] Latest entry: history_id={row[0]}, event_type={row[1]}")
            print(f"    Query: {row[2]}")
            metrics = json.loads(row[3])
            print(f"    User Feedback: {metrics.get('user_feedback', 'N/A')}")
    
    conn.close()
    rag_history.close()
    print("\n[SUCCESS] Query logging works!")
    
except Exception as e:
    import traceback
    print(f"[ERROR] {e}")
    print(traceback.format_exc())
