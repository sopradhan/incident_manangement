"""
Test Script: Autonomous RAG Agent - Document Ingestion & Retrieval

This script demonstrates the complete workflow:
1. Ingest a document
2. Ask questions with full traceability
3. Optimize and adjust config
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from incident_iq.rag.agent.autonomous_rag_agent import AutonomousRAGAgent

def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"🤖 {title}")
    print("=" * 80)

def print_result(data, title="Result"):
    """Print formatted result."""
    print(f"\n✅ {title}:")
    print(json.dumps(data, indent=2))

def test_ingestion():
    """Test document ingestion."""
    print_header("TEST 1: Document Ingestion")
    
    try:
        agent = AutonomousRAGAgent()
        
        # Sample document about incident management
        document = """
Incident Management Best Practices

An incident is any unplanned interruption or reduction in the quality of a service.

## Incident Classification

Incidents are classified by severity:
- Critical (Sev 1): Complete service outage, revenue impact
- High (Sev 2): Major functionality impaired, significant impact
- Medium (Sev 3): Minor functionality affected, workaround available
- Low (Sev 4): Cosmetic issues, minimal user impact

## Incident Lifecycle

1. Detection: An issue is identified
2. Logging: The incident is recorded in the system
3. Categorization: The incident is classified by type and severity
4. Initial Response: The support team initiates troubleshooting
5. Resolution: The root cause is addressed and fixed
6. Closure: The incident is closed and documented
7. Post-Incident Review: Analysis and lessons learned

## Response Time Targets (SLA)

- Critical: Initial response within 15 minutes, resolution within 4 hours
- High: Initial response within 30 minutes, resolution within 8 hours
- Medium: Initial response within 2 hours, resolution within 24 hours
- Low: Initial response within 8 hours, resolution within 72 hours

## Best Practices

1. Maintain clear communication with stakeholders
2. Document all troubleshooting steps
3. Escalate appropriately when needed
4. Follow the change management process for fixes
5. Conduct thorough post-incident reviews
6. Use monitoring and alerting to detect issues early
7. Maintain a knowledge base of common issues and resolutions
        """
        
        print("📝 Document to ingest:")
        print(document[:200] + "...")
        
        result = agent.ingest_document(
            text=document,
            doc_id="incident_mgmt_doc_001",
            rbac_namespace="general"
        )
        
        print_result(result, "Ingestion Result")
        
        if result.get("success"):
            print(f"\n✓ Document successfully ingested!")
            print(f"  - Chunks created: {result.get('chunks_count', 0)}")
            print(f"  - Chunks saved to VectorDB: {result.get('chunks_saved', 0)}")
            return True
        else:
            print(f"✗ Ingestion failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"✗ Ingestion exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_retrieval(ingestion_success):
    """Test question answering with traceability."""
    print_header("TEST 2: Question Answering with Traceability")
    
    if not ingestion_success:
        print("⚠️  Skipping retrieval test (no documents ingested)")
        return
    
    try:
        agent = AutonomousRAGAgent()
        
        questions = [
            "What is the response time target for critical incidents?",
            "What are the stages of the incident lifecycle?",
            "How are incidents classified?"
        ]
        
        for question in questions:
            print(f"\n❓ Question: {question}")
            
            result = agent.ask_question(
                question=question,
                rbac_namespace="general"
            )
            
            if result.get("success"):
                print(f"✅ Answer: {result.get('answer')}")
                
                # Show traceability
                trace = result.get('traceability', {})
                if trace:
                    if isinstance(trace, str):
                        trace = json.loads(trace)
                    print(f"\n📍 Traceability:")
                    print(f"   - Question: {trace.get('question')}")
                    print(f"   - Top-K results: {trace.get('top_k', 0)}")
                    
                    sources = trace.get('sources', [])
                    if sources:
                        for i, src in enumerate(sources, 1):
                            print(f"   - Source {i}: {src.get('doc_id')} (Score: {src.get('similarity_score', 'N/A')})")
                            print(f"     Preview: {src.get('text_preview', 'N/A')[:100]}")
            else:
                print(f"✗ Failed to answer: {result.get('error')}")
                
    except Exception as e:
        print(f"✗ Retrieval test exception: {e}")
        import traceback
        traceback.print_exc()

def test_optimization():
    """Test optimization functionality."""
    print_header("TEST 3: System Optimization")
    
    try:
        agent = AutonomousRAGAgent()
        
        # Sample performance history
        performance_history = [
            {
                "timestamp": "2025-11-26T10:00:00",
                "params": {"k_final": 5, "chunk_size": 512},
                "metrics": {"accuracy": 0.82, "latency_ms": 245, "cost_usd": 0.0012}
            },
            {
                "timestamp": "2025-11-26T11:00:00",
                "params": {"k_final": 5, "chunk_size": 512},
                "metrics": {"accuracy": 0.85, "latency_ms": 238, "cost_usd": 0.0011}
            },
            {
                "timestamp": "2025-11-26T12:00:00",
                "params": {"k_final": 4, "chunk_size": 512},
                "metrics": {"accuracy": 0.87, "latency_ms": 210, "cost_usd": 0.0009}
            }
        ]
        
        print("📊 Performance History:")
        for entry in performance_history:
            print(f"  - {entry['timestamp']}: Accuracy={entry['metrics']['accuracy']}, Cost=${entry['metrics']['cost_usd']}")
        
        result = agent.optimize(performance_history)
        print_result(result, "Optimization Result")
        
    except Exception as e:
        print(f"✗ Optimization test exception: {e}")
        import traceback
        traceback.print_exc()

def test_config_adjustment():
    """Test configuration adjustment."""
    print_header("TEST 4: Config Adjustment")
    
    try:
        agent = AutonomousRAGAgent()
        
        updates = {
            "RAG_K_FINAL": 4,
            "RAG_CHUNK_SIZE": 512,
            "LLM_TEMPERATURE": 0.3
        }
        
        print("🔧 Config updates to apply:")
        for key, value in updates.items():
            print(f"  - {key}: {value}")
        
        result = agent.adjust_config(updates)
        print_result(result, "Config Adjustment Result")
        
    except Exception as e:
        print(f"✗ Config adjustment test exception: {e}")
        import traceback
        traceback.print_exc()

def test_health_check():
    """Test embedding health check."""
    print_header("TEST 5: Embedding Health Check")
    
    try:
        agent = AutonomousRAGAgent()
        
        # Sample embeddings
        embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.11, 0.21, 0.31, 0.41, 0.51],
            [0.12, 0.22, 0.32, 0.42, 0.52],
        ]
        
        result = agent.check_health(embeddings, "doc_001")
        print_result(result, "Health Check Result")
        
    except Exception as e:
        print(f"✗ Health check exception: {e}")
        import traceback
        traceback.print_exc()

def test_cost_estimation():
    """Test cost estimation."""
    print_header("TEST 6: Cost Estimation")
    
    try:
        agent = AutonomousRAGAgent()
        
        context = [
            {"doc_id": "doc_001", "text": "This is a sample context chunk about incident management."},
            {"doc_id": "doc_002", "text": "Another context chunk with more details about procedures."}
        ]
        
        result = agent.estimate_cost(context)
        print_result(result, "Cost Estimation Result")
        
    except Exception as e:
        print(f"✗ Cost estimation exception: {e}")
        import traceback
        traceback.print_exc()

def test_agent_memory():
    """Test agent memory recording."""
    print_header("TEST 7: Agent Memory Recording")
    
    try:
        agent = AutonomousRAGAgent()
        
        result = agent.record_memory(
            agent_name="RetrievalAgent",
            memory_key="query_001",
            memory_value="User asked about incident response procedures. Retrieved 5 relevant documents.",
            memory_type="context"
        )
        print_result(result, "Memory Recording Result")
        
    except Exception as e:
        print(f"✗ Memory recording exception: {e}")
        import traceback
        traceback.print_exc()
    """Test configuration adjustment."""
    print_header("TEST 4: Config Adjustment")
    
    try:
        agent = AutonomousRAGAgent()
        
        updates = {
            "RAG_K_FINAL": 4,
            "RAG_CHUNK_SIZE": 512,
            "LLM_TEMPERATURE": 0.3
        }
        
        print("🔧 Config updates to apply:")
        for key, value in updates.items():
            print(f"  - {key}: {value}")
        
        result = agent.adjust_config(updates)
        print_result(result, "Config Adjustment Result")
        
    except Exception as e:
        print(f"✗ Config adjustment test exception: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🤖 AUTONOMOUS RAG AGENT - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    try:
        # Test 1: Ingestion
        ingestion_success = test_ingestion()
        
        # Test 2: Retrieval (depends on ingestion)
        test_retrieval(ingestion_success)
        
        # Test 3: Optimization
        test_optimization()
        
        # Test 4: Config
        test_config_adjustment()
        
        # Test 5: Health Check
        test_health_check()
        
        # Test 6: Cost Estimation
        test_cost_estimation()
        
        # Test 7: Agent Memory
        test_agent_memory()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
