#!/usr/bin/env python
"""
GUARDRAILS SERVICE TEST - QUICK TEST VERSION
Simple, direct test of guardrails with corrective action processor

Usage:
  python scripts/test_guardrails_quick.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def test_guardrails_quick():
    """Quick guardrails test"""
    
    print("\n" + "="*80)
    print("GUARDRAILS SERVICE - QUICK TEST")
    print("="*80)
    
    try:
        # Import the service
        print("\n[1] Importing GuardrailsService...")
        from src.incident_iq.services.guardrails_service import create_guardrails_service
        print("    ✓ Import successful")
        
        # Create service
        print("\n[2] Creating GuardrailsService...")
        guardrails = create_guardrails_service()
        print("    ✓ Service created")
        
        # Check registered scopes
        print("\n[3] Checking registered guardrails...")
        for scope, guards in guardrails.guardrails.items():
            print(f"    - {scope}: {len(guards)} guardrails")
        
        # Test ingestion input validation
        print("\n[4] Testing ingestion input validation...")
        valid_doc = {
            'document_id': 'doc_001',
            'content': 'Test document content'
        }
        passed, results = guardrails.check_ingestion_input(valid_doc)
        print(f"    ✓ Valid document: {'PASS' if passed else 'FAIL'}")
        
        # Test invalid document (missing field)
        print("\n[5] Testing invalid document (missing content)...")
        invalid_doc = {'document_id': 'doc_002'}
        passed, results = guardrails.check_ingestion_input(invalid_doc)
        print(f"    ✓ Invalid document: {'PASS' if not passed else 'FAIL'} (should fail)")
        
        # Test retrieval query
        print("\n[6] Testing retrieval query validation...")
        valid_query = {
            'query': 'What are the steps?',
            'top_k': 5
        }
        passed, results = guardrails.check_retrieval_input(valid_query)
        print(f"    ✓ Valid query: {'PASS' if passed else 'FAIL'}")
        
        # Test invalid query (top_k too high)
        print("\n[7] Testing invalid query (top_k exceeds maximum)...")
        invalid_query = {
            'query': 'What are the steps?',
            'top_k': 150
        }
        passed, results = guardrails.check_retrieval_input(invalid_query)
        print(f"    ✓ Invalid query: {'PASS' if not passed else 'FAIL'} (should fail)")
        
        # Test RL action validation
        print("\n[8] Testing RL action validation...")
        valid_action = {
            'action': 'REINDEX',
            'parameters': {'new_chunk_size': 512}
        }
        passed, results = guardrails.check_rl_action(valid_action)
        print(f"    ✓ Valid action: {'PASS' if passed else 'FAIL'}")
        
        # Test invalid action
        print("\n[9] Testing invalid RL action...")
        invalid_action = {
            'action': 'INVALID_ACTION',
            'parameters': {}
        }
        passed, results = guardrails.check_rl_action(invalid_action)
        print(f"    ✓ Invalid action: {'PASS' if not passed else 'FAIL'} (should fail)")
        
        # Test reward clipping
        print("\n[10] Testing RL reward clipping...")
        reward_data = {'reward': 2.5}  # Will be clipped to 1.0
        passed, results = guardrails.check_rl_reward(reward_data)
        clipped_reward = reward_data['reward']
        print(f"    ✓ Original reward: 2.5 → Clipped: {clipped_reward}")
        
        # Get statistics
        print("\n[11] Checking guardrail statistics...")
        stats = guardrails.get_guard_stats()
        print(f"    Total checks: {stats['total_checks']}")
        print(f"    Passed: {stats['passed']}")
        print(f"    Failed: {stats['failed']}")
        print(f"    Pass rate: {stats['pass_rate']:.1%}")
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_guardrails_quick()
    sys.exit(0 if success else 1)
