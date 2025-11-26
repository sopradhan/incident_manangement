"""
Test Script: LangGraph-based RAG Agent

Tests the LangGraph workflow orchestration with nodes and edges.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"🤖 {title}")
    print("=" * 80)


def test_ingestion():
    """Test LangGraph ingestion workflow."""
    print_header("LangGraph Test 1: Document Ingestion Workflow")
    
    try:
        agent = LangGraphRAGAgent()
        
        document = """
Incident Management Process

An incident is any unplanned interruption to a service.

## Classification
- Critical: Complete outage
- High: Major impact
- Medium: Minor impact
- Low: Cosmetic

## Workflow
1. Detection
2. Logging
3. Investigation
4. Resolution
5. Closure
"""
        
        print("📝 Ingesting document through LangGraph workflow...")
        result = agent.ingest_document(document, "langgraph_doc_001")
        
        print(f"✅ Status: {'Success' if result['success'] else 'Failed'}")
        print(f"   Doc ID: {result['doc_id']}")
        print(f"   Chunks: {result.get('chunks_count', 0)}")
        print(f"   Saved: {result.get('chunks_saved', 0)}")
        if result.get('errors'):
            print(f"   Errors: {result['errors']}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retrieval():
    """Test LangGraph retrieval workflow."""
    print_header("LangGraph Test 2: Retrieval Workflow with Traceability")
    
    try:
        agent = LangGraphRAGAgent()
        
        questions = [
            "What are the incident severity levels?",
            "What is the incident workflow?"
        ]
        
        for question in questions:
            print(f"\n❓ Question: {question}")
            result = agent.ask_question(question)
            
            print(f"✅ Status: {'Success' if result['success'] else 'Failed'}")
            print(f"   Answer: {result.get('answer', 'N/A')[:100]}...")
            print(f"   Sources: {len(result.get('sources', []))} documents")
            if result.get('errors'):
                print(f"   Errors: {result['errors']}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


def test_optimization():
    """Test LangGraph optimization workflow."""
    print_header("LangGraph Test 3: Optimization Workflow")
    
    try:
        agent = LangGraphRAGAgent()
        
        performance_history = [
            {"params": {"k": 5}, "metrics": {"accuracy": 0.82, "cost": 0.001}},
            {"params": {"k": 4}, "metrics": {"accuracy": 0.85, "cost": 0.0009}},
        ]
        config_updates = {"RAG_K_FINAL": 4}
        
        print("📊 Running optimization workflow...")
        result = agent.optimize_system(performance_history, config_updates)
        
        print(f"✅ Status: {'Success' if result['success'] else 'Failed'}")
        if result.get('errors'):
            print(f"   Errors: {result['errors']}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🤖 LANGGRAPH RAG AGENT - WORKFLOW TESTS")
    print("=" * 80)
    
    ingestion_ok = test_ingestion()
    test_retrieval()
    test_optimization()
    
    print("\n" + "=" * 80)
    print("✅ LANGGRAPH TESTS COMPLETED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
