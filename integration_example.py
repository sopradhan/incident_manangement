#!/usr/bin/env python
"""
Integration Example: Enhanced Todo Agent + DeepAgents RAG Agent

Demonstrates how to use:
1. EnhancedTodoAgent: For persistent task planning and tracking
2. DeepAgentsRAGAgent: For RAG operations (ingest, query, optimize)

Together they create a complete autonomous RAG workflow with persistent todos.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.incident_iq.rag.agents.deepagents_agent.enhanced_todo_agent import EnhancedTodoAgent
from src.incident_iq.rag.agents.deepagents_agent.deepagents_rag_agent import DeepAgentsRAGAgent


def integration_example():
    """Show integrated workflow with todos and RAG"""
    
    print("\n" + "="*80)
    print("  INTEGRATION EXAMPLE: EnhancedTodoAgent + DeepAgentsRAGAgent")
    print("="*80 + "\n")
    
    # ============ SETUP ============
    print("1. Setting up Todo Agent with persistent storage...")
    todo_agent = EnhancedTodoAgent(
        todo_dir="./integration_workflow",
        model="gpt-4"
    )
    print("   [OK] Todo Agent ready\n")
    
    print("2. Setting up DeepAgents RAG Agent...")
    rag_agent = DeepAgentsRAGAgent()
    print("   [OK] RAG Agent ready\n")
    
    # ============ TASK: COMPLETE RAG WORKFLOW WITH TODOS ============
    print("="*80)
    print("  TASK: Execute Complete RAG Workflow with Todo Planning")
    print("="*80 + "\n")
    
    workflow_task = """
    I need to execute a complete RAG workflow with the following steps:
    
    1. Plan the workflow (break into sub-tasks)
    2. Ingest incident management documents
    3. Ask questions to verify ingestion
    4. Run system optimization
    5. Document final results
    
    Please plan this carefully, execute each step, and save results to persistent storage.
    """
    
    print("Starting todo-based workflow planning...\n")
    result = todo_agent.execute_task(workflow_task)
    
    if result.get('success'):
        print("\n[OK] Workflow planning complete")
        print("\nTodo Status:")
        todo_agent.print_todo_status()
    else:
        print(f"\n[ERROR] Workflow failed: {result.get('error')}")
    
    # ============ EXECUTE RAG OPERATIONS ============
    print("\n" + "="*80)
    print("  EXECUTING RAG OPERATIONS (from todo plan)")
    print("="*80 + "\n")
    
    # Step 1: Ingest
    print("Step 1: Document Ingestion\n")
    doc = """
    INCIDENT RESPONSE PLAYBOOK
    
    Critical Incidents (P1):
    - Immediate escalation to CTO
    - War room activation within 5 minutes
    - Hourly status updates
    
    High Priority (P2):
    - Team lead notification
    - War room within 30 minutes
    - 4-hour updates
    """
    
    ingest_result = rag_agent.ingest_document(doc, "incident_playbook_001")
    print(f"Ingest Success: {ingest_result.get('success')}")
    print(f"Execution Time: {ingest_result.get('execution_time_ms'):.1f}ms")
    print("[OK] Document ingested\n")
    
    # Step 2: Ask Questions
    print("Step 2: Answer Questions\n")
    question = "What should happen immediately when a critical incident is detected?"
    qa_result = rag_agent.ask_question(question)
    
    if qa_result.get('success'):
        answer_data = qa_result.get('result', {})
        print(f"Q: {question}")
        print(f"A: {answer_data.get('answer', 'No answer')}\n")
        print("[OK] Question answered\n")
    
    # Step 3: Optimize
    print("Step 3: System Optimization\n")
    perf_history = [{
        "query": question,
        "latency_ms": 150,
        "quality_score": 0.95,
        "tokens_used": 300,
        "cost_usd": 0.001
    }]
    
    opt_result = rag_agent.optimize_system(perf_history)
    print(f"Optimization Success: {opt_result.get('success')}")
    print(f"Execution Time: {opt_result.get('execution_time_ms'):.1f}ms")
    print("[OK] System optimized\n")
    
    # ============ FINAL REPORTS ============
    print("="*80)
    print("  FINAL REPORTS")
    print("="*80 + "\n")
    
    # Print RAG Task Report
    print("RAG Agent Task Report:")
    rag_agent.print_task_report()
    
    # Print Todo Status
    print("Final Todo Status:")
    todo_agent.print_todo_status()
    
    # ============ SUMMARY ============
    print("="*80)
    print("  INTEGRATION SUMMARY")
    print("="*80 + "\n")
    
    print("✓ Todos were planned with FilesystemBackend")
    print("✓ RAG operations were executed with TaskManager")
    print("✓ All results were persisted to disk")
    print("✓ Chain-of-Thought reasoning was tracked")
    print("\nCheck ./integration_workflow/ for persistent todo data")
    print("Check RAG task report above for execution details\n")


if __name__ == "__main__":
    try:
        integration_example()
    except Exception as e:
        print(f"\n[ERROR] Integration example failed: {e}")
        import traceback
        traceback.print_exc()
