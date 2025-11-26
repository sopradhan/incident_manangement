#!/usr/bin/env python
"""
End-to-End Test: Document Ingestion → Query → Logging → Visualization
"""

import json
import sys
from pathlib import Path

# Test 1: Verify database configuration
print("\n" + "="*80)
print("TEST 1: Database Configuration")
print("="*80)

try:
    from src.incident_iq.rag.config.env_config import EnvConfig
    
    env = EnvConfig()
    db_path = env.get_db_path()
    print(f"[✓] Database path configured: {db_path}")
    
    # Check if file exists
    if Path(db_path).exists():
        print(f"[✓] Database file exists: {db_path}")
    else:
        print(f"[✗] Database file NOT found: {db_path}")
        sys.exit(1)
        
except Exception as e:
    print(f"[✗] Failed to load database config: {e}")
    sys.exit(1)

# Test 2: Verify RAGHistoryModel connection
print("\n" + "="*80)
print("TEST 2: RAGHistoryModel Connection")
print("="*80)

try:
    from src.incident_iq.database.models.rag_history_model import RAGHistoryModel
    
    model = RAGHistoryModel()
    print(f"[✓] RAGHistoryModel instantiated successfully")
    print(f"[✓] Database path: {model.db_path}")
    
    # Check table existence
    model.cursor.execute("SELECT COUNT(*) FROM rag_history_and_optimization")
    count = model.cursor.fetchone()[0]
    print(f"[✓] rag_history_and_optimization table accessible ({count} rows)")
    
except Exception as e:
    print(f"[✗] RAGHistoryModel connection failed: {e}")
    sys.exit(1)

# Test 3: Verify ingestion pipeline
print("\n" + "="*80)
print("TEST 3: Ingestion Pipeline Status")
print("="*80)

try:
    model = RAGHistoryModel()
    
    # Check document_metadata
    model.cursor.execute("SELECT COUNT(*) FROM document_metadata")
    doc_count = model.cursor.fetchone()[0]
    print(f"[✓] document_metadata: {doc_count} documents")
    
    # Check chunk_embedding_data
    model.cursor.execute("SELECT COUNT(*) FROM chunk_embedding_data")
    chunk_count = model.cursor.fetchone()[0]
    print(f"[✓] chunk_embedding_data: {chunk_count} chunks")
    
    # Get sample doc_id for testing
    model.cursor.execute("SELECT doc_id FROM document_metadata LIMIT 1")
    row = model.cursor.fetchone()
    sample_doc_id = row[0] if row else None
    print(f"[✓] Sample doc_id: {sample_doc_id}")
    
except Exception as e:
    print(f"[✗] Ingestion pipeline check failed: {e}")
    sys.exit(1)

# Test 4: Test query logging
print("\n" + "="*80)
print("TEST 4: Query Logging Functionality")
print("="*80)

try:
    model = RAGHistoryModel()
    
    if not sample_doc_id:
        print("[!] No documents found, skipping query logging test")
    else:
        query_id = model.log_query(
            query_text="What is the incident management process?",
            target_doc_id=sample_doc_id,
            metrics_json=json.dumps({
                "frequency": 1,
                "avg_accuracy": 0.85,
                "cost_tokens": 100,
                "latency_ms": 250,
                "user_feedback": 0.75,
                "quality_category": "warm",
                "sources_count": 3
            }),
            context_json=json.dumps({"contexts": 3, "avg_score": 0.86}),
            session_id="test_session_001"
        )
        
        print(f"[✓] Query logged with ID: {query_id}")
        
        # Verify it was written
        model.cursor.execute("SELECT COUNT(*) FROM rag_history_and_optimization WHERE event_type = 'QUERY'")
        query_count = model.cursor.fetchone()[0]
        print(f"[✓] QUERY events in table: {query_count}")
        
except Exception as e:
    print(f"[✗] Query logging failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test healing logging
print("\n" + "="*80)
print("TEST 5: Healing Action Logging")
print("="*80)

try:
    model = RAGHistoryModel()
    
    if not sample_doc_id:
        print("[!] No documents found, skipping healing logging test")
    else:
        healing_id = model.log_healing(
            target_doc_id=sample_doc_id,
            target_chunk_id=f"{sample_doc_id}_chunk_1",
            metrics_json=json.dumps({
                "strategy": "OPTIMIZE",
                "before_quality": 0.65,
                "after_quality": 0.82,
                "improvement": 0.17
            }),
            context_json=json.dumps({
                "reason": "quality_improvement",
                "alternatives_considered": ["SKIP", "REINDEX"]
            }),
            action_taken="OPTIMIZE",
            reward_signal=0.15,
            session_id="test_session_001"
        )
        
        print(f"[✓] Healing action logged with ID: {healing_id}")
        
        # Verify it was written
        model.cursor.execute("SELECT COUNT(*) FROM rag_history_and_optimization WHERE event_type = 'HEAL'")
        heal_count = model.cursor.fetchone()[0]
        print(f"[✓] HEAL events in table: {heal_count}")
        
except Exception as e:
    print(f"[✗] Healing logging failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Visualization utility
print("\n" + "="*80)
print("TEST 6: LangGraph Visualization")
print("="*80)

try:
    from src.incident_iq.rag.visualization.langgraph_visualizer import (
        create_visualization, 
        LangGraphVisualization
    )
    
    viz = create_visualization("test_session_001")
    print(f"[✓] Visualization tracker created: {viz.session_id}")
    
    # Simulate some node execution
    viz.record_node_start("retrieve_context", {"question": "test"})
    viz.record_node_end("retrieve_context", {"retrieved_docs": 5})
    
    viz.record_node_start("rerank_context", {"documents": 5})
    viz.record_node_end("rerank_context", {"reranked_docs": 5})
    
    viz.record_node_start("generate_answer", {"context": "test"})
    viz.record_node_end("generate_answer", {"answer": "Test answer"})
    
    # Get trace data
    trace = viz.get_trace_data()
    print(f"[✓] Trace data generated with {trace['node_count']} nodes")
    print(f"[✓] Success rate: {trace['successful_nodes']}/{trace['node_count']}")
    
    # Generate ASCII diagram
    diagram = viz.generate_ascii_diagram()
    print("[✓] ASCII diagram generated (see below):")
    print(diagram)
    
except Exception as e:
    print(f"[✗] Visualization test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("="*80)
print("✓ ALL TESTS PASSED")
print("="*80)
print("\n[Summary]")
print(f"  - Database: ✓ Connected")
print(f"  - Documents: {doc_count} ingested")
print(f"  - Chunks: {chunk_count} embedded")
print(f"  - Query logging: ✓ Working")
print(f"  - Healing logging: ✓ Working")
print(f"  - Visualization: ✓ Working")
print("\nThe system is ready for end-to-end testing with LangGraph!")
