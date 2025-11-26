"""
Complete Demo: RL Healing Agent + LangGraph + Optimized Schema
Purpose: Show end-to-end flow with metadata tracking and intelligent optimization
Date: 2025-11-26
"""
import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent
from incident_iq.rag.agents.healing_agent.rl_healing_agent import RLHealingAgent


def demo_complete_workflow():
    """
    Complete workflow demonstration:
    1. Ingest document
    2. Query with RL optimization
    3. Show metadata tracking
    4. Display healing suggestions
    """
    
    print("\n" + "="*80)
    print("🚀 COMPLETE RAG WORKFLOW DEMO")
    print("   Optimized Schema + RL Healing Agent + LangGraph")
    print("="*80)
    
    # Initialize agent
    print("\n[1] Initializing LangGraph Agent with RL Healing...")
    try:
        agent = LangGraphRAGAgent()
        print("    ✅ LangGraph Agent initialized")
        if agent.rl_healing_agent:
            print("    ✅ RL Healing Agent initialized")
        else:
            print("    ⚠️  RL Healing Agent not available (DB might not be initialized)")
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return
    
    # Sample document
    sample_doc = """
    # Incident Management Framework
    
    ## Incident Severity Levels
    
    The incident management system categorizes incidents into four severity levels:
    
    ### Critical (Severity 1)
    - System completely down or unavailable
    - All users affected
    - Revenue impact
    - Response time: 15 minutes
    - Requires executive notification
    
    ### High (Severity 2)
    - Major functionality impaired
    - Multiple departments affected
    - Workarounds available
    - Response time: 1 hour
    
    ### Medium (Severity 3)
    - Limited functionality affected
    - Single department impacted
    - Minor workarounds available
    - Response time: 4 hours
    
    ### Low (Severity 4)
    - Cosmetic issues or minor inconvenience
    - Single user or non-critical feature
    - Response time: 24 hours
    
    ## Incident Workflow
    
    1. **Detection**: Alert received from monitoring system
    2. **Categorization**: Severity and component assignment
    3. **Assignment**: Route to appropriate team
    4. **Resolution**: Team works on fix
    5. **Verification**: Solution tested and verified
    6. **Communication**: Update stakeholders
    7. **Closure**: Mark as resolved, capture lessons learned
    
    ## Response Time SLAs
    
    - Critical: 99.9% uptime SLA, 4-hour resolution target
    - High: 99.5% uptime SLA, 8-hour resolution target
    - Medium: 99% uptime SLA, 24-hour resolution target
    - Low: 95% uptime SLA, 48-hour resolution target
    """
    
    doc_id = "incident_mgmt_001"
    
    # Ingest document
    print("\n[2] Ingesting Document...")
    print(f"    Document ID: {doc_id}")
    print(f"    Content length: {len(sample_doc)} characters")
    
    try:
        ingest_result = agent.ingest_document(sample_doc, doc_id)
        print(f"    ✅ Ingestion successful")
        print(f"       - Chunks created: {ingest_result['chunks_count']}")
        print(f"       - Chunks saved: {ingest_result['chunks_saved']}")
    except Exception as e:
        print(f"    ❌ Ingestion failed: {e}")
        return
    
    # Query with different quality levels
    test_queries = [
        {
            "question": "What are the incident severity levels?",
            "expected_quality": "high"
        },
        {
            "question": "What is the SLA for critical incidents?",
            "expected_quality": "high"
        },
        {
            "question": "Explain the incident workflow process.",
            "expected_quality": "high"
        },
    ]
    
    print("\n[3] Executing Queries with RL Agent...")
    print("-" * 80)
    
    for i, query_info in enumerate(test_queries, 1):
        question = query_info["question"]
        print(f"\n    [{i}] Query: \"{question}\"")
        
        try:
            result = agent.ask_question(question, doc_id=doc_id)
            
            # Display results
            print(f"        ✅ Status: {'Success' if result['success'] else 'Failed'}")
            print(f"        📊 Retrieval Quality: {result['retrieval_quality']:.2%}")
            print(f"        📄 Sources Found: {result['sources_count']} documents")
            
            # RL Agent Info
            if result['rl_recommendation']:
                rl = result['rl_recommendation']
                print(f"        🤖 RL Action: {rl['action']}")
                print(f"           - Confidence: {rl['confidence']:.2%}")
                print(f"           - Expected Improvement: {rl['expected_improvement']:.1%}")
            
            # Optimization Info
            if result['optimization_applied']:
                print(f"        ⚙️  Optimization Applied: {result['rl_action']}")
                print(f"           - Reason: {result['optimization_reason']}")
            
            # Answer preview
            answer_preview = result['answer'][:150] if isinstance(result['answer'], str) else str(result['answer'])[:150]
            print(f"        💬 Answer: {answer_preview}...")
            
            # Show traceability
            if result['traceability']:
                trace = result['traceability']
                if isinstance(trace, str):
                    trace = json.loads(trace)
                sources = trace.get('traceability', {}).get('documents', [])
                if sources:
                    print(f"        🔗 Traceability:")
                    for source in sources[:2]:
                        print(f"           - {source.get('doc_id')}: {source.get('text_preview', '')[:80]}...")
            
            # Errors
            if result['errors']:
                print(f"        ⚠️  Errors: {result['errors']}")
                
        except Exception as e:
            print(f"        ❌ Query failed: {e}")
    
    # RL Agent Learning Stats
    print("\n[4] RL Agent Learning Statistics")
    print("-" * 80)
    
    if agent.rl_healing_agent:
        try:
            stats = agent.rl_healing_agent.get_learning_stats()
            print(f"\n    📈 Learning Progress:")
            print(f"       - Total decisions: {stats['total_decisions']}")
            print(f"       - Exploration rate (epsilon): {stats['epsilon']:.2%}")
            print(f"       - Best performing action: {stats['best_action']}")
            
            print(f"\n    📊 Action Usage Distribution:")
            for action, data in stats['actions'].items():
                usage = data['percentage']
                reward = data['avg_reward']
                print(f"       - {action:12} | Usage: {usage:5.1f}% | Avg Reward: {reward:7.4f}")
        except Exception as e:
            print(f"    ⚠️  Could not get learning stats: {e}")
    
    # Database Schema Summary
    print("\n[5] Database Schema Summary")
    print("-" * 80)
    print("""
    ✅ Optimized 3-Table Schema:
    
    1. document_metadata
       ├─ Stores document metadata and chunking strategy
       ├─ PK: doc_id
       ├─ FK references: (none)
       └─ Rows: ~1-1000 (one per document)
    
    2. chunk_embedding_data
       ├─ Stores per-chunk quality and RL suggestions
       ├─ PK: chunk_id
       ├─ FK: doc_id → document_metadata
       └─ Rows: ~1000-100000 (many per document)
    
    3. rag_history_and_optimization
       ├─ Unified log for QUERY, HEAL, SYNTHETIC_TEST events
       ├─ PK: history_id (auto-increment)
       ├─ FK: target_doc_id → document_metadata
       └─ Rows: ~100-1000000 (grows with usage)
    
    📊 Benefits:
       • Reduced from 5 tables to 3 (40% reduction)
       • Clear relationships and foreign keys
       • Flexible JSON fields for evolution
       • Single historical log for all events
       • Ready for RL agent tracking
    """)
    
    # Sample SQL Queries
    print("\n[6] Sample SQL Queries for Complete Picture")
    print("-" * 80)
    print("""
    # Document Health Dashboard
    SELECT d.doc_id, d.title, COUNT(c.chunk_id) as chunks,
           AVG(c.quality_score) as quality
    FROM document_metadata d
    LEFT JOIN chunk_embedding_data c ON d.doc_id = c.doc_id
    GROUP BY d.doc_id;
    
    # Healing History
    SELECT json_extract(h.metrics_json, '$.strategy') as strategy,
           COUNT(*) as times_used,
           AVG(CAST(json_extract(h.metrics_json, '$.improvement_delta') AS FLOAT)) as improvement
    FROM rag_history_and_optimization h
    WHERE h.event_type = 'HEAL'
    GROUP BY strategy;
    
    # Query Performance Heatmap
    SELECT h.query_text, COUNT(*) as frequency,
           AVG(CAST(json_extract(h.metrics_json, '$.avg_accuracy') AS FLOAT)) as accuracy
    FROM rag_history_and_optimization h
    WHERE h.event_type = 'QUERY'
    GROUP BY h.query_text;
    
    # RL Agent Decisions
    SELECT h.action_taken, AVG(h.reward_signal) as avg_reward, COUNT(*) as count
    FROM rag_history_and_optimization h
    WHERE h.action_taken IS NOT NULL
    GROUP BY h.action_taken;
    """)
    
    print("\n" + "="*80)
    print("✅ DEMO COMPLETE")
    print("="*80)
    print("""
    Next Steps:
    1. Run migration: python src/incident_iq/database/migration/optimized_schema/run_migration.py
    2. Monitor RL agent learning over multiple queries
    3. Check database tables for metadata updates
    4. Use SQL queries to analyze system performance
    5. Tune RL parameters based on observed patterns
    """)


if __name__ == "__main__":
    demo_complete_workflow()
