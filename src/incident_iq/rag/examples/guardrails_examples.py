"""
GUARDRAILS SERVICE - PRACTICAL EXAMPLES
Demonstrates guardrails usage patterns in real scenarios

File: src/incident_iq/rag/examples/guardrails_examples.py
"""

import json
from src.incident_iq.services.guardrails_service import (
    create_guardrails_service,
    SchemaValidationGuard,
    RangeValidationGuard,
    ContentSizeGuard,
    QualityGuard,
    RLActionBoundsGuard,
    RLRewardClippingGuard,
    RLStateValidationGuard,
    RateLimitGuard,
    ResourceProtectionGuard
)


# ==============================================================================
# EXAMPLE 1: INGESTION WITH GUARDRAILS
# ==============================================================================

def example_ingestion_with_guardrails():
    """
    Example: Document ingestion with input/output guardrails
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: INGESTION WITH GUARDRAILS")
    print("="*80)
    
    # Initialize guardrails
    guardrails = create_guardrails_service()
    
    # Test Case 1: Valid document
    print("\nTest 1: Valid document")
    valid_doc = {
        'document_id': 'doc_001',
        'content': 'This is a valid incident management document.',
        'metadata': {'source': 'api', 'priority': 'high'}
    }
    passed, results = guardrails.check_ingestion_input(valid_doc)
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        if r.result.value != 'pass':
            print(f"    - {r.guard_name}: {r.message}")
    
    # Test Case 2: Missing required field
    print("\nTest 2: Missing required field (content)")
    invalid_doc = {
        'document_id': 'doc_002',
        'metadata': {'source': 'api'}
    }
    passed, results = guardrails.check_ingestion_input(invalid_doc)
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        if r.result.value == 'fail':
            print(f"    ✗ {r.guard_name}: {r.message}")
    
    # Test Case 3: Content too large
    print("\nTest 3: Content exceeds size limit")
    oversized_doc = {
        'document_id': 'doc_003',
        'content': 'x' * (15 * 1024 * 1024),  # 15MB
        'metadata': {}
    }
    passed, results = guardrails.check_ingestion_input(oversized_doc)
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        if r.result.value == 'fail':
            print(f"    ✗ {r.guard_name}: {r.message}")


# ==============================================================================
# EXAMPLE 2: RETRIEVAL WITH GUARDRAILS
# ==============================================================================

def example_retrieval_with_guardrails():
    """
    Example: Query retrieval with input validation and resource protection
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: RETRIEVAL WITH GUARDRAILS")
    print("="*80)
    
    guardrails = create_guardrails_service()
    
    # Test Case 1: Valid query
    print("\nTest 1: Valid query")
    valid_query = {
        'query': 'What are the steps to resolve a critical incident?',
        'top_k': 5
    }
    passed, results = guardrails.check_retrieval_input(valid_query)
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        print(f"    - {r.guard_name}: {r.message}")
    
    # Test Case 2: top_k exceeds maximum
    print("\nTest 2: top_k exceeds maximum")
    invalid_query = {
        'query': 'What are the steps to resolve a critical incident?',
        'top_k': 150  # Exceeds max of 100
    }
    passed, results = guardrails.check_retrieval_input(invalid_query)
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        if r.result.value == 'fail':
            print(f"    ✗ {r.guard_name}: {r.message}")
    
    # Test Case 3: Query validation with resource limits
    print("\nTest 3: Query with resource output check")
    query_output = {
        'query': 'sample query',
        'results': ['result1', 'result2'],
        'top_k': 2,
        'quality_score': 0.85,
        'tokens_used': 150,
        'output': 'results' * 100
    }
    passed, results = guardrails.check_output(query_output, scope='retrieval')
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        print(f"    - {r.guard_name}: {r.message}")


# ==============================================================================
# EXAMPLE 3: RL ACTION VALIDATION
# ==============================================================================

def example_rl_action_validation():
    """
    Example: RL agent action validation with guardrails
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: RL ACTION VALIDATION")
    print("="*80)
    
    guardrails = create_guardrails_service()
    
    # Test Case 1: Valid REINDEX action
    print("\nTest 1: Valid REINDEX action")
    valid_action = {
        'action': 'REINDEX',
        'parameters': {
            'new_chunk_size': 512,
            'new_overlap': 0.1
        }
    }
    passed, results = guardrails.check_rl_action(valid_action)
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        print(f"    - {r.guard_name}: {r.message}")
    
    # Test Case 2: Invalid action
    print("\nTest 2: Invalid action name")
    invalid_action = {
        'action': 'INVALID_ACTION',
        'parameters': {}
    }
    passed, results = guardrails.check_rl_action(invalid_action)
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        if r.result.value == 'fail':
            print(f"    ✗ {r.guard_name}: {r.message}")
    
    # Test Case 3: Parameter out of bounds
    print("\nTest 3: Parameter out of bounds")
    out_of_bounds_action = {
        'action': 'REINDEX',
        'parameters': {
            'new_chunk_size': 5000,  # Exceeds max of 2048
            'new_overlap': 0.1
        }
    }
    passed, results = guardrails.check_rl_action(out_of_bounds_action)
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        if r.result.value == 'fail':
            print(f"    ✗ {r.guard_name}: {r.message}")


# ==============================================================================
# EXAMPLE 4: RL REWARD CLIPPING
# ==============================================================================

def example_rl_reward_clipping():
    """
    Example: RL reward validation and clipping
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: RL REWARD CLIPPING")
    print("="*80)
    
    guardrails = create_guardrails_service()
    
    # Test Case 1: Normal reward (within bounds)
    print("\nTest 1: Normal reward within bounds")
    normal_reward = {'reward': 0.5}
    passed, results = guardrails.check_rl_reward(normal_reward)
    print(f"  Input reward: 0.5")
    print(f"  Clipped reward: {normal_reward['reward']:.3f}")
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    
    # Test Case 2: Reward exceeds maximum
    print("\nTest 2: Reward exceeds maximum")
    large_reward = {'reward': 2.5}
    passed, results = guardrails.check_rl_reward(large_reward)
    print(f"  Input reward: 2.5")
    print(f"  Clipped reward: {large_reward['reward']:.3f}")
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        print(f"    - {r.message}")
    
    # Test Case 3: Negative reward (below minimum)
    print("\nTest 3: Negative reward below minimum")
    negative_reward = {'reward': -2.0}
    passed, results = guardrails.check_rl_reward(negative_reward)
    print(f"  Input reward: -2.0")
    print(f"  Clipped reward: {negative_reward['reward']:.3f}")
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        print(f"    - {r.message}")


# ==============================================================================
# EXAMPLE 5: RL STATE VALIDATION
# ==============================================================================

def example_rl_state_validation():
    """
    Example: RL state validation for optimization
    """
    print("\n" + "="*80)
    print("EXAMPLE 5: RL STATE VALIDATION")
    print("="*80)
    
    guardrails = create_guardrails_service()
    
    # Test Case 1: Valid state with all features
    print("\nTest 1: Valid state with all features")
    valid_state = {
        'features': {
            'avg_quality_score': 0.78,
            'low_quality_doc_count': 5,
            'total_query_count': 1200,
            'avg_response_time_ms': 450,
            'total_tokens_used': 25000,
            'reindex_attempts': 2
        }
    }
    passed, results = guardrails.check_rl_action(valid_state)
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        if 'state' in r.guard_name:
            print(f"    - {r.guard_name}: {r.message}")
    
    # Test Case 2: Missing required features
    print("\nTest 2: Missing required features")
    incomplete_state = {
        'features': {
            'avg_quality_score': 0.78,
            'low_quality_doc_count': 5
            # Missing other features
        }
    }
    passed, results = guardrails.check_rl_action(incomplete_state)
    print(f"  Result: {'PASS' if passed else 'FAIL'}")
    for r in results:
        if 'state' in r.guard_name and r.result.value == 'fail':
            print(f"    ✗ {r.message}")


# ==============================================================================
# EXAMPLE 6: RATE LIMITING
# ==============================================================================

def example_rate_limiting():
    """
    Example: Rate limiting in action
    """
    print("\n" + "="*80)
    print("EXAMPLE 6: RATE LIMITING")
    print("="*80)
    
    # Create guardrails with low rate limit for demo
    guardrails = create_guardrails_service()
    
    # Lower the rate limit for demonstration
    for guard in guardrails.guardrails.get('ingestion', []):
        if isinstance(guard, RateLimitGuard):
            guard.max_requests_per_minute = 3  # Allow only 3 per minute
    
    agent_id = 'test_agent_123'
    
    print(f"\nRate limit: 3 requests per minute for agent '{agent_id}'")
    print("Sending requests...")
    
    for i in range(5):
        request = {'agent_id': agent_id}
        passed, results = guardrails.check_ingestion_input(request)
        rate_result = [r for r in results if 'rate_limit' in r.guard_name][0]
        status = '✓ PASS' if passed else '✗ FAIL'
        print(f"  Request {i+1}: {status} - {rate_result.message}")


# ==============================================================================
# EXAMPLE 7: GUARDRAIL MONITORING & STATISTICS
# ==============================================================================

def example_guardrail_monitoring():
    """
    Example: Monitoring guardrails and getting statistics
    """
    print("\n" + "="*80)
    print("EXAMPLE 7: GUARDRAIL MONITORING & STATISTICS")
    print("="*80)
    
    guardrails = create_guardrails_service()
    
    # Run some guardrail checks
    test_cases = [
        {'document_id': 'doc_1', 'content': 'valid content'},  # Should pass
        {'content': 'missing id'},  # Should fail
        {'document_id': 'doc_2', 'content': 'x' * (15 * 1024 * 1024)},  # Should fail
    ]
    
    for doc in test_cases:
        guardrails.check_ingestion_input(doc)
    
    # Get statistics
    stats = guardrails.get_guard_stats()
    
    print(f"\nGuardrail Statistics:")
    print(f"  Total checks: {stats['total_checks']}")
    print(f"  Passed: {stats['passed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Pass rate: {stats['pass_rate']:.1%}")
    
    print(f"\nBy Guard:")
    for guard_name, counts in stats['by_guard'].items():
        pass_count = counts['pass']
        fail_count = counts['fail']
        total = pass_count + fail_count
        pass_rate = pass_count / total if total > 0 else 0
        print(f"  {guard_name}: {pass_count}/{total} passed ({pass_rate:.1%})")
    
    # Get failed checks
    print(f"\nFailed Checks:")
    failed = guardrails.get_failed_checks(limit=10)
    for check in failed:
        print(f"  - {check['guard_name']}: {check['message']}")


# ==============================================================================
# EXAMPLE 8: CUSTOM GUARDRAIL
# ==============================================================================

def example_custom_guardrail():
    """
    Example: Creating and registering custom guardrails
    """
    print("\n" + "="*80)
    print("EXAMPLE 8: CUSTOM GUARDRAIL")
    print("="*80)
    
    from src.incident_iq.services.guardrails_service import (
        BaseGuard, GuardType, GuardResult, GuardailCheckResult
    )
    
    # Define custom guardrail
    class DepartmentGuard(BaseGuard):
        """Validate document has valid department"""
        
        VALID_DEPARTMENTS = ['finance', 'operations', 'hr', 'it']
        
        def __init__(self):
            super().__init__('department_guard')
        
        def check(self, data) -> GuardailCheckResult:
            department = data.get('metadata', {}).get('department', '').lower()
            
            if not department:
                return GuardailCheckResult(
                    guard_type=GuardType.POLICY_ENFORCEMENT,
                    guard_name=self.name,
                    result=GuardResult.FAIL,
                    message="Missing department in metadata",
                    severity="high"
                )
            
            if department not in self.VALID_DEPARTMENTS:
                return GuardailCheckResult(
                    guard_type=GuardType.POLICY_ENFORCEMENT,
                    guard_name=self.name,
                    result=GuardResult.FAIL,
                    message=f"Invalid department '{department}'. Valid: {self.VALID_DEPARTMENTS}",
                    severity="high"
                )
            
            return GuardailCheckResult(
                guard_type=GuardType.POLICY_ENFORCEMENT,
                guard_name=self.name,
                result=GuardResult.PASS,
                message=f"Department '{department}' is valid",
                severity="low"
            )
    
    # Create guardrails and register custom guard
    guardrails = create_guardrails_service()
    guardrails.register_guardrail(DepartmentGuard(), scope='ingestion')
    
    # Test custom guardrail
    print("\nTest 1: Valid department")
    doc1 = {
        'document_id': 'doc_1',
        'content': 'content',
        'metadata': {'department': 'Finance'}
    }
    passed, results = guardrails.check_ingestion_input(doc1)
    custom_result = [r for r in results if r.guard_name == 'department_guard'][0]
    print(f"  Result: {'PASS' if custom_result.result.value == 'pass' else 'FAIL'}")
    print(f"  Message: {custom_result.message}")
    
    print("\nTest 2: Invalid department")
    doc2 = {
        'document_id': 'doc_2',
        'content': 'content',
        'metadata': {'department': 'Marketing'}
    }
    passed, results = guardrails.check_ingestion_input(doc2)
    custom_result = [r for r in results if r.guard_name == 'department_guard'][0]
    print(f"  Result: {'PASS' if custom_result.result.value == 'pass' else 'FAIL'}")
    print(f"  Message: {custom_result.message}")


# ==============================================================================
# MAIN: RUN ALL EXAMPLES
# ==============================================================================

def main():
    """Run all examples"""
    examples = [
        example_ingestion_with_guardrails,
        example_retrieval_with_guardrails,
        example_rl_action_validation,
        example_rl_reward_clipping,
        example_rl_state_validation,
        example_rate_limiting,
        example_guardrail_monitoring,
        example_custom_guardrail
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")
    
    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETED")
    print("="*80)


if __name__ == '__main__':
    main()
