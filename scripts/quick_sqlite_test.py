#!/usr/bin/env python3
"""
Quick test to verify SQLite data capture
"""
import sys
sys.path.insert(0, '.')

from src.incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent
import sqlite3

try:
    print("[*] Initializing agent...")
    agent = LangGraphRAGAgent()
    
    print("[*] Ingesting test document...")
    result = agent.ingest_document(
        text='This is a test document about incident management. Incident severity levels are: critical, high, medium, low.',
        doc_id='test_doc_001'
    )
    
    print("[*] Ingestion result:", result)
    
    # Check database
    print("\n[*] Checking database...")
    conn = sqlite3.connect('chroma_db/rag.db')
    cursor = conn.cursor()
    
    for table in ['document_metadata', 'chunk_embedding_data', 'rag_history_and_optimization']:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"[+] {table}: {count} rows")
    
    # Show sample data if exists
    if count > 0:
        cursor.execute('SELECT * FROM document_metadata LIMIT 1')
        row = cursor.fetchone()
        print(f"\n[Sample] document_metadata: {row}")
    
    conn.close()
    print("\n[DONE] Test complete")
    
except Exception as e:
    import traceback
    print(f"[ERROR] {e}")
    print(traceback.format_exc())
