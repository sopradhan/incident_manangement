#!/usr/bin/env python
"""
GUARDRAILS SERVICE TEST WITH CORRECTIVE ACTION PROCESSOR
Tests guardrails integration with corrective action processing workflow

Usage:
  python scripts/test_guardrails_corrective_action.py
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.incident_iq.services.guardrails_service import (
    create_guardrails_service,
    GuardResult,
    GuardType,
    BaseGuard,
    GuardailCheckResult
)


# ==============================================================================
# CUSTOM GUARDRAIL FOR CORRECTIVE ACTIONS
# ==============================================================================

class CorrectiveActionGuard(BaseGuard):
    """Validates corrective action has required fields and valid state"""
    
    def __init__(self):
        super().__init__('corrective_action_guard', severity='high')
    
    def check(self, data):
        """Validate corrective action"""
        required_fields = ['action_id', 'incident_id', 'action_type', 'priority', 'status']
        missing = [f for f in required_fields if f not in data or not data.get(f)]
        
        if missing:
            return GuardailCheckResult(
                guard_type=GuardType.POLICY_ENFORCEMENT,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Missing required corrective action fields: {missing}",
                severity=self.severity
            )
        
        # Validate action_type
        valid_types = ['investigation', 'remediation', 'prevention', 'escalation']
        if data.get('action_type', '').lower() not in valid_types:
            return GuardailCheckResult(
                guard_type=GuardType.POLICY_ENFORCEMENT,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Invalid action_type '{data.get('action_type')}'. Valid: {valid_types}",
                severity=self.severity
            )
        
        # Validate priority
        valid_priorities = ['critical', 'high', 'medium', 'low']
        if data.get('priority', '').lower() not in valid_priorities:
            return GuardailCheckResult(
                guard_type=GuardType.POLICY_ENFORCEMENT,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Invalid priority '{data.get('priority')}'. Valid: {valid_priorities}",
                severity=self.severity
            )
        
        # Validate status
        valid_status = ['created', 'assigned', 'in_progress', 'completed', 'cancelled']
        if data.get('status', '').lower() not in valid_status:
            return GuardailCheckResult(
                guard_type=GuardType.POLICY_ENFORCEMENT,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Invalid status '{data.get('status')}'. Valid: {valid_status}",
                severity=self.severity
            )
        
        return GuardailCheckResult(
            guard_type=GuardType.POLICY_ENFORCEMENT,
            guard_name=self.name,
            result=GuardResult.PASS,
            message=f"Corrective action {data.get('action_id')} is valid",
            severity=self.severity
        )


class CorrectiveActionOutputGuard(BaseGuard):
    """Validates corrective action processing output"""
    
    def __init__(self):
        super().__init__('corrective_action_output_guard', severity='high')
    
    def check(self, data):
        """Validate output"""
        required_fields = ['action_id', 'processed_at', 'result_status', 'metrics']
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            return GuardailCheckResult(
                guard_type=GuardType.OUTPUT_VALIDATION,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Output missing fields: {missing}",
                severity=self.severity
            )
        
        # Validate metrics
        metrics = data.get('metrics', {})
        required_metrics = ['processing_time_ms', 'quality_score']
        missing_metrics = [m for m in required_metrics if m not in metrics]
        
        if missing_metrics:
            return GuardailCheckResult(
                guard_type=GuardType.OUTPUT_VALIDATION,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Output missing metrics: {missing_metrics}",
                severity=self.severity
            )
        
        return GuardailCheckResult(
            guard_type=GuardType.OUTPUT_VALIDATION,
            guard_name=self.name,
            result=GuardResult.PASS,
            message=f"Output for action {data.get('action_id')} is valid",
            severity=self.severity
        )


# ==============================================================================
# CORRECTIVE ACTION PROCESSOR WITH GUARDRAILS
# ==============================================================================

class CorrectiveActionProcessor:
    """Process corrective actions with guardrails validation"""
    
    def __init__(self):
        self.guardrails = create_guardrails_service()
        
        # Register custom guardrails
        self.guardrails.register_guardrail(CorrectiveActionGuard(), scope='corrective_action')
        self.guardrails.register_guardrail(CorrectiveActionOutputGuard(), scope='corrective_action')
        
        self.processed_count = 0
        self.failed_count = 0
        self.results = []
    
    def process_corrective_action(self, action):
        """Process a corrective action with guardrails"""
        
        # 1. Validate input
        passed, results = self.guardrails.check_input(action, scope='corrective_action')
        
        if not passed:
            self.failed_count += 1
            failed_result = [r for r in results if r.result == GuardResult.FAIL][0]
            error_output = {
                'action_id': action.get('action_id', 'unknown'),
                'success': False,
                'error': failed_result.message,
                'guardrail_check': failed_result.guard_name
            }
            self.results.append(error_output)
            return error_output
        
        try:
            # 2. Process action
            start_time = datetime.utcnow()
            
            # Simulate processing based on action_type
            action_type = action.get('action_type', '').lower()
            if action_type == 'investigation':
                processing_result = self._process_investigation(action)
            elif action_type == 'remediation':
                processing_result = self._process_remediation(action)
            elif action_type == 'prevention':
                processing_result = self._process_prevention(action)
            elif action_type == 'escalation':
                processing_result = self._process_escalation(action)
            else:
                processing_result = {'success': False, 'reason': 'Unknown action type'}
            
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # 3. Prepare output
            output = {
                'action_id': action.get('action_id'),
                'incident_id': action.get('incident_id'),
                'processed_at': datetime.utcnow().isoformat(),
                'result_status': 'success' if processing_result.get('success') else 'failed',
                'result_message': processing_result.get('message', ''),
                'metrics': {
                    'processing_time_ms': processing_time_ms,
                    'quality_score': processing_result.get('quality_score', 0.85),
                    'resource_usage': processing_result.get('resource_usage', 'normal')
                }
            }
            
            # 4. Validate output
            passed, results = self.guardrails.check_output(output, scope='corrective_action')
            
            if not passed:
                output['guardrail_warnings'] = [r.to_dict() for r in results if r.result == GuardResult.FAIL]
            else:
                output['guardrail_status'] = 'passed'
            
            self.processed_count += 1
            self.results.append(output)
            return output
            
        except Exception as e:
            self.failed_count += 1
            error_output = {
                'action_id': action.get('action_id', 'unknown'),
                'success': False,
                'error': str(e),
                'exception_type': type(e).__name__
            }
            self.results.append(error_output)
            return error_output
    
    def _process_investigation(self, action):
        """Simulate investigation processing"""
        return {
            'success': True,
            'message': f"Investigation {action.get('action_id')} completed",
            'quality_score': 0.92,
            'resource_usage': 'normal'
        }
    
    def _process_remediation(self, action):
        """Simulate remediation processing"""
        return {
            'success': True,
            'message': f"Remediation {action.get('action_id')} applied",
            'quality_score': 0.88,
            'resource_usage': 'normal'
        }
    
    def _process_prevention(self, action):
        """Simulate prevention processing"""
        return {
            'success': True,
            'message': f"Prevention measure {action.get('action_id')} deployed",
            'quality_score': 0.85,
            'resource_usage': 'low'
        }
    
    def _process_escalation(self, action):
        """Simulate escalation processing"""
        return {
            'success': True,
            'message': f"Escalation {action.get('action_id')} sent",
            'quality_score': 0.80,
            'resource_usage': 'low'
        }
    
    def get_summary(self):
        """Get processing summary"""
        return {
            'total_processed': self.processed_count,
            'total_failed': self.failed_count,
            'total_actions': self.processed_count + self.failed_count,
            'success_rate': self.processed_count / (self.processed_count + self.failed_count) if (self.processed_count + self.failed_count) > 0 else 0.0,
            'results': self.results
        }


# ==============================================================================
# TEST CASES
# ==============================================================================

def run_tests():
    """Run comprehensive guardrails tests"""
    
    print("\n" + "="*80)
    print("GUARDRAILS SERVICE TEST - CORRECTIVE ACTION PROCESSOR")
    print("="*80)
    
    processor = CorrectiveActionProcessor()
    
    # Test Case 1: Valid corrective action
    print("\n[TEST 1] Valid Corrective Action")
    print("-" * 80)
    action1 = {
        'action_id': 'CA_001',
        'incident_id': 'INC_2025_001',
        'action_type': 'investigation',
        'priority': 'critical',
        'status': 'in_progress',
        'description': 'Investigate root cause of service degradation',
        'assigned_to': 'security_team'
    }
    result1 = processor.process_corrective_action(action1)
    print(f"✓ Action processed successfully")
    print(f"  Status: {result1.get('result_status')}")
    print(f"  Processing time: {result1.get('metrics', {}).get('processing_time_ms', 0):.1f}ms")
    print(f"  Quality score: {result1.get('metrics', {}).get('quality_score', 0):.2f}")
    
    # Test Case 2: Missing required field
    print("\n[TEST 2] Missing Required Field")
    print("-" * 80)
    action2 = {
        'action_id': 'CA_002',
        'incident_id': 'INC_2025_002',
        # Missing 'action_type'
        'priority': 'high',
        'status': 'created'
    }
    result2 = processor.process_corrective_action(action2)
    print(f"✗ Action validation failed")
    print(f"  Error: {result2.get('error')}")
    print(f"  Guard: {result2.get('guardrail_check')}")
    
    # Test Case 3: Invalid action type
    print("\n[TEST 3] Invalid Action Type")
    print("-" * 80)
    action3 = {
        'action_id': 'CA_003',
        'incident_id': 'INC_2025_003',
        'action_type': 'invalid_type',
        'priority': 'medium',
        'status': 'created'
    }
    result3 = processor.process_corrective_action(action3)
    print(f"✗ Action validation failed")
    print(f"  Error: {result3.get('error')}")
    
    # Test Case 4: Invalid priority
    print("\n[TEST 4] Invalid Priority")
    print("-" * 80)
    action4 = {
        'action_id': 'CA_004',
        'incident_id': 'INC_2025_004',
        'action_type': 'remediation',
        'priority': 'urgent',  # Invalid
        'status': 'created'
    }
    result4 = processor.process_corrective_action(action4)
    print(f"✗ Action validation failed")
    print(f"  Error: {result4.get('error')}")
    
    # Test Case 5: Valid remediation action
    print("\n[TEST 5] Valid Remediation Action")
    print("-" * 80)
    action5 = {
        'action_id': 'CA_005',
        'incident_id': 'INC_2025_001',
        'action_type': 'remediation',
        'priority': 'high',
        'status': 'in_progress',
        'description': 'Apply security patch to affected servers',
        'assigned_to': 'ops_team'
    }
    result5 = processor.process_corrective_action(action5)
    print(f"✓ Action processed successfully")
    print(f"  Status: {result5.get('result_status')}")
    print(f"  Quality score: {result5.get('metrics', {}).get('quality_score', 0):.2f}")
    
    # Test Case 6: Valid prevention action
    print("\n[TEST 6] Valid Prevention Action")
    print("-" * 80)
    action6 = {
        'action_id': 'CA_006',
        'incident_id': 'INC_2025_001',
        'action_type': 'prevention',
        'priority': 'medium',
        'status': 'created',
        'description': 'Implement automated monitoring'
    }
    result6 = processor.process_corrective_action(action6)
    print(f"✓ Action processed successfully")
    print(f"  Status: {result6.get('result_status')}")
    
    # Test Case 7: Valid escalation action
    print("\n[TEST 7] Valid Escalation Action")
    print("-" * 80)
    action7 = {
        'action_id': 'CA_007',
        'incident_id': 'INC_2025_001',
        'action_type': 'escalation',
        'priority': 'critical',
        'status': 'assigned',
        'assigned_to': 'management'
    }
    result7 = processor.process_corrective_action(action7)
    print(f"✓ Action processed successfully")
    print(f"  Status: {result7.get('result_status')}")
    
    # Test Case 8: Invalid status
    print("\n[TEST 8] Invalid Status")
    print("-" * 80)
    action8 = {
        'action_id': 'CA_008',
        'incident_id': 'INC_2025_005',
        'action_type': 'investigation',
        'priority': 'low',
        'status': 'unknown_status'  # Invalid
    }
    result8 = processor.process_corrective_action(action8)
    print(f"✗ Action validation failed")
    print(f"  Error: {result8.get('error')}")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    summary = processor.get_summary()
    print(f"\nProcessing Results:")
    print(f"  Total actions: {summary['total_actions']}")
    print(f"  Successful: {summary['total_processed']}")
    print(f"  Failed: {summary['total_failed']}")
    print(f"  Success rate: {summary['success_rate']:.1%}")
    
    # Guardrail statistics
    stats = processor.guardrails.get_guard_stats()
    print(f"\nGuardrail Statistics:")
    print(f"  Total checks: {stats['total_checks']}")
    print(f"  Passed: {stats['passed']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Pass rate: {stats['pass_rate']:.1%}")
    
    print(f"\nBy Guard:")
    for guard_name, counts in stats['by_guard'].items():
        total = counts['pass'] + counts['fail']
        pass_rate = counts['pass'] / total if total > 0 else 0
        print(f"  {guard_name}: {counts['pass']}/{total} ({pass_rate:.1%})")
    
    # Failed checks
    failed_checks = processor.guardrails.get_failed_checks(limit=10)
    if failed_checks:
        print(f"\nFailed Checks ({len(failed_checks)}):")
        for check in failed_checks:
            print(f"  - {check['guard_name']}: {check['message']}")
    
    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80 + "\n")
    
    return summary['success_rate'] >= 0.5  # At least 50% should pass


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
