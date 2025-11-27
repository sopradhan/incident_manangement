"""
LangGraph Master Agent - Simple One-Line Invocation

Usage:
    python invoke_langgraph_sqlite.py              # Ingest knowledge_base table
    python invoke_langgraph_sqlite.py --query      # Ingest and query
    python invoke_langgraph_sqlite.py --help       # Show examples
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent


def main():
    """Main entry point."""
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        return
    
    # Initialize master agent
    agent = LangGraphRAGAgent()
    
    if "--query" in sys.argv:
        # Ingest and query
        ingest_and_query(agent)
    else:
        # Just ingest
        ingest_only(agent)


def ingest_only(agent):
    """Ingest SQLite table using agent.invoke()"""
    
    print("\n" + "="*80)
    print("🤖 LANGGRAPH MASTER AGENT - SQLITE TABLE INGESTION")
    print("="*80)
    print("\n📋 Configuration: src/incident_iq/rag/config/data_sources.json")
    print("📊 Table: knowledge_base")
    print("⏳ Ingesting...")
    
    # ONE-LINE INVOCATION
    result = agent.invoke(
        "ingest_sqlite_table",
        table_name="knowledge_base"
    )
    
    # Display results
    print(f"\n✅ Status: {'SUCCESS' if result.get('success') else 'FAILED'}")
    print(f"📊 Chunks Saved: {result.get('chunks_saved', 0)}")
    print(f"🏷️  Doc ID: {result.get('doc_id', 'N/A')}")
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
    
    return result.get('success', False)


def ingest_and_query(agent):
    """Ingest and then query using agent.invoke()"""
    
    print("\n" + "="*80)
    print("🤖 LANGGRAPH MASTER AGENT - INGEST AND QUERY")
    print("="*80)
    
    # Step 1: Ingest
    print("\n📥 Step 1: Ingesting knowledge_base table...")
    ingest_result = agent.invoke("ingest_sqlite_table", table_name="knowledge_base")
    
    if not ingest_result.get('success'):
        print(f"❌ Ingestion failed: {ingest_result.get('error')}")
        return
    
    print(f"✅ Complete: {ingest_result.get('chunks_saved')} chunks saved")
    
    # Step 2: Query
    print("\n❓ Step 2: Querying ingested data...")
    
    questions = [
        "What are the common causes of incidents?",
        "How should we remediate critical issues?",
        "What is the impact on resources?"
    ]
    
    for q in questions:
        print(f"\n   Q: {q}")
        query_result = agent.invoke("ask_question", question=q, response_mode="concise")
        
        answer = query_result.get('answer', 'No answer generated')
        
        # Clean up JSON if present
        if isinstance(answer, str) and answer.strip().startswith('{'):
            try:
                parsed = json.loads(answer)
                answer = parsed.get('answer', answer)
            except:
                pass
        
        print(f"   A: {answer[:150]}...")


def print_help():
    """Print help and examples."""
    print("""
🤖 LangGraph Master Agent - One-Line Invocation Examples

BASIC USAGE:
============

1. Ingest SQLite table (default: knowledge_base)
   python invoke_langgraph_sqlite.py

2. Ingest and query immediately
   python invoke_langgraph_sqlite.py --query

3. Show this help
   python invoke_langgraph_sqlite.py --help


PYTHON API:
===========

from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent

agent = LangGraphRAGAgent()

# Ingest SQLite table
result = agent.invoke("ingest_sqlite_table", table_name="knowledge_base")

# Ask question
result = agent.invoke("ask_question", question="What are common causes?")

# Ingest document
result = agent.invoke("ingest_document", text="...", doc_id="doc_001")

# Optimize system
result = agent.invoke("optimize", performance_history=[...])


CONFIGURATION:
==============

Source: src/incident_iq/rag/config/data_sources.json

Current settings for knowledge_base:
  - Text columns: cause, description, impact, remediation_steps, rca
  - Metadata: id, resource_type, environment, dollar_impact
  - Chunk size: 512 characters
  - Overlap: 50 characters


EXPECTED OUTPUT:
================

✅ Status: SUCCESS
📊 Chunks Saved: 247
🏷️  Doc ID: sqlite_knowledge_base
""")


if __name__ == "__main__":
    main()
    
    print("\n" + "="*80)
    print("✅ COMPLETE")
    print("="*80 + "\n")
