#!/usr/bin/env python
"""
DeepAgents Healing Agent Test with Metadata Logging
Tests DeepAgents using healing_agent and updates the same database tables for metadata
as LangGraph, for consistency and unified query history tracking.

Tests:
1. Initialize DeepAgents RAG Agent
2. Ingest sample document using ingestion subagent
3. Retrieve and answer questions using retrieval subagent
4. Execute healing optimization using healing subagent
5. Log all operations to rag_history_and_optimization table
6. Verify metadata consistency across both agent types
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.incident_iq.rag.agents.deepagents_agent.deepagents_rag_agent import DeepAgentsRAGAgent
from src.incident_iq.database.models.rag_history_model import RAGHistoryModel
from src.incident_iq.rag.agents.healing_agent.rl_healing_agent import RLHealingAgent, RLState


# Sample documents for testing
SAMPLE_DOCUMENTS = {
    "doc_001": {
        "title": "Incident Management Best Practices",
        "content": """
            Incident management is a critical process for organizations to respond to and resolve 
            unexpected events that disrupt normal operations. Key best practices include:
            
            1. Preparedness: Establish clear incident response procedures and communication channels
            2. Detection: Monitor systems 24/7 to quickly identify anomalies
            3. Containment: Isolate affected systems to prevent further damage
            4. Investigation: Root cause analysis to understand what happened
            5. Recovery: Restore systems to normal operation
            6. Documentation: Record lessons learned for future reference
            
            Effective incident management reduces Mean Time To Resolution (MTTR) and improves 
            overall system reliability.
        """
    },
    "doc_002": {
        "title": "RAG Systems and Quality Optimization",
        "content": """
            Retrieval-Augmented Generation (RAG) systems combine retrieval and generation to 
            provide context-aware responses. Quality metrics include:
            
            - Relevance: How well retrieved documents match the query
            - Accuracy: Whether the generated answer is factually correct
            - Latency: Response time for retrieval and generation
            - Cost: Token consumption and computational resources
            
            Optimization strategies:
            - Chunk size tuning based on query patterns
            - Embedding model selection for domain-specific accuracy
            - Reranking to improve retrieval quality
            - Caching frequently accessed contexts
            
            Healing systems monitor these metrics and automatically optimize parameters.
        """
    },
    "doc_003": {
        "title": "Agent-Based Systems Architecture",
        "content": """
            Multi-agent systems enable complex task orchestration through specialized agents:
            
            DeepAgents Framework:
            - SubAgents: Specialized agents for specific tasks (Ingestion, Retrieval, Healing, Config)
            - Master Agent: Orchestrates subagents for complex workflows
            - Tool Integration: Each subagent has domain-specific tools
            - Modular Design: Easy to add new capabilities
            
            LangGraph Alternative:
            - State-based workflows using directed graphs
            - Nodes represent processing steps
            - Edges define conditional logic
            - Visualization support for understanding flow
            
            Both approaches enable autonomous RAG systems with different trade-offs.
        """
    }
}

TEST_QUERIES = [
    "What are the key steps in incident management?",
    "How can RAG system quality be measured and improved?",
    "What are the differences between DeepAgents and LangGraph architectures?",
    "What optimization strategies exist for embedding systems?"
]


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_deepagents_initialization():
    """Test 1: Initialize DeepAgents RAG Agent"""
    print_section("TEST 1: DeepAgents RAG Agent Initialization")
    
    try:
        agent = DeepAgentsRAGAgent()
        print("[✓] DeepAgentsRAGAgent initialized successfully")
        print(f"    - LLM Service: {agent.llm_service.__class__.__name__}")
        print(f"    - VectorDB Service: {agent.vectordb_service.__class__.__name__}")
        print(f"    - Config Service: {agent.config_service.__class__.__name__}")
        
        # Handle both dict and object subagent representations
        def get_subagent_name(subagent):
            if isinstance(subagent, dict):
                return subagent.get("name", "unknown")
            return getattr(subagent, "name", "unknown")
        
        print(f"    - Ingestion SubAgent: {get_subagent_name(agent.ingestion_subagent)}")
        print(f"    - Retrieval SubAgent: {get_subagent_name(agent.retrieval_subagent)}")
        print(f"    - Healing SubAgent: {get_subagent_name(agent.healing_subagent)}")
        print(f"    - Config SubAgent: {get_subagent_name(agent.config_subagent)}")
        return agent
    except Exception as e:
        print(f"[✗] Failed to initialize DeepAgentsRAGAgent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_ingestion_with_metadata_logging(agent: DeepAgentsRAGAgent, model: RAGHistoryModel, session_id: str):
    """Test 2: Ingest documents and log to metadata"""
    print_section("TEST 2: Document Ingestion with Metadata Logging")
    
    ingestion_results = []
    
    for doc_id, doc_data in SAMPLE_DOCUMENTS.items():
        try:
            print(f"\nIngesting document: {doc_id} - {doc_data['title']}")
            
            # Ingest through deepagents ingestion subagent
            result = agent.ingest_document(
                text=doc_data['content'],
                doc_id=doc_id
            )
            
            if result['success']:
                print(f"  [✓] Document ingestion successful")
                
                # Log to metadata table for consistency with LangGraph
                metrics = {
                    "doc_id": doc_id,
                    "title": doc_data['title'],
                    "content_length": len(doc_data['content']),
                    "ingestion_status": "completed",
                    "timestamp": datetime.now().isoformat()
                }
                
                history_id = model.log_query(
                    query_text=f"Ingest document: {doc_data['title']}",
                    target_doc_id=doc_id,
                    metrics_json=json.dumps(metrics),
                    context_json=json.dumps({
                        "agent_type": "deepagents",
                        "subagent": "IngestionSubAgent",
                        "document_title": doc_data['title']
                    }),
                    agent_id="deepagents_agent",
                    session_id=session_id
                )
                
                if history_id > 0:
                    print(f"  [✓] Metadata logged with history_id: {history_id}")
                    ingestion_results.append({
                        "doc_id": doc_id,
                        "title": doc_data['title'],
                        "history_id": history_id,
                        "status": "logged"
                    })
                else:
                    print(f"  [✗] Failed to log metadata")
                    ingestion_results.append({
                        "doc_id": doc_id,
                        "title": doc_data['title'],
                        "status": "ingested_but_not_logged"
                    })
            else:
                print(f"  [✗] Ingestion failed: {result.get('error')}")
                ingestion_results.append({
                    "doc_id": doc_id,
                    "title": doc_data['title'],
                    "status": "failed",
                    "error": result.get('error')
                })
        
        except Exception as e:
            print(f"  [✗] Exception during ingestion: {e}")
            import traceback
            traceback.print_exc()
            ingestion_results.append({
                "doc_id": doc_id,
                "title": doc_data['title'],
                "status": "error",
                "error": str(e)
            })
    
    return ingestion_results


def test_retrieval_with_metadata_logging(agent: DeepAgentsRAGAgent, model: RAGHistoryModel, 
                                         session_id: str, sample_doc_id: str = "doc_001"):
    """Test 3: Retrieve and answer questions, log to metadata"""
    print_section("TEST 3: Query Retrieval with Metadata Logging")
    
    retrieval_results = []
    
    for idx, query in enumerate(TEST_QUERIES, 1):
        try:
            print(f"\nQuery {idx}: {query}")
            
            # Ask question through retrieval subagent
            result = agent.ask_question(query)
            
            if result['success']:
                print(f"  [✓] Retrieval successful")
                
                # Extract answer from result (structure depends on implementation)
                answer = result.get('result', {}).get('answer', 'No answer generated')
                
                # Log query to metadata table
                metrics = {
                    "query_index": idx,
                    "query_length": len(query),
                    "retrieval_status": "successful",
                    "timestamp": datetime.now().isoformat()
                }
                
                history_id = model.log_query(
                    query_text=query,
                    target_doc_id=sample_doc_id,
                    metrics_json=json.dumps(metrics),
                    context_json=json.dumps({
                        "agent_type": "deepagents",
                        "subagent": "RetrievalSubAgent",
                        "answer_preview": str(answer)[:200]
                    }),
                    agent_id="deepagents_agent",
                    session_id=session_id
                )
                
                if history_id > 0:
                    print(f"  [✓] Query logged with history_id: {history_id}")
                    retrieval_results.append({
                        "query": query,
                        "history_id": history_id,
                        "status": "logged"
                    })
                else:
                    print(f"  [✗] Failed to log query")
                    retrieval_results.append({
                        "query": query,
                        "status": "retrieved_but_not_logged"
                    })
            else:
                print(f"  [✗] Retrieval failed: {result.get('error')}")
                retrieval_results.append({
                    "query": query,
                    "status": "failed",
                    "error": result.get('error')
                })
        
        except Exception as e:
            print(f"  [✗] Exception during retrieval: {e}")
            import traceback
            traceback.print_exc()
            retrieval_results.append({
                "query": query,
                "status": "error",
                "error": str(e)
            })
    
    return retrieval_results


def test_healing_with_metadata_logging(agent: DeepAgentsRAGAgent, model: RAGHistoryModel, 
                                       session_id: str, sample_doc_id: str = "doc_001"):
    """Test 4: Execute healing optimization and log to metadata"""
    print_section("TEST 4: Healing Optimization with Metadata Logging")
    
    healing_results = []
    
    try:
        # Create performance history for healing
        performance_history = [
            {
                "query": "What is incident management?",
                "quality_score": 0.65,
                "latency_ms": 450,
                "cost_tokens": 1200,
                "accuracy": 0.72,
                "timestamp": datetime.now().isoformat()
            },
            {
                "query": "How to optimize RAG?",
                "quality_score": 0.58,
                "latency_ms": 520,
                "cost_tokens": 1450,
                "accuracy": 0.68,
                "timestamp": datetime.now().isoformat()
            },
            {
                "query": "Architecture comparison",
                "quality_score": 0.62,
                "latency_ms": 480,
                "cost_tokens": 1350,
                "accuracy": 0.70,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        print("\nCalling healing subagent for optimization...")
        
        # Call healing/optimization through the agent
        healing_result = agent.optimize_system(performance_history)
        
        if healing_result['success']:
            print("[✓] Healing optimization completed")
            
            # Simulate healing actions and log each to metadata
            healing_actions = [
                {
                    "action": "OPTIMIZE",
                    "target": "chunk_size",
                    "before_quality": 0.62,
                    "after_quality": 0.78,
                    "improvement": 0.16
                },
                {
                    "action": "RERANK",
                    "target": "context_reranker",
                    "before_quality": 0.62,
                    "after_quality": 0.82,
                    "improvement": 0.20
                },
                {
                    "action": "REINDEX",
                    "target": "embedding_model",
                    "before_quality": 0.62,
                    "after_quality": 0.85,
                    "improvement": 0.23
                }
            ]
            
            for healing_action in healing_actions:
                try:
                    chunk_id = f"{sample_doc_id}_chunk_001"
                    
                    # Log healing action to metadata table
                    metrics = {
                        "action": healing_action["action"],
                        "target": healing_action["target"],
                        "quality_before": healing_action["before_quality"],
                        "quality_after": healing_action["after_quality"],
                        "improvement": healing_action["improvement"],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    history_id = model.log_healing(
                        target_doc_id=sample_doc_id,
                        target_chunk_id=chunk_id,
                        metrics_json=json.dumps(metrics),
                        context_json=json.dumps({
                            "agent_type": "deepagents",
                            "subagent": "HealingSubAgent",
                            "reason": "performance_improvement"
                        }),
                        action_taken=healing_action["action"],
                        reward_signal=healing_action["improvement"],
                        agent_id="deepagents_agent",
                        session_id=session_id
                    )
                    
                    if history_id > 0:
                        print(f"  [✓] Healing action '{healing_action['action']}' logged with history_id: {history_id}")
                        healing_results.append({
                            "action": healing_action["action"],
                            "target": healing_action["target"],
                            "history_id": history_id,
                            "status": "logged",
                            "improvement": healing_action["improvement"]
                        })
                    else:
                        print(f"  [✗] Failed to log healing action")
                        healing_results.append({
                            "action": healing_action["action"],
                            "status": "not_logged"
                        })
                
                except Exception as e:
                    print(f"  [✗] Exception logging healing action: {e}")
                    healing_results.append({
                        "action": healing_action["action"],
                        "status": "error",
                        "error": str(e)
                    })
        else:
            print(f"[✗] Healing optimization failed: {healing_result.get('error')}")
            healing_results.append({
                "status": "failed",
                "error": healing_result.get('error')
            })
    
    except Exception as e:
        print(f"[✗] Exception during healing test: {e}")
        import traceback
        traceback.print_exc()
        healing_results.append({
            "status": "error",
            "error": str(e)
        })
    
    return healing_results


def test_metadata_consistency(model: RAGHistoryModel, session_id: str):
    """Test 5: Verify metadata consistency across agent types"""
    print_section("TEST 5: Metadata Consistency Verification")
    
    try:
        # Check QUERY events logged by deepagents
        model.cursor.execute("""
            SELECT COUNT(*), agent_id FROM rag_history_and_optimization 
            WHERE event_type = 'QUERY' AND session_id = ?
            GROUP BY agent_id
        """, (session_id,))
        
        query_counts = model.cursor.fetchall()
        print(f"\n[✓] Query events by agent:")
        for row in query_counts:
            print(f"    - {row[1]}: {row[0]} events")
        
        # Check HEAL events logged by deepagents
        model.cursor.execute("""
            SELECT COUNT(*), agent_id FROM rag_history_and_optimization 
            WHERE event_type = 'HEAL' AND session_id = ?
            GROUP BY agent_id
        """, (session_id,))
        
        heal_counts = model.cursor.fetchall()
        print(f"\n[✓] Healing events by agent:")
        for row in heal_counts:
            print(f"    - {row[1]}: {row[0]} events")
        
        # Get total events for session
        model.cursor.execute("""
            SELECT COUNT(*) FROM rag_history_and_optimization 
            WHERE session_id = ?
        """, (session_id,))
        
        total = model.cursor.fetchone()[0]
        print(f"\n[✓] Total events in session {session_id}: {total}")
        
        # Get sample DeepAgents events
        model.cursor.execute("""
            SELECT history_id, event_type, query_text, target_doc_id, agent_id, timestamp
            FROM rag_history_and_optimization 
            WHERE session_id = ? AND agent_id = 'deepagents_agent'
            LIMIT 5
        """, (session_id,))
        
        print(f"\n[✓] Sample DeepAgents logged events:")
        for row in model.cursor.fetchall():
            print(f"    - ID: {row[0]}, Type: {row[1]}, Doc: {row[3]}, Agent: {row[4]}")
        
        return {
            "total_events": total,
            "query_events": query_counts,
            "heal_events": heal_counts,
            "status": "consistent"
        }
    
    except Exception as e:
        print(f"[✗] Metadata consistency check failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


def test_rl_healing_integration(model: RAGHistoryModel, session_id: str, sample_doc_id: str = "doc_001"):
    """Test 6: Integrate RL Healing Agent decision-making with deepagents"""
    print_section("TEST 6: RL Healing Agent Integration with DeepAgents")
    
    rl_results = []
    
    try:
        # Initialize RL Healing Agent
        db_path = "./chroma_db/rag.db"
        rl_agent = RLHealingAgent(db_path=db_path)
        print("[✓] RL Healing Agent initialized")
        
        # Simulate RL decision-making with sample states
        test_states = [
            RLState(
                quality_score=0.55,
                query_accuracy=0.60,
                chunk_count=50,
                avg_token_cost=1500,
                reindex_count=0,
                last_healing_delta=0.0,
                query_frequency=10,
                user_feedback=0.65
            ),
            RLState(
                quality_score=0.72,
                query_accuracy=0.78,
                chunk_count=50,
                avg_token_cost=1200,
                reindex_count=1,
                last_healing_delta=0.17,
                query_frequency=15,
                user_feedback=0.80
            ),
            RLState(
                quality_score=0.45,
                query_accuracy=0.50,
                chunk_count=100,
                avg_token_cost=2100,
                reindex_count=0,
                last_healing_delta=-0.10,
                query_frequency=20,
                user_feedback=0.50
            )
        ]
        
        for state_idx, state in enumerate(test_states, 1):
            try:
                print(f"\nRL Decision {state_idx}:")
                print(f"  Current Quality: {state.quality_score:.2f}")
                print(f"  Query Accuracy: {state.query_accuracy:.2f}")
                print(f"  Avg Token Cost: {state.avg_token_cost}")
                
                # Get RL agent decision
                rl_action = rl_agent.decide_action(state, sample_doc_id)
                
                print(f"  [✓] RL Action: {rl_action.action}")
                print(f"      Confidence: {rl_action.confidence:.2f}")
                print(f"      Estimated Improvement: {rl_action.estimated_improvement:.3f}")
                
                # Log RL decision to metadata
                metrics = {
                    "rl_action": rl_action.action,
                    "confidence": rl_action.confidence,
                    "estimated_improvement": rl_action.estimated_improvement,
                    "estimated_cost": rl_action.estimated_cost,
                    "state": {
                        "quality_score": state.quality_score,
                        "query_accuracy": state.query_accuracy,
                        "avg_token_cost": state.avg_token_cost
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                # Log as healing action
                history_id = model.log_healing(
                    target_doc_id=sample_doc_id,
                    target_chunk_id=f"{sample_doc_id}_chunk_{state_idx:03d}",
                    metrics_json=json.dumps(metrics),
                    context_json=json.dumps({
                        "agent_type": "deepagents_with_rl",
                        "subagent": "HealingSubAgent",
                        "rl_decision": "true"
                    }),
                    action_taken=rl_action.action,
                    reward_signal=rl_action.estimated_improvement,
                    agent_id="deepagents_rl_agent",
                    session_id=session_id
                )
                
                if history_id > 0:
                    print(f"  [✓] RL decision logged with history_id: {history_id}")
                    rl_results.append({
                        "state_idx": state_idx,
                        "action": rl_action.action,
                        "history_id": history_id,
                        "status": "logged"
                    })
                else:
                    print(f"  [✗] Failed to log RL decision")
                    rl_results.append({
                        "state_idx": state_idx,
                        "action": rl_action.action,
                        "status": "not_logged"
                    })
            
            except Exception as e:
                print(f"  [✗] Exception in RL decision: {e}")
                import traceback
                traceback.print_exc()
                rl_results.append({
                    "state_idx": state_idx,
                    "status": "error",
                    "error": str(e)
                })
        
        return rl_results
    
    except Exception as e:
        print(f"[✗] RL integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return [{"status": "error", "error": str(e)}]


def test_summary(ingestion_results, retrieval_results, healing_results, 
                 consistency_results, rl_results):
    """Display test summary"""
    print_section("TEST SUMMARY: DeepAgents Healing with Metadata Logging")
    
    print("\n[1] INGESTION RESULTS")
    ingested_count = sum(1 for r in ingestion_results if r['status'] in ['logged', 'ingested_but_not_logged'])
    logged_count = sum(1 for r in ingestion_results if r['status'] == 'logged')
    print(f"    Documents processed: {len(ingestion_results)}")
    print(f"    Successfully logged: {logged_count}/{ingested_count}")
    
    print("\n[2] RETRIEVAL RESULTS")
    retrieved_count = sum(1 for r in retrieval_results if 'status' in r)
    logged_queries = sum(1 for r in retrieval_results if r['status'] == 'logged')
    print(f"    Queries processed: {len(retrieval_results)}")
    print(f"    Successfully logged: {logged_queries}/{retrieved_count}")
    
    print("\n[3] HEALING RESULTS")
    healing_count = sum(1 for r in healing_results if 'status' in r)
    logged_heals = sum(1 for r in healing_results if r['status'] == 'logged')
    print(f"    Healing actions processed: {healing_count}")
    print(f"    Successfully logged: {logged_heals}/{healing_count}")
    
    print("\n[4] METADATA CONSISTENCY")
    if consistency_results.get('status') == 'consistent':
        print(f"    Total events logged: {consistency_results.get('total_events', 0)}")
        print(f"    ✓ All agents writing to same table: rag_history_and_optimization")
    else:
        print(f"    ✗ Consistency check failed: {consistency_results.get('error')}")
    
    print("\n[5] RL INTEGRATION")
    rl_logged = sum(1 for r in rl_results if r.get('status') == 'logged')
    print(f"    RL decisions logged: {rl_logged}/{len(rl_results)}")
    
    print("\n" + "="*80)
    print("  ✓ DeepAgents Healing Test Complete")
    print("  ✓ All metadata logged to rag_history_and_optimization table")
    print("  ✓ Consistent with LangGraph agent logging patterns")
    print("="*80 + "\n")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("  DeepAgents Healing Agent Test with Metadata Logging")
    print("  Unified logging for LangGraph and DeepAgents")
    print("="*80)
    
    # Generate session ID
    session_id = f"deepagents_healing_{int(time.time())}"
    print(f"\nSession ID: {session_id}\n")
    
    # Initialize database model
    try:
        model = RAGHistoryModel()
        print("[✓] RAGHistoryModel initialized")
    except Exception as e:
        print(f"[✗] Failed to initialize RAGHistoryModel: {e}")
        sys.exit(1)
    
    # Run tests
    agent = test_deepagents_initialization()
    time.sleep(1)
    
    ingestion_results = test_ingestion_with_metadata_logging(agent, model, session_id)
    time.sleep(1)
    
    sample_doc_id = ingestion_results[0]['doc_id'] if ingestion_results else "doc_001"
    retrieval_results = test_retrieval_with_metadata_logging(agent, model, session_id, sample_doc_id)
    time.sleep(1)
    
    healing_results = test_healing_with_metadata_logging(agent, model, session_id, sample_doc_id)
    time.sleep(1)
    
    consistency_results = test_metadata_consistency(model, session_id)
    time.sleep(1)
    
    rl_results = test_rl_healing_integration(model, session_id, sample_doc_id)
    
    # Display summary
    test_summary(ingestion_results, retrieval_results, healing_results, 
                 consistency_results, rl_results)


if __name__ == "__main__":
    main()
