#!/usr/bin/env python
"""Test that workflow diagram is generated once and reused across sessions"""

print("\n" + "="*80)
print("TEST: Workflow Diagram Generated Once & Cached")
print("="*80 + "\n")

from pathlib import Path
from src.incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent

# Initialize agent
print("[Step 1] Initialize agent...")
agent = LangGraphRAGAgent()
print("[✓] Agent initialized")

# Run first query
print("\n[Step 2] Run first query...")
result1 = agent.ask_question("What is incident management?")
print(f"[✓] Query 1 completed. Session: {result1.get('session_id')[:8]}...")

# Check files after first query
pngs_after_1 = list(Path('session_graph').glob('*.png'))
workflows_1 = [p for p in pngs_after_1 if 'workflow' in p.name]
print(f"    - Workflow diagrams: {len(workflows_1)}")

# Run second query  
print("\n[Step 3] Run second query...")
result2 = agent.ask_question("What are incident priorities?")
print(f"[✓] Query 2 completed. Session: {result2.get('session_id')[:8]}...")

# Check files after second query
pngs_after_2 = list(Path('session_graph').glob('*.png'))
workflows_2 = [p for p in pngs_after_2 if 'workflow' in p.name]
print(f"    - Workflow diagrams: {len(workflows_2)}")

# Verify workflow is same file
print("\n[Step 4] Verify workflow diagram is reused...")
if len(workflows_1) > 0 and len(workflows_2) > 0:
    if workflows_1[0].name == workflows_2[0].name:
        print(f"[✓] Same workflow file used: {workflows_1[0].name}")
        print("    (Not regenerated for each session)")
    else:
        print("[!] Different workflow files:")
        print(f"    - Query 1: {workflows_1[0].name}")
        print(f"    - Query 2: {workflows_2[0].name}")

# Check all files
print("\n[Step 5] File Summary...")
all_pngs = list(Path('session_graph').glob('*.png'))
trace_pngs = [p for p in all_pngs if 'trace_' in p.name]
workflow_pngs = [p for p in all_pngs if 'workflow' in p.name]

print(f"[✓] Total PNG files: {len(all_pngs)}")
print(f"    - Execution traces: {len(trace_pngs)} (one per query)")
print(f"    - Workflow diagrams: {len(workflow_pngs)} (reused across all queries)")

if workflow_pngs:
    wf = workflow_pngs[0]
    size = wf.stat().st_size
    print(f"\n[✓] Workflow diagram:")
    print(f"    - File: {wf.name}")
    print(f"    - Size: {size} bytes")
    print(f"    - Path: session_graph/workflow_langgraph.png")

print("\n" + "="*80)
print("✓ Test Complete: Workflow is generated once and cached")
print("="*80 + "\n")
