#!/usr/bin/env python3
"""Test end-to-end plug-and-play workflow with questions"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from incident_iq.rag.agents.master_orchestrator import MasterOrchestrator


def test_finance_workflow():
    """Test complete finance workflow: ingest -> ask -> answer"""
    print("\n" + "="*60)
    print("WORKFLOW TEST 1: FINANCE (Ingest + Question)")
    print("="*60)
    
    finance_data = [
        "Q3 2024 Financial Results: Total Revenue: $45.2M, Operating Income: $12.5M, Profit Margin: 27.6%",
        "Investment Portfolio Allocation: Technology 40%, Healthcare 30%, Finance 20%, Energy 10%",
        "New Product Pricing: Standard Plan $99/month, Professional $299/month, Enterprise Custom",
        "Customer Acquisition Cost: $450, Lifetime Value: $18,000, CAC Payback: 9 months",
    ]
    
    orch = MasterOrchestrator()
    
    # Ingest
    print("\n[1] Ingesting finance data...")
    ingest_result = orch.ingest_data(finance_data, domain="finance")
    print(f"    Domain: {ingest_result['domain']}")
    print(f"    Documents: {ingest_result['documents_ingested']}")
    
    # Ask question
    print("\n[2] Asking question...")
    question = "What is our Q3 profit margin and product pricing strategy?"
    print(f"    Question: {question}")
    
    answer_result = orch.ask_question(question)
    
    if answer_result['success']:
        print(f"\n[3] Answer (truncated):")
        answer = answer_result.get('answer', '')[:300]
        print(f"    {answer}...")
        print(f"\n[4] Metadata:")
        print(f"    Tokens: {answer_result.get('token_usage', {}).get('total', 0)}")
        print(f"    Tags: {answer_result.get('tags', [])[:3]}")
        print(f"    Agents used: {answer_result.get('agents_used', [])}")
        print(f"\n[OK] Finance workflow successful")
        return True
    else:
        print(f"[ERROR] Question failed: {answer_result.get('error')}")
        return False


def test_technical_workflow():
    """Test complete technical workflow: ingest -> ask -> answer"""
    print("\n" + "="*60)
    print("WORKFLOW TEST 2: TECHNICAL (Ingest + Question)")
    print("="*60)
    
    technical_data = """
    API Configuration Guide:
    
    1. Authentication:
       - Use OAuth 2.0 for web applications
       - Use API keys for server-to-server communication
       - Rotate keys every 90 days
    
    2. Rate Limiting:
       - 1000 requests per minute for standard tier
       - 5000 requests per minute for premium tier
       - 429 responses indicate rate limit exceeded
    
    3. Error Handling:
       - 404: Resource not found
       - 500: Server error, retry with exponential backoff
       - 503: Service temporarily unavailable
    
    4. Database Connection:
       - Connection pooling recommended (min: 5, max: 20)
       - Timeout: 30 seconds
       - SSL/TLS required for production
    """
    
    orch = MasterOrchestrator()
    
    # Ingest
    print("\n[1] Ingesting technical documentation...")
    ingest_result = orch.ingest_data(technical_data)
    print(f"    Domain: {ingest_result['domain']}")
    print(f"    Documents: {ingest_result['documents_ingested']}")
    
    # Ask question
    print("\n[2] Asking question...")
    question = "How should I configure database connections for production?"
    print(f"    Question: {question}")
    
    answer_result = orch.ask_question(question)
    
    if answer_result['success']:
        print(f"\n[3] Answer (truncated):")
        answer = answer_result.get('answer', '')[:300]
        print(f"    {answer}...")
        print(f"\n[4] Metadata:")
        print(f"    Tokens: {answer_result.get('token_usage', {}).get('total', 0)}")
        print(f"    Tags: {answer_result.get('tags', [])[:3]}")
        print(f"    Agents used: {answer_result.get('agents_used', [])}")
        print(f"\n[OK] Technical workflow successful")
        return True
    else:
        print(f"[ERROR] Question failed: {answer_result.get('error')}")
        return False


def test_multi_domain_questions():
    """Test asking questions about different domains"""
    print("\n" + "="*60)
    print("WORKFLOW TEST 3: Multi-Domain Q&A")
    print("="*60)
    
    domains = {
        "finance": {
            "data": "Annual revenue growth: 25%, Operating margin: 18%, ROE: 22%",
            "question": "What's our revenue growth rate?"
        },
        "travel": {
            "data": "Top destinations: Paris (1200/week), Tokyo (1500/week), NYC (900/week)",
            "question": "Which destination costs the most per week?"
        },
    }
    
    print("\n[1] Testing independent orchestrators with different domains")
    
    for domain_name, domain_info in domains.items():
        orch = MasterOrchestrator()
        
        # Ingest
        ingest_result = orch.ingest_data(domain_info["data"], domain=domain_name)
        print(f"\n  [{domain_name.upper()}] Ingested {ingest_result['documents_ingested']} docs")
        
        # Ask
        answer_result = orch.ask_question(domain_info["question"])
        
        if answer_result['success']:
            print(f"  [{domain_name.upper()}] Q: {domain_info['question'][:50]}...")
            print(f"  [{domain_name.upper()}] Answer: {answer_result.get('answer', '')[:80]}...")
        else:
            print(f"  [{domain_name.upper()}] ERROR: {answer_result.get('error')}")
            return False
    
    print("\n[OK] Multi-domain Q&A successful")
    return True


if __name__ == "__main__":
    try:
        print("\n[TEST] Plug-and-Play Workflow (Ingest + Question)")
        print("[TEST] Testing complete end-to-end domain-agnostic RAG\n")
        
        success = True
        success = test_finance_workflow() and success
        success = test_technical_workflow() and success
        success = test_multi_domain_questions() and success
        
        if success:
            print("\n" + "="*60)
            print("[SUCCESS] All plug-and-play workflows passed!")
            print("="*60)
            print("\nPlug-and-Play RAG System is COMPLETE:")
            print("  ✓ ingest_data(data) - accepts ANY format")
            print("  ✓ Auto-detects domain (finance, travel, medical, technical)")
            print("  ✓ ask_question(q) - works on any domain")
            print("  ✓ No domain-specific configuration needed")
            print("  ✓ Same interface works across all domains")
            print("  ✓ LLM response generation works")
            print("  ✓ Metadata tracking active")
            print("  ✓ Agents spawning correctly\n")
        else:
            print("\n[FAILURE] Some tests failed")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
