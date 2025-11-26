"""
Test Script: DeepAgents SubAgent-based RAG

Tests the DeepAgents SubAgent orchestration with modular subagents.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from incident_iq.rag.agents.deepagents_agent import DeepAgentsRAGAgent


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"🤖 {title}")
    print("=" * 80)


def test_ingestion():
    """Test DeepAgents ingestion subagent."""
    print_header("DeepAgents Test 1: IngestionSubAgent")
    
    try:
        agent = DeepAgentsRAGAgent()
        
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
        
        print("📝 Ingesting document via IngestionSubAgent...")
        result = agent.ingest_document(document, "deepagents_doc_001")
        
        print(f"✅ Status: {'Success' if result['success'] else 'Failed'}")
        print(f"   Doc ID: {result['doc_id']}")
        if result.get('error'):
            print(f"   Error: {result['error']}")
        else:
            print(f"   Result: {json.dumps(result.get('result', {}), indent=2)[:200]}...")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retrieval():
    """Test DeepAgents retrieval subagent."""
    print_header("DeepAgents Test 2: RetrievalSubAgent")
    
    try:
        agent = DeepAgentsRAGAgent()
        
        questions = [
            "What are the incident severity levels?",
            "What is the incident workflow?"
        ]
        
        for question in questions:
            print(f"\n❓ Question: {question}")
            result = agent.ask_question(question)
            
            print(f"✅ Status: {'Success' if result['success'] else 'Failed'}")
            if result.get('error'):
                print(f"   Error: {result['error']}")
            else:
                print(f"   Result: {json.dumps(result.get('result', {}), indent=2)[:200]}...")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


def test_healing():
    """Test DeepAgents healing subagent."""
    print_header("DeepAgents Test 3: HealingSubAgent")
    
    try:
        agent = DeepAgentsRAGAgent()
        
        performance_history = [
            {"params": {"k": 5}, "metrics": {"accuracy": 0.82, "cost": 0.001}},
            {"params": {"k": 4}, "metrics": {"accuracy": 0.85, "cost": 0.0009}},
        ]
        
        print("📊 Running optimization via HealingSubAgent...")
        result = agent.optimize_system(performance_history)
        
        print(f"✅ Status: {'Success' if result['success'] else 'Failed'}")
        if result.get('error'):
            print(f"   Error: {result['error']}")
        else:
            print(f"   Result: {json.dumps(result.get('result', {}), indent=2)[:200]}...")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


def test_config():
    """Test DeepAgents config subagent."""
    print_header("DeepAgents Test 4: ConfigSubAgent")
    
    try:
        agent = DeepAgentsRAGAgent()
        
        updates = {"RAG_K_FINAL": 4, "LLM_TEMPERATURE": 0.3}
        
        print("🔧 Adjusting config via ConfigSubAgent...")
        result = agent.adjust_config(updates)
        
        print(f"✅ Status: {'Success' if result['success'] else 'Failed'}")
        if result.get('error'):
            print(f"   Error: {result['error']}")
        else:
            print(f"   Result: {json.dumps(result.get('result', {}), indent=2)[:200]}...")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🤖 DEEPAGENTS RAG AGENT - SUBAGENT TESTS")
    print("=" * 80)
    
    test_ingestion()
    test_retrieval()
    test_healing()
    test_config()
    
    print("\n" + "=" * 80)
    print("✅ DEEPAGENTS TESTS COMPLETED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
