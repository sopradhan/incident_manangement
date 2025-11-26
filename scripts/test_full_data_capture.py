#!/usr/bin/env python3
"""
COMPREHENSIVE DATABASE CAPTURE TEST
Tests ingestion, querying, and healing to verify all 3 tables are populated
"""
import sys
sys.path.insert(0, '.')

from src.incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent
import sqlite3
import json

def print_section(title):
    print(f"\n{'='*90}")
    print(f"[*] {title}")
    print(f"{'='*90}\n")

def main():
    try:
        # Initialize agent
        print_section("PHASE 1: Initialization")
        agent = LangGraphRAGAgent()
        print("[+] Agent initialized successfully")
        
        # Phase 1: Test Ingestion (should populate document_metadata & chunk_embedding_data)
        print_section("PHASE 2: Document Ingestion")
        print("[*] Ingesting test document...")
        
        ingest_result = agent.ingest_document(
            text='''
            INCIDENT MANAGEMENT GUIDE
            
            Incident severity levels are classified as follows:
            - Critical: System down, affecting all users
            - High: Major functionality unavailable
            - Medium: Partial functionality affected
            - Low: Minor issues, workaround available
            
            Response times:
            - Critical: 15 minutes
            - High: 1 hour
            - Medium: 4 hours
            - Low: 1 business day
            ''',
            doc_id='incident_guide_001'
        )
        
        print(f"[+] Ingestion result: success={ingest_result['success']}, chunks={ingest_result['chunks_saved']}")
        
        # Phase 2: Test Query (should populate rag_history_and_optimization with QUERY event)
        print_section("PHASE 3: User Query")
        print("[*] Asking question...")
        
        query_result = agent.ask_question(
            question="What is the response time for critical incidents?",
            doc_id="incident_guide_001"
        )
        
        print(f"[+] Query result: success={query_result['success']}")
        if query_result.get('answer'):
            print(f"[+] Answer: {query_result['answer'][:100]}...")
        
        # Phase 3: Check database
        print_section("PHASE 4: Database Verification")
        
        conn = sqlite3.connect('chroma_db/rag.db')
        cursor = conn.cursor()
        
        results = {}
        
        # Check document_metadata
        cursor.execute('SELECT COUNT(*) FROM document_metadata')
        doc_count = cursor.fetchone()[0]
        results['document_metadata'] = doc_count
        print(f"[+] document_metadata: {doc_count} row(s)")
        
        if doc_count > 0:
            cursor.execute('SELECT doc_id, title, chunk_size_char FROM document_metadata LIMIT 1')
            row = cursor.fetchone()
            print(f"    Sample: doc_id={row[0]}, title={row[1]}, chunk_size={row[2]}")
        
        # Check chunk_embedding_data
        cursor.execute('SELECT COUNT(*) FROM chunk_embedding_data')
        chunk_count = cursor.fetchone()[0]
        results['chunk_embedding_data'] = chunk_count
        print(f"\n[+] chunk_embedding_data: {chunk_count} row(s)")
        
        if chunk_count > 0:
            cursor.execute('SELECT chunk_id, doc_id, quality_score FROM chunk_embedding_data LIMIT 1')
            row = cursor.fetchone()
            print(f"    Sample: chunk_id={row[0]}, doc_id={row[1]}, quality={row[2]}")
        
        # Check rag_history_and_optimization
        cursor.execute('SELECT COUNT(*) FROM rag_history_and_optimization')
        history_count = cursor.fetchone()[0]
        results['rag_history_and_optimization'] = history_count
        print(f"\n[+] rag_history_and_optimization: {history_count} row(s)")
        
        # Show breakdown by event type
        cursor.execute('''
            SELECT event_type, COUNT(*) as count 
            FROM rag_history_and_optimization 
            GROUP BY event_type
        ''')
        event_types = cursor.fetchall()
        if event_types:
            print(f"    Event types breakdown:")
            for evt_type, cnt in event_types:
                print(f"      - {evt_type}: {cnt}")
        
        if history_count > 0:
            cursor.execute('''
                SELECT history_id, event_type, query_text, action_taken 
                FROM rag_history_and_optimization 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            print(f"\n    Sample: history_id={row[0]}, event_type={row[1]}, query={str(row[2])[:40] if row[2] else 'N/A'}..., action={row[3]}")
        
        conn.close()
        
        # Final summary
        print_section("SUMMARY")
        
        all_populated = all(count > 0 for count in results.values())
        
        print("[RESULTS]")
        for table_name, count in results.items():
            status = "[V]" if count > 0 else "[X]"
            print(f"  {status} {table_name}: {count} rows")
        
        print("\n[CONCLUSION]")
        if all_populated:
            print("[SUCCESS] All 3 tables have data!")
            print("[+] document_metadata: Document info captured")
            print("[+] chunk_embedding_data: Chunk quality tracking captured")
            print("[+] rag_history_and_optimization: Query & healing events captured")
            return 0
        else:
            print("[PARTIAL] Some tables are still empty")
            missing = [t for t, c in results.items() if c == 0]
            print(f"Missing data in: {', '.join(missing)}")
            return 1
        
    except Exception as e:
        import traceback
        print_section("ERROR")
        print(f"[ERROR] {e}")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
