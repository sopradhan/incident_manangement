#!/usr/bin/env python
"""
Test LangGraph Agent with All Response Modes
- concise: End-user friendly (answer only)
- verbose: Engineer/RAG Admin (all metadata, traceability, RL info)
- internal: System/Integration (answer + structured data for database updates)
"""

import json
import time
from datetime import datetime
from src.incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent

# Initialize agent
print("\n" + "="*80)
print("LANGGRAPH AGENT - ALL RESPONSE MODES TEST")
print("="*80 + "\n")

agent = LangGraphRAGAgent()
print("[OK] Agent initialized\n")

# Test questions
questions = [
    "What is incident management?",
    "What are the incident priority levels?",
    "How do we handle critical incidents?",
]

# Chat history to persist conversations
chat_history = {
    "concise": [],
    "verbose": [],
    "internal": []
}

# Test all three modes
modes = ["concise", "verbose", "internal"]

for mode in modes:
    print(f"\n{'='*80}")
    print(f"MODE: {mode.upper()}")
    mode_desc = {"concise": "End-user friendly", "verbose": "Engineer/Admin", "internal": "System/Integration"}
    print(f"Description: {mode_desc[mode]}")
    print(f"{'='*80}\n")
    
    for i, question in enumerate(questions, 1):
        print(f"[Q{i}] {question}")
        
        start = time.time()
        result = agent.ask_question(
            question=question,
            response_mode=mode
        )
        elapsed = time.time() - start
        
        # Store in chat history
        chat_history[mode].append({
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "response": result,
            "elapsed_ms": elapsed * 1000
        })
        
        # Display response based on mode
        if result.get("success"):
            if mode == "concise":
                # Concise: Just the answer
                print(f"    Answer: {result.get('answer', '')[:200]}...")
                print(f"    Session: {result.get('session_id', 'N/A')[:8]}...")
            
            elif mode == "verbose":
                # Verbose: Full details for engineers
                print(f"    Answer: {result.get('answer', '')[:150]}...")
                print(f"    Quality Score: {result.get('retrieval_quality', 0):.2f}")
                print(f"    Sources: {result.get('sources_count', 0)} documents")
                print(f"    RL Action: {result.get('rl_action', 'SKIP')}")
                print(f"    Optimization: {result.get('optimization_applied', False)}")
                print(f"    Execution Time: {result.get('execution_time_ms', 0):.0f}ms")
                print(f"    Session: {result.get('session_id', 'N/A')[:8]}...")
            
            elif mode == "internal":
                # Internal: Structured for system integration (plain answer text)
                print(f"    Answer: {result.get('answer', '')[:150]}...")
                print(f"    Quality: {result.get('quality_score', 0):.2f}")
                print(f"    Sources: {result.get('sources_count', 0)}")
                source_docs = result.get('source_docs', [])
                if source_docs:
                    print(f"    First Source: {source_docs[0].get('doc_id', 'N/A')}")
                print(f"    Session: {result.get('metadata', {}).get('session_id', 'N/A')[:8]}...")
        else:
            print(f"    [ERROR] Query failed: {result.get('errors', ['Unknown error'])}")
        
        print()

# Display chat history summary
print(f"\n{'='*80}")
print("CHAT HISTORY SUMMARY")
print(f"{'='*80}\n")

for mode in modes:
    history = chat_history[mode]
    print(f"{mode.upper()} Mode - {len(history)} questions:")
    for i, entry in enumerate(history, 1):
        success = entry['response'].get('success', False)
        status = "[OK]" if success else "[FAILED]"
        print(f"  {status} Q{i}: {entry['question'][:60]}... ({entry['elapsed_ms']:.0f}ms)")
    print()

print("="*80)
print("TEST COMPLETE - Chat history persisted and ready for resume")
print("="*80 + "\n")

# Save chat history to file for persistence
import os
history_dir = "data/chat_history"
os.makedirs(history_dir, exist_ok=True)
history_file = f"{history_dir}/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(history_file, "w") as f:
    json.dump(chat_history, f, indent=2, default=str)
print(f"[OK] Chat history saved to: {history_file}\n")
