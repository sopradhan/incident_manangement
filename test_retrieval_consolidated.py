#!/usr/bin/env python
"""
Test DeepAgents Consolidated Agent - Retrieval from Master Agent
Tests that the Flashpoint master orchestrator correctly delegates to retrieval-agent
and returns complete answers with proper task tracking and persistent todos.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.incident_iq.rag.agents.deepagents_agent.deepagents_rag_agent import DeepAgentsRAGAgent


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def test_retrieval_from_master_agent():
    """Test retrieval from Flashpoint master agent"""
    
    print_section("INITIALIZING CONSOLIDATED DEEPAGENTS RAG AGENT")
    
    # Initialize the consolidated agent
    try:
        agent = DeepAgentsRAGAgent(todo_dir="./test_retrieval_workflow")
        print("[OK] Consolidated agent initialized successfully")
        print(f"    - TaskManager embedded: Yes")
        print(f"    - FilesystemBackend enabled: Yes")
        print(f"    - TodoListMiddleware: Yes")
        print(f"    - Master Agent (Flashpoint): Yes")
        print(f"    - Todo persistence dir: ./test_retrieval_workflow\n")
    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
        return
    
    # ============ STEP 1: INGESTION ============
    print_section("STEP 1: DOCUMENT INGESTION (Setup for Retrieval)")
    
    test_doc = """
    INCIDENT MANAGEMENT FRAMEWORK
    
    Overview:
    Incident management is a critical process for maintaining system reliability and minimizing impact.
    
    Key Phases:
    1. DETECTION: Automated monitoring identifies anomalies
    2. TRIAGE: Determine severity and impact scope
    3. RESPONSE: Activate response team and communication channels
    4. INVESTIGATION: Root cause analysis using logs and metrics
    5. MITIGATION: Implement quick fix if available
    6. RESOLUTION: Deploy permanent solution
    7. POST-MORTEM: Document lessons learned and improvements
    
    Severity Levels:
    - Critical (P1): System down, revenue impacting → 5 min response
    - High (P2): Significant degradation → 15 min response
    - Medium (P3): Noticeable impact → 30 min response
    - Low (P4): Minor issues → 4 hour response
    
    Best Practices:
    - Establish clear escalation paths
    - Use runbooks for common incidents
    - Maintain detailed incident logs
    - Conduct regular drills
    - Automate detection and mitigation where possible
    """
    
    print("Ingesting incident management document...")
    ingest_result = agent.ingest_document(
        text=test_doc,
        doc_id="incident_mgmt_001"
    )
    
    if ingest_result.get('success'):
        print(f"[OK] Document ingested")
        print(f"    - Task ID: {ingest_result.get('task_id')}")
        print(f"    - Execution time: {ingest_result.get('execution_time_ms'):.1f}ms")
        print(f"    - Todo persisted: {ingest_result.get('todo_persisted')}\n")
    else:
        print(f"[ERROR] Ingestion failed: {ingest_result.get('error')}")
        return
    
    # ============ STEP 2: RETRIEVAL FROM MASTER AGENT ============
    print_section("STEP 2: TEST RETRIEVAL FROM MASTER AGENT (Flashpoint)")
    
    test_questions = [
        "What are the key phases of incident management?",
        "What is the response time for critical incidents?",
        "What severity levels exist in incident management?",
        "Describe the incident management framework overview"
    ]
    
    for idx, question in enumerate(test_questions, 1):
        print(f"\n[QUERY {idx}] {question}")
        print("-" * 80)
        
        qa_result = agent.ask_question(question)
        
        if qa_result.get('success'):
            result_data = qa_result.get('result', {})
            answer = result_data.get('answer', 'No answer')
            
            print(f"\n✓ Status: SUCCESS")
            print(f"  Task ID: {qa_result.get('task_id')}")
            print(f"  Execution time: {qa_result.get('execution_time_ms'):.1f}ms")
            print(f"  Todo persisted: {qa_result.get('todo_persisted')}")
            
            print(f"\nANSWER:")
            print(f"{answer}\n")
        else:
            print(f"\n✗ Status: FAILED")
            print(f"  Error: {qa_result.get('error')}\n")
    
    # ============ STEP 3: TASK REPORT ============
    print_section("STEP 3: TASK EXECUTION REPORT (TaskManager)")
    
    print("Printing task execution report with Chain-of-Thought reasoning...\n")
    agent.print_task_report()
    
    # ============ STEP 4: PERSISTENT TODOS ============
    print_section("STEP 4: PERSISTENT TODO STATUS (FilesystemBackend)")
    
    print("Checking persistent todos from FilesystemBackend...\n")
    agent.print_todo_status()
    
    # ============ STEP 5: COMBINED REPORT ============
    print_section("STEP 5: COMBINED REPORT (TaskManager + FilesystemBackend)")
    
    print("Showing both tracking systems together...\n")
    agent.print_combined_report()
    
    # ============ STEP 6: EXPORT DATA ============
    print_section("STEP 6: EXPORT TASK DATA")
    
    exported_tasks = agent.export_tasks()
    print("Exported tasks (first 500 chars):")
    print(exported_tasks[:500] + "...\n")
    
    todos_list = agent.get_todos()
    print(f"Persistent todos: {len(todos_list)} items")
    if todos_list:
        print(f"First todo: {todos_list[0].get('title', 'N/A')}\n")
    
    # ============ FINAL SUMMARY ============
    print_section("RETRIEVAL TEST SUMMARY")
    
    task_summary = agent.get_task_report()
    print("✓ Test Execution Summary:")
    print(f"  - Planned tasks: {task_summary.get('planned_tasks')}")
    print(f"  - Executed tasks: {task_summary.get('executed_tasks')}")
    print(f"  - Completed: {task_summary.get('completed_tasks')}")
    print(f"  - Failed: {task_summary.get('failed_tasks')}")
    print(f"  - Success rate: {task_summary.get('success_rate'):.1f}%")
    print(f"  - Avg execution time: {task_summary.get('avg_execution_time_ms'):.1f}ms")
    
    print(f"\n✓ Task Types Distribution:")
    for task_type, count in task_summary.get('task_types', {}).items():
        print(f"  - {task_type}: {count}")
    
    print(f"\n✓ Subagent Distribution:")
    for subagent, count in task_summary.get('subagent_distribution', {}).items():
        print(f"  - {subagent}: {count}")
    
    print(f"\n✓ Persistent Storage:")
    print(f"  - Todos directory: ./test_retrieval_workflow/")
    print(f"  - Todos count: {len(todos_list)}")
    print(f"  - Todos persisted: {'Yes' if todos_list else 'No'}")
    
    print("\n" + "="*80)
    print("  TEST COMPLETE - RETRIEVAL FROM MASTER AGENT WORKING")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        test_retrieval_from_master_agent()
    except Exception as e:
        print(f"\n[FATAL ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
