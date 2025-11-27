#!/usr/bin/env python3
"""
Final test: Agent with table ingestion and question asking
Tests: LangGraphRAGAgent.invoke() with real workflow
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent

def main():
    print("\n" + "="*80)
    print("TESTING LangGraphRAGAgent WITH TABLE INGESTION & QUESTION ASKING")
    print("="*80 + "\n")
    
    # Initialize agent
    print("[1] Initializing LangGraphRAGAgent...")
    agent = LangGraphRAGAgent()
    print("[OK] Agent initialized\n")
    
    # Test 1: Ingest sample data as a table
    print("[2] Testing table ingestion...")
    
    try:
        result = agent.invoke(
            operation="ingest_sqlite_table",
            table_name="knowledge_base",
            doc_id="sqlite_knowledge_base",
            rbac_namespace="general",
            response_mode="verbose"
        )
        print("[OK] Table ingestion completed")
        print(json.dumps(result, indent=2) + "\n")
    except Exception as e:
        import traceback
        print("[ERROR] Table ingestion failed: " + str(e))
        traceback.print_exc()
        return False
    
    # Test 2: Ask a question about the ingested data
    print("[3] Testing question answering on ingested data...")
    
    questions = [
        "What are the critical severity incidents?",
        "How many incidents are currently open?",
        "List all incidents with their severity levels",
    ]
    
    for question in questions:
        print("   Q: " + question)
        try:
            result = agent.invoke(
                operation="ask_question",
                question=question,
                response_mode="concise"  # Concise mode = no tool details
            )
            answer = result.get('answer', 'No answer')
            print("   A: " + answer[:100] + "...\n")
        except Exception as e:
            print("   [ERROR] " + str(e) + "\n")
            return False
    
    print("[4] Testing verbose mode (shows tool details)...")
    try:
        result = agent.invoke(
            operation="ask_question",
            question="What is the status of incident 2?",
            response_mode="verbose"  # Verbose = shows all tool details
        )
        answer = result.get('answer', 'No answer')
        print("[OK] Answer: " + answer[:80] + "...")
        if "tool_usage" in result:
            print("  Tools used: " + str(result['tool_usage']) + "\n")
    except Exception as e:
        print("[ERROR] " + str(e) + "\n")
        return False
    
    print("="*80)
    print("ALL TESTS PASSED")
    print("="*80)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
