#!/usr/bin/env python
"""Test internal mode response format"""
import sys
from io import StringIO
from src.incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent

# Suppress debug output
old_stdout = sys.stdout
sys.stdout = StringIO()

agent = LangGraphRAGAgent()
response = agent.ask_question(
    question="What is incident management?",
    response_mode="internal"
)

# Restore stdout
sys.stdout = old_stdout

print("\nINTERNAL MODE RESPONSE:")
print("=" * 70)
print(f"Success: {response.get('success')}")
print(f"\nAnswer (Plain Text):")
print(response.get('answer', 'No answer'))
print(f"\nQuality Score: {response.get('quality_score'):.2f}")
print(f"Sources Found: {response.get('sources_count')}")
print(f"Session ID: {response.get('metadata', {}).get('session_id', 'N/A')[:8]}...")
print(f"Execution Time: {response.get('metadata', {}).get('execution_time_ms', 0):.0f}ms")
print("=" * 70)
