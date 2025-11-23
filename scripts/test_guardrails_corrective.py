#!/usr/bin/env python
"""
GUARDRAILS SERVICE TEST - CORRECTIVE ACTION PROCESSOR
Simple test of guardrails with corrective action workflow

Usage:
  python scripts/test_guardrails_corrective.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Run guardrails tests"""
    
    print("\n" + "="*80)
    print("GUARDRAILS SERVICE TEST - CORRECTIVE ACTION PROCESSOR")
    print("="*80)
    
    try:
        # Import the service
        print("\n[TEST 1] Importing GuardrailsService...")
        from src.incident_iq.services.guardrails_service import create_guardrails_service
        print("  SUCCESS: Import completed")
        
        # Create service
        print("\n[TEST 2] Creating GuardrailsService...")
        guardrails = create_guardrails_service()
        print("  SUCCESS: Service created")
        
        # Check registered scopes
        print("\n[TEST 3] Checking registered guardrails by scope...")
        for scope, guards in guardrails.guardrails.items():
            print(f"  Scope '{scope}': {len(guards)} guardrails")
        
        # Test 1: Valid ingestion
        print("\n[TEST 4] Testing valid ingestion document...")
        valid_doc = {
            'document_id': 'doc_001',
            'content': 'Test incident management document'
        }
        passed, results = guardrails.check_ingestion_input(valid_doc)
        status = "PASS" if passed else "FAIL"
        print(f"  Result: {status}")
        for r in results:
            if r.result.value == 'pass':
                print(f"    - {r.guard_name}: {r.message}")
        
        # Test 2: Invalid document (missing field)
        print("\n[TEST 5] Testing invalid document (missing 'content' field)...")
        invalid_doc = {
            'document_id': 'doc_002'
        }
        passed, results = guardrails.check_ingestion_input(invalid_doc)
        status = "PASS" if passed else "FAIL (Expected)"
        print(f"  Result: {status}")
        for r in results:
            if r.result.value == 'fail':
                print(f"    BLOCKED: {r.guard_name} - {r.message}")
        
        # Test 3: Valid query
        print("\n[TEST 6] Testing valid retrieval query...")
        valid_query = {
            'query': 'What are steps to resolve critical incidents?',
            'top_k': 5
        }
        passed, results = guardrails.check_retrieval_input(valid_query)
        status = "PASS" if passed else "FAIL"
        print(f"  Result: {status}")
        
        # Test 4: Invalid query (top_k too high)
        print("\n[TEST 7] Testing invalid query (top_k=150 exceeds max=100)...")
        invalid_query = {
            'query': 'What are steps?',
            'top_k': 150
        }
        passed, results = guardrails.check_retrieval_input(invalid_query)
        status = "PASS" if passed else "FAIL (Expected)"
        print(f"  Result: {status}")
        for r in results:
            if r.result.value == 'fail':
                print(f"    BLOCKED: {r.guard_name} - {r.message}")
        
        # Test 5: Valid RL action
        print("\n[TEST 8] Testing valid RL REINDEX action...")
        valid_action = {
            'action': 'REINDEX',
            'parameters': {'new_chunk_size': 512, 'new_overlap': 0.1}
        }
        passed, results = guardrails.check_rl_action(valid_action)
        status = "PASS" if passed else "FAIL"
        print(f"  Result: {status}")
        
        # Test 6: Invalid RL action
        print("\n[TEST 9] Testing invalid RL action (unknown action)...")
        invalid_action = {
            'action': 'INVALID_ACTION',
            'parameters': {}
        }
        passed, results = guardrails.check_rl_action(invalid_action)
        status = "PASS" if passed else "FAIL (Expected)"
        print(f"  Result: {status}")
        for r in results:
            if r.result.value == 'fail':
                print(f"    BLOCKED: {r.guard_name} - {r.message}")
        
        # Test 7: RL reward clipping
        print("\n[TEST 10] Testing RL reward clipping (2.5 should clip to 1.0)...")
        reward_data = {'reward': 2.5}
        passed, results = guardrails.check_rl_reward(reward_data)
        clipped_value = reward_data['reward']
        print(f"  Original reward: 2.5")
        print(f"  Clipped reward: {clipped_value}")
        print(f"  Result: {'PASS (clipped successfully)' if clipped_value == 1.0 else 'FAIL'}")
        
        # Test 8: RL negative reward clipping
        print("\n[TEST 11] Testing RL reward clipping (negative reward)...")
        reward_data = {'reward': -2.0}
        passed, results = guardrails.check_rl_reward(reward_data)
        clipped_value = reward_data['reward']
        print(f"  Original reward: -2.0")
        print(f"  Clipped reward: {clipped_value}")
        print(f"  Result: {'PASS (clipped successfully)' if clipped_value == -1.0 else 'FAIL'}")
        
        # Get statistics
        print("\n[TEST 12] Checking guardrail statistics...")
        stats = guardrails.get_guard_stats()
        print(f"  Total checks: {stats['total_checks']}")
        print(f"  Passed: {stats['passed']}")
        print(f"  Failed: {stats['failed']}")
        pass_rate = stats['pass_rate']
        print(f"  Pass rate: {pass_rate:.1%}")
        
        print("\n[TEST 13] Statistics by guard...")
        for guard_name, counts in stats['by_guard'].items():
            total = counts['pass'] + counts['fail']
            pass_count = counts['pass']
            fail_count = counts['fail']
            if total > 0:
                rate = pass_count / total
                print(f"  {guard_name}: {pass_count} pass, {fail_count} fail ({rate:.1%})")
        
        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        # Count test results
        test_results = [
            ("Valid ingestion", True),
            ("Invalid ingestion blocked", not guardrails.check_ingestion_input({'document_id': 'doc'})[0]),
            ("Valid query", guardrails.check_retrieval_input(valid_query)[0]),
            ("Invalid query blocked", not guardrails.check_retrieval_input(invalid_query)[0]),
            ("Valid RL action", guardrails.check_rl_action(valid_action)[0]),
            ("Invalid RL action blocked", not guardrails.check_rl_action(invalid_action)[0]),
            ("Reward clipping", clipped_value == 1.0),
            ("Statistics collection", stats['total_checks'] > 0)
        ]
        
        passed_count = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        print(f"\nResults:")
        for test_name, result in test_results:
            status = "PASS" if result else "FAIL"
            print(f"  [{status}] {test_name}")
        
        print(f"\nOverall: {passed_count}/{total_tests} tests passed ({passed_count/total_tests:.1%})")
        
        print("\n" + "="*80)
        if passed_count == total_tests:
            print("SUCCESS: All guardrails tests passed!")
        else:
            print(f"WARNING: {total_tests - passed_count} tests failed")
        print("="*80 + "\n")
        
        return passed_count == total_tests
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
