#!/usr/bin/env python
"""
Test LangGraph Agent with 5 Questions
Tests both verbose and concise response modes
"""

from src.incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent

# Initialize agent
print("\n" + "="*80)
print("TESTING LANGGRAPH AGENT - 5 QUESTIONS")
print("="*80 + "\n")

agent = LangGraphRAGAgent()
print("[OK] Agent initialized\n")

# Test questions
questions = [
    "What is incident management?",
    "What are the incident priority levels?",
    "How do we handle critical incidents?",
    "What is the incident resolution process?",
    "Who should be notified during an incident?"
]

# Test both modes
modes = ["verbose", "concise"]

for mode in modes:
    print(f"\n{'='*80}")
    print(f"MODE: {mode.upper()}")
    print(f"{'='*80}\n")
    
    for i, question in enumerate(questions, 1):
        print(f"[{i}/5] Question: {question}")
        
        result = agent.ask_question(
            question=question,
            response_mode=mode
        )
        
        print(f"      Success: {result.get('success')}")
        print(f"      Session ID: {result.get('session_id')}")
        print(f"      Sources: {result.get('sources_count')}")
        print(f"      Execution Time: {result.get('execution_time_ms')}ms")
        
        # Show response based on mode
        answer = result.get('answer', '')
        if mode == "verbose":
            quality = result.get('retrieval_quality', 0.0)
            print(f"      Quality: {quality:.2f}" if isinstance(quality, (int, float)) else f"      Quality: N/A")
            print(f"      RL Action: {result.get('rl_action', 'SKIP')}")
            print(f"      Answer: {answer[:100]}..." if len(answer) > 100 else f"      Answer: {answer}")
        else:
            print(f"      Answer (Concise): {answer[:150]}..." if len(answer) > 150 else f"      Answer (Concise): {answer}")
        
        print()

print("="*80)
print("TEST COMPLETE")
print("="*80 + "\n")
