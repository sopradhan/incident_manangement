#!/usr/bin/env python
"""
SIMPLE DeepAgents Test - Focus on Core Functionality
- Ingest documents
- Ask questions
- Run healing optimization
- Print task report

No complex config managers - just the essentials.
"""

import sys
import json
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.incident_iq.rag.agents.deepagents_agent.deepagents_rag_agent import DeepAgentsRAGAgent
from src.incident_iq.database.models.rag_history_model import RAGHistoryModel
from src.incident_iq.rag.agents.healing_agent.rl_healing_agent import RLHealingAgent, RLState


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_response(data: Any, indent: int = 0):
    """Recursively print response data"""
    prefix = " " * indent
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}{key}:")
                print_response(value, indent + 2)
            else:
                val_str = str(value)[:100]
                print(f"{prefix}{key}: {val_str}")
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            print(f"{prefix}[{idx}]:")
            print_response(item, indent + 2)
    else:
        print(f"{prefix}{str(data)[:100]}")


def test_simple_flow():
    """Run simple test: ingest -> ask -> optimize -> report"""
    
    print_section("INITIALIZING DEEPAGENTS RAG AGENT")
    
    # Initialize agent
    agent = DeepAgentsRAGAgent()
    print("[OK] Agent initialized")
    
    # Initialize RL healing agent
    rl_agent = RLHealingAgent()
    print("[OK] RL Healing Agent initialized")
    
    # Initialize database
    db = RAGHistoryModel()
    print("[OK] Database initialized")
    
    # ============ STEP 1: DOCUMENT INGESTION ============
    print_section("STEP 1: DOCUMENT INGESTION")
    
    test_doc = """
    INCIDENT MANAGEMENT BEST PRACTICES
    
    1. DETECTION: Monitor systems continuously to identify incidents early
    2. CLASSIFICATION: Categorize by severity (Critical, High, Medium, Low)
    3. RESPONSE: Activate response team based on severity level
    4. INVESTIGATION: Root cause analysis and impact assessment
    5. RESOLUTION: Implement fix and verify stability
    6. COMMUNICATION: Notify stakeholders throughout process
    7. DOCUMENTATION: Record all actions and lessons learned
    8. PREVENTION: Use insights to prevent similar incidents
    """
    
    print("Ingesting test document...")
    ingest_result = agent.ingest_document(
        text=test_doc,
        doc_id="incident_practices_001"
    )
    
    print(f"\nIngestion Status: {ingest_result.get('success')}")
    print(f"Execution Time: {ingest_result.get('execution_time_ms'):.1f}ms")
    
    if ingest_result.get('success'):
        print("[OK] Document ingested successfully")
    else:
        print(f"[ERROR] Ingestion failed: {ingest_result.get('error')}")
    
    # ============ STEP 2: QUESTION ANSWERING ============
    print_section("STEP 2: QUESTION ANSWERING")
    
    questions = [
        "What are the key steps in incident management?",
        "How should incidents be classified?"
    ]
    
    for question in questions:
        print(f"Q: {question}\n")
        
        qa_result = agent.ask_question(question)
        
        print(f"Status: {qa_result.get('success')}")
        print(f"Execution Time: {qa_result.get('execution_time_ms'):.1f}ms")
        
        if qa_result.get('success'):
            result_data = qa_result.get('result', {})
            answer = result_data.get('answer', 'No answer available')
            print(f"\nAnswer:\n{answer}\n")
            print("[OK] Question answered")
        else:
            print(f"[ERROR] Query failed: {qa_result.get('error')}")
        
        print("-" * 80)
    
    # ============ STEP 3: HEALING OPTIMIZATION ============
    print_section("STEP 3: HEALING OPTIMIZATION")
    
    # Create performance history for optimization
    performance_history = [
        {
            "query": "incident management steps",
            "latency_ms": 250,
            "quality_score": 0.85,
            "tokens_used": 500,
            "cost_usd": 0.002
        },
        {
            "query": "incident classification",
            "latency_ms": 180,
            "quality_score": 0.92,
            "tokens_used": 420,
            "cost_usd": 0.0015
        }
    ]
    
    print("Running system optimization...")
    optimize_result = agent.optimize_system(performance_history)
    
    print(f"\nOptimization Status: {optimize_result.get('success')}")
    print(f"Execution Time: {optimize_result.get('execution_time_ms'):.1f}ms")
    
    if optimize_result.get('success'):
        print("[OK] System optimization completed")
        result = optimize_result.get('result')
        if result:
            print(f"\nOptimization Result:\n{result}\n")
    else:
        print(f"[ERROR] Optimization failed: {optimize_result.get('error')}")
    
    # ============ STEP 4: TASK REPORT ============
    print_section("STEP 4: TASK EXECUTION REPORT")
    
    # Print task report
    agent.print_task_report()
    
    # Export task data
    exported_tasks = agent.export_tasks()
    print("\nExported Tasks (JSON):")
    print(exported_tasks)
    
    print_section("TEST COMPLETE")
    print("[OK] Simple DeepAgents test finished successfully")


if __name__ == "__main__":
    try:
        test_simple_flow()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
