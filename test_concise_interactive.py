#!/usr/bin/env python
"""
Interactive Concise Mode - User Satisfaction Loop
Shows answer → asks satisfaction → loops if needed
"""
import sys
from src.incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent
from io import StringIO

def suppress_debug():
    """Suppress debug output"""
    return StringIO()

def ask_satisfaction():
    """Get user satisfaction feedback"""
    try:
        while True:
            response = input("\nAre you satisfied with this answer? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                return True
            elif response in ['no', 'n']:
                return False
            else:
                print("Please enter 'yes' or 'no'")
    except EOFError:
        # Non-interactive mode (piped input)
        return True

def main():
    print("\n" + "="*80)
    print("INTERACTIVE CONCISE MODE - INCIDENT MANAGEMENT Q&A")
    print("="*80 + "\n")
    
    agent = LangGraphRAGAgent()
    print("[OK] Agent initialized\n")
    
    while True:
        # Get question from user
        try:
            question = input("Ask a question (or 'quit' to exit): ").strip()
        except EOFError:
            # Non-interactive mode - end gracefully
            print("\n[OK] Workflow ended. Thank you!")
            break
        
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n[OK] Workflow ended. Thank you!")
            break
        
        if not question:
            print("[!] Please enter a valid question\n")
            continue
        
        print(f"\nQuestion: {question}")
        print("-" * 80)
        
        # Get answer in concise mode (suppress debug output)
        old_stdout = sys.stdout
        sys.stdout = suppress_debug()
        
        try:
            response = agent.ask_question(
                question=question,
                response_mode="concise"
            )
        finally:
            sys.stdout = old_stdout
        
        # Display answer
        if response.get("success"):
            answer = response.get("answer", "No answer available")
            print(f"Answer:\n{answer}\n")
            print("-" * 80)
            
            # Ask satisfaction
            if ask_satisfaction():
                print("[OK] Great! Moving on...\n")
            else:
                print("\n[?] Let me try again to find better information...\n")
                # Continue loop for another attempt
        else:
            print(f"[ERROR] Failed to get answer: {response.get('errors', 'Unknown error')}\n")
    
    print("\n" + "="*80)
    print("SESSION COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[OK] Session interrupted by user. Thank you!")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
