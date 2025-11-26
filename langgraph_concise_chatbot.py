#!/usr/bin/env python
"""
LangGraph-based Concise Chatbot with State Management
Inspired by: https://github.com/ProactiveAIAgents/LangGraph_Chatbot_Agent
"""

import sys
from typing import Any, Dict, List, Annotated
from datetime import datetime
from io import StringIO

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from src.incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent


class ChatState(TypedDict):
    """State management for chatbot conversation."""
    question: str
    answer: str
    session_id: str
    satisfied: bool
    message_count: int
    conversation_history: List[Dict[str, str]]
    errors: List[str]


class LangGraphConciseChatbot:
    """Interactive chatbot with LangGraph state management."""
    
    def __init__(self):
        """Initialize chatbot and RAG agent."""
        self.agent = LangGraphRAGAgent()
        self.graph = self._build_graph()
        print("[OK] LangGraph Concise Chatbot initialized\n")
    
    def _build_graph(self) -> Any:
        """Build LangGraph conversation flow."""
        graph = StateGraph(ChatState)
        
        def get_question(state: ChatState) -> ChatState:
            """Node: Get user question."""
            try:
                question = input("Ask a question (or 'quit' to exit): ").strip()
            except EOFError:
                question = "quit"
            
            if question.lower() in ['quit', 'exit', 'q']:
                state["answer"] = "END_SESSION"
            else:
                state["question"] = question
            
            return state
        
        def process_question(state: ChatState) -> ChatState:
            """Node: Process question through RAG agent."""
            if state["answer"] == "END_SESSION":
                return state
            
            question = state["question"]
            if not question:
                state["errors"].append("Please enter a valid question")
                return state
            
            # Suppress debug output
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                response = self.agent.ask_question(
                    question=question,
                    response_mode="concise"
                )
            finally:
                sys.stdout = old_stdout
            
            if response.get("success"):
                state["answer"] = response.get("answer", "No answer available")
                state["session_id"] = response.get("session_id", "")
                state["message_count"] += 1
            else:
                state["errors"].append(f"Query failed: {response.get('errors', 'Unknown error')}")
            
            return state
        
        def display_answer(state: ChatState) -> ChatState:
            """Node: Display answer to user."""
            if state["answer"] == "END_SESSION":
                return state
            
            if state["errors"]:
                print(f"[ERROR] {state['errors'][-1]}\n")
                return state
            
            print(f"\nQuestion: {state['question']}")
            print("-" * 70)
            print(f"Answer:\n{state['answer']}\n")
            print("-" * 70)
            
            # Add to history
            state["conversation_history"].append({
                "timestamp": datetime.now().isoformat(),
                "question": state["question"],
                "answer": state["answer"],
                "session_id": state["session_id"]
            })
            
            return state
        
        def ask_satisfaction(state: ChatState) -> ChatState:
            """Node: Ask if user satisfied."""
            if state["answer"] == "END_SESSION" or state["errors"]:
                state["satisfied"] = True
                return state
            
            try:
                response = input("\nAre you satisfied with this answer? (yes/no): ").strip().lower()
            except EOFError:
                response = "yes"
            
            state["satisfied"] = response in ['yes', 'y']
            return state
        
        def handle_satisfied(state: ChatState) -> ChatState:
            """Node: Handle satisfied response."""
            if not state["satisfied"]:
                return state
            print("\n[OK] Great! Happy to help. Ask another question or type 'quit' to exit.\n")
            return state
        
        def handle_unsatisfied(state: ChatState) -> ChatState:
            """Node: Handle unsatisfied response."""
            if state["satisfied"] or state["answer"] == "END_SESSION":
                return state
            
            print("\n[?] Let me try to find better information...\n")
            return state
        
        def end_session(state: ChatState) -> ChatState:
            """Node: End session."""
            print("\n[OK] Workflow ended. Thank you!")
            return state
        
        # Add nodes
        graph.add_node("get_question", get_question)
        graph.add_node("process_question", process_question)
        graph.add_node("display_answer", display_answer)
        graph.add_node("ask_satisfaction", ask_satisfaction)
        graph.add_node("handle_satisfied", handle_satisfied)
        graph.add_node("handle_unsatisfied", handle_unsatisfied)
        graph.add_node("end_session", end_session)
        
        # Add edges
        graph.add_edge(START, "get_question")
        graph.add_edge("get_question", "process_question")
        graph.add_edge("process_question", "display_answer")
        graph.add_edge("display_answer", "ask_satisfaction")
        
        # Conditional routing after satisfaction
        def route_satisfaction(state: ChatState) -> str:
            if state["answer"] == "END_SESSION":
                return "end_session"
            elif state["satisfied"]:
                return "handle_satisfied"
            else:
                return "handle_unsatisfied"
        
        graph.add_conditional_edges("ask_satisfaction", route_satisfaction, {
            "end_session": "end_session",
            "handle_satisfied": "handle_satisfied",
            "handle_unsatisfied": "handle_unsatisfied"
        })
        
        graph.add_edge("handle_satisfied", "get_question")
        graph.add_edge("handle_unsatisfied", "get_question")
        graph.add_edge("end_session", END)
        
        return graph.compile()
    
    def run(self):
        """Run the chatbot."""
        print("\n" + "="*70)
        print("LANGGRAPH CONCISE CHATBOT - INCIDENT MANAGEMENT")
        print("="*70 + "\n")
        
        initial_state: ChatState = {
            "question": "",
            "answer": "",
            "session_id": "",
            "satisfied": False,
            "message_count": 0,
            "conversation_history": [],
            "errors": []
        }
        
        try:
            final_state = self.graph.invoke(initial_state)
            
            # Print summary
            print("\n" + "="*70)
            print("SESSION SUMMARY")
            print("="*70)
            print(f"Total Questions: {final_state['message_count']}")
            print(f"Messages in History: {len(final_state['conversation_history'])}")
            
            if final_state["conversation_history"]:
                print("\nConversation History:")
                for i, entry in enumerate(final_state["conversation_history"], 1):
                    print(f"  {i}. Q: {entry['question'][:60]}...")
                    print(f"     A: {entry['answer'][:60]}...")
            
            print("="*70 + "\n")
            
            # Save session
            import json
            import os
            history_dir = "data/chat_history"
            os.makedirs(history_dir, exist_ok=True)
            session_file = f"{history_dir}/concise_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(session_file, "w") as f:
                json.dump(final_state, f, indent=2, default=str)
            print(f"[OK] Session saved to: {session_file}\n")
            
        except KeyboardInterrupt:
            print("\n\n[OK] Session interrupted by user. Thank you!")


if __name__ == "__main__":
    chatbot = LangGraphConciseChatbot()
    chatbot.run()
