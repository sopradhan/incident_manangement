#!/usr/bin/env python3
"""
LangGraph Agent - Interactive Chat CLI
Direct command-line invocation for chat mode

USAGE:
    python langgraph_chat_cli.py [mode] [--help]
    
    mode: 'concise' (default), 'internal', 'verbose'
    
EXAMPLES:
    python langgraph_chat_cli.py
    python langgraph_chat_cli.py concise
    python langgraph_chat_cli.py verbose
    python langgraph_chat_cli.py --help
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent


def main():
    parser = argparse.ArgumentParser(
        description="LangGraph Agent Interactive Chat",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
RESPONSE MODES:
  concise   - User-friendly, concise answers with policy validation
  internal  - System integration mode, structured data, hallucination check only
  verbose   - Full debug details for engineers, no guardrails

EXAMPLES:
  python langgraph_chat_cli.py
  python langgraph_chat_cli.py concise
  python langgraph_chat_cli.py verbose
  python langgraph_chat_cli.py --no-history
        """
    )
    
    parser.add_argument(
        "mode",
        nargs="?",
        default="concise",
        choices=["concise", "internal", "verbose"],
        help="Response mode for chat (default: concise)"
    )
    
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Don't show conversation history at end"
    )
    
    args = parser.parse_args()
    
    try:
        print(f"\n[INIT] Initializing LangGraph Agent...")
        agent = LangGraphRAGAgent()
        print(f"[OK] Agent ready for chat\n")
        
        # Start interactive chat
        result = agent.invoke(
            operation="chat",
            response_mode=args.mode,
            show_history=not args.no_history
        )
        
        print(f"\n[OK] Chat session completed")
        print(f"    Questions asked: {result['message_count']}")
        print(f"    Session saved to: {result['session_file']}\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n[OK] Session interrupted by user")
        return 0
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
