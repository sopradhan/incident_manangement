#!/usr/bin/env python
"""
End-to-End Test: Full LangGraph Query with Logging & Visualization
"""

import json
from pathlib import Path

print("\n" + "="*80)
print("FULL END-TO-END QUERY TEST")
print("="*80)

# Step 1: Clear previous data
print("\n[Step 1] Checking database state before query...")
from src.incident_iq.database.models.rag_history_model import RAGHistoryModel

model = RAGHistoryModel()
model.cursor.execute("SELECT COUNT(*) FROM rag_history_and_optimization")
before_count = model.cursor.fetchone()[0]
print(f"[✓] rag_history_and_optimization before query: {before_count} rows")

# Step 2: Initialize agent
print("\n[Step 2] Initializing LangGraphRAGAgent...")
from src.incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent

try:
    agent = LangGraphRAGAgent()
    print("[✓] Agent initialized successfully")
except Exception as e:
    print(f"[✗] Failed to initialize agent: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 3: Ask a question
print("\n[Step 3] Running ask_question()...")
print("-" * 80)

try:
    result = agent.ask_question(
        question="What is incident management?",
        doc_id=None  # Will extract from context
    )
    
    print("-" * 80)
    print(f"[✓] Query completed")
    print(f"    - Success: {result.get('success')}")
    print(f"    - Session ID: {result.get('session_id')}")
    print(f"    - Execution Time: {result.get('execution_time_ms'):.0f}ms")
    print(f"    - Sources Count: {result.get('sources_count')}")
    print(f"    - Optimization Applied: {result.get('optimization_applied')}")
    print(f"    - RL Action: {result.get('rl_action')}")
    if result.get('errors'):
        print(f"    - Errors: {result.get('errors')}")
    
except Exception as e:
    print(f"[✗] Query failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Step 4: Check database after query
print("\n[Step 4] Checking database state after query...")
model = RAGHistoryModel()
model.cursor.execute("SELECT COUNT(*) FROM rag_history_and_optimization")
after_count = model.cursor.fetchone()[0]
print(f"[✓] rag_history_and_optimization after query: {after_count} rows")
print(f"    - Rows added: {after_count - before_count}")

# Show detail of new rows
if after_count > before_count:
    model.cursor.execute("SELECT history_id, event_type, query_text, action_taken FROM rag_history_and_optimization ORDER BY history_id DESC LIMIT ?", (after_count - before_count,))
    rows = model.cursor.fetchall()
    print(f"[✓] New events logged:")
    for row in rows:
        print(f"    - ID: {row[0]}, Type: {row[1]}, Query/Action: {row[2] or row[3]}")
else:
    print("[!] WARNING: No new rows added to rag_history_and_optimization!")
    print("[DEBUG] Query logging may not be executing")

# Step 5: Check visualization files
print("\n[Step 5] Checking visualization output files...")
session_id = result.get('session_id')

logs_dir = Path("logs")
session_graph_dir = Path("session_graph")

json_files = list(logs_dir.glob(f"*{session_id[:8]}*"))
print(f"[✓] JSON trace files: {len(json_files)}")
for f in json_files:
    size = f.stat().st_size
    print(f"    - {f.name} ({size} bytes)")

png_files = list(session_graph_dir.glob(f"*{session_id[:8]}*"))
print(f"[✓] PNG visualization files: {len(png_files)}")
for f in png_files:
    size = f.stat().st_size
    print(f"    - {f.name} ({size} bytes)")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Query executed: {result.get('success')}")
print(f"Database rows added: {after_count - before_count}")
print(f"Visualization files created: {len(json_files) + len(png_files)}")
print(f"Session ID: {session_id}")
print("="*80 + "\n")
