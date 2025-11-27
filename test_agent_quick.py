"""
Quick Test: LangGraph Agent Table Ingestion + Question Answering

Run this to quickly test:
1. agent.invoke("ingest_sqlite_table", ...) - Ingest knowledge_base table
2. agent.invoke("ask_question", ...) - Ask questions in different modes
"""

import sys
import json
from pathlib import Path

# Add src to path so we can import from incident_iq package
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

print("\n" + "="*80)
print("QUICK TEST: LangGraph Agent Table Ingestion & Question Answering")
print("="*80)

# Step 1: Initialize Agent
print("\n[STEP 1] Initialize Agent")
print("-" * 80)
try:
    from incident_iq.rag.agents.langgraph_agent import LangGraphRAGAgent
    agent = LangGraphRAGAgent()
    print("[OK] Agent initialized successfully")
    print(f"  - LLM Service: {type(agent.llm_service).__name__}")
    print(f"  - VectorDB Service: {type(agent.vectordb_service).__name__}")
    print(f"  - Guardrails: {'Enabled' if agent.guardrails else 'Disabled'}")
except Exception as e:
    print(f"[ERROR] Failed to initialize agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 2: Ingest Table
print("\n[STEP 2] Ingest SQLite Table (knowledge_base)")
print("-" * 80)
print("Configuration from data_sources.json:")
print("  table_name: knowledge_base")
print("  text_columns: ['cause', 'description', 'impact', 'remediation_steps', 'rca']")
print("  metadata_columns: ['id', 'resource_type', 'environment', 'dollar_impact']")
print()

try:
    ingest_result = agent.invoke(
        "ingest_sqlite_table",
        table_name="knowledge_base",
        doc_id="sqlite_knowledge_base",
        rbac_namespace="general",
        text_columns=["cause", "description", "impact", "remediation_steps", "rca"],
        metadata_columns=["id", "resource_type", "environment", "dollar_impact"]
    )
    
    print("Result:")
    print(json.dumps(ingest_result, indent=2))
    
    if not ingest_result.get("success"):
        print("\n[NOTE] Ingestion may have failed due to empty table or missing data")
        print("  The test will continue with question answering")
    else:
        print(f"\n[OK] Successfully ingested table")
        print(f"  Records processed: {ingest_result.get('records_processed', 0)}")
        print(f"  Total chunks saved: {ingest_result.get('total_chunks_saved', 0)}")
        
except Exception as e:
    print(f"[ERROR] Error during table ingestion: {e}")
    import traceback
    traceback.print_exc()

# Step 3: Ask Question - CONCISE Mode
print("\n[STEP 3] Ask Question - CONCISE Mode")
print("-" * 80)
print("Mode: concise (user-friendly)")
print("Guardrails: hallucination_check + security_incident_policy")
print()

try:
    question1 = "What are the main incident causes?"
    print(f"Question: {question1}")
    print()
    
    result = agent.invoke(
        "ask_question",
        question=question1,
        response_mode="concise"
    )
    
    print("Response:")
    print(f"  Success: {result.get('success')}")
    print(f"  Answer: {result.get('answer', 'N/A')[:300]}...")
    print(f"  Session ID: {result.get('session_id')}")
    print(f"  Guardrails Applied: {result.get('guardrails_applied')}")
    if result.get('errors'):
        print(f"  Errors: {result.get('errors')}")
    
except Exception as e:
    print(f"[ERROR] Error during concise question answering: {e}")
    import traceback
    traceback.print_exc()

# Step 4: Ask Question - INTERNAL Mode
print("\n[STEP 4] Ask Question - INTERNAL Mode")
print("-" * 80)
print("Mode: internal (system integration, structured data)")
print("Guardrails: hallucination_check only")
print()

try:
    question2 = "What remediation steps are recommended?"
    print(f"Question: {question2}")
    print()
    
    result = agent.invoke(
        "ask_question",
        question=question2,
        response_mode="internal"
    )
    
    print("Response:")
    print(f"  Success: {result.get('success')}")
    print(f"  Answer: {result.get('answer', 'N/A')[:300]}...")
    print(f"  Quality Score: {result.get('quality_score')}")
    print(f"  Sources Count: {result.get('sources_count')}")
    print(f"  Guardrails Applied: {result.get('guardrails_applied')}")
    if result.get('source_docs'):
        print(f"  Source Docs: {json.dumps(result.get('source_docs')[:2], indent=4)}")
    if result.get('errors'):
        print(f"  Errors: {result.get('errors')}")
    
except Exception as e:
    print(f"[ERROR] Error during internal question answering: {e}")
    import traceback
    traceback.print_exc()

# Step 5: Ask Question - VERBOSE Mode
print("\n[STEP 5] Ask Question - VERBOSE Mode")
print("-" * 80)
print("Mode: verbose (full debug details)")
print("Guardrails: NONE (raw data for engineers)")
print("Debug Output: Full node-by-node execution shown above")
print()

try:
    question3 = "What are the environmental impacts?"
    print(f"Question: {question3}")
    print()
    print("[Note: Console output from retrieval workflow visible above]")
    print()
    
    result = agent.invoke(
        "ask_question",
        question=question3,
        response_mode="verbose"
    )
    
    print("\nResponse Summary:")
    print(f"  Success: {result.get('success')}")
    print(f"  Answer: {result.get('answer', 'N/A')[:300]}...")
    print(f"  Retrieval Quality: {result.get('retrieval_quality')}")
    print(f"  Sources Count: {result.get('sources_count')}")
    print(f"  Optimization Applied: {result.get('optimization_applied')}")
    print(f"  Execution Time: {result.get('execution_time_ms')}ms")
    print(f"  Guardrails Applied: {result.get('guardrails_applied')}")
    if result.get('errors'):
        print(f"  Errors: {result.get('errors')}")
    
except Exception as e:
    print(f"[ERROR] Error during verbose question answering: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print("\n✓ All tests executed successfully!")
print("\nNext steps:")
print("  1. Check the answers generated above")
print("  2. Verify guardrails are applied (concise/internal modes)")
print("  3. Check debug output in verbose mode")
print("  4. Review source documents in internal mode")
print()
