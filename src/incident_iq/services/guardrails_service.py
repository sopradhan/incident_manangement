"""
Guardrails Service - Centralized policy enforcement and validation service
Used by all agents (ingestion, retrieval, healing) and RL agents

Guardrails provide:
  1. Input validation (schema, format, constraints)
  2. Output validation (quality checks, safety checks)
  3. Policy enforcement (business rules, security policies)
  4. RL-specific guardrails (action bounds, reward clipping)
  5. Rate limiting and resource protection
  6. Audit logging for compliance
"""
import json
import logging
import sqlite3
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class GuardType(Enum):
    """Types of guardrails"""
    INPUT_VALIDATION = "input_validation"
    OUTPUT_VALIDATION = "output_validation"
    POLICY_ENFORCEMENT = "policy_enforcement"
    RL_ACTION_BOUNDS = "rl_action_bounds"
    RATE_LIMITING = "rate_limiting"
    RESOURCE_PROTECTION = "resource_protection"
    SECURITY_POLICY = "security_policy"
    COMPLIANCE_AUDIT = "compliance_audit"


class GuardResult(Enum):
    """Guardrail check results"""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    DEFER = "defer"  # For critical guardrails that need human review


@dataclass
class GuardailCheckResult:
    """Result of a guardrail check"""
    guard_type: GuardType
    guard_name: str
    result: GuardResult
    message: str
    severity: str  # critical, high, medium, low
    metadata: Dict = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'guard_type': self.guard_type.value,
            'guard_name': self.guard_name,
            'result': self.result.value,
            'message': self.message,
            'severity': self.severity,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class BaseGuard(ABC):
    """Base class for all guardrails"""
    
    def __init__(self, name: str, severity: str = "high"):
        self.name = name
        self.severity = severity
    
    @abstractmethod
    def check(self, data: Dict) -> GuardailCheckResult:
        """Check if data passes this guardrail"""
        pass


# ==============================================================================
# INPUT VALIDATION GUARDRAILS
# ==============================================================================

class SchemaValidationGuard(BaseGuard):
    """Validates data against schema"""
    
    def __init__(self, schema: Dict, name: str = "schema_validation"):
        super().__init__(name)
        self.schema = schema
    
    def check(self, data: Dict) -> GuardailCheckResult:
        """Validate data against schema"""
        try:
            # Check required fields
            required_fields = self.schema.get('required', [])
            missing = [f for f in required_fields if f not in data]
            if missing:
                return GuardailCheckResult(
                    guard_type=GuardType.INPUT_VALIDATION,
                    guard_name=self.name,
                    result=GuardResult.FAIL,
                    message=f"Missing required fields: {missing}",
                    severity=self.severity
                )
            
            # Check field types
            properties = self.schema.get('properties', {})
            for field, field_schema in properties.items():
                if field in data:
                    expected_type = field_schema.get('type')
                    actual_type = type(data[field]).__name__
                    if not self._matches_type(data[field], expected_type):
                        return GuardailCheckResult(
                            guard_type=GuardType.INPUT_VALIDATION,
                            guard_name=self.name,
                            result=GuardResult.FAIL,
                            message=f"Field '{field}': expected {expected_type}, got {actual_type}",
                            severity=self.severity
                        )
            
            return GuardailCheckResult(
                guard_type=GuardType.INPUT_VALIDATION,
                guard_name=self.name,
                result=GuardResult.PASS,
                message="Schema validation passed",
                severity=self.severity
            )
        except Exception as e:
            return GuardailCheckResult(
                guard_type=GuardType.INPUT_VALIDATION,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Validation error: {str(e)}",
                severity="critical"
            )
    
    def _matches_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'object': dict,
            'array': list
        }
        expected = type_map.get(expected_type)
        return isinstance(value, expected) if expected else True


class RangeValidationGuard(BaseGuard):
    """Validates numeric values are within range"""
    
    def __init__(self, field: str, min_val: float = None, max_val: float = None, name: str = None):
        super().__init__(name or f"range_validation_{field}")
        self.field = field
        self.min_val = min_val
        self.max_val = max_val
    
    def check(self, data: Dict) -> GuardailCheckResult:
        """Validate value is in range"""
        if self.field not in data:
            return GuardailCheckResult(
                guard_type=GuardType.INPUT_VALIDATION,
                guard_name=self.name,
                result=GuardResult.PASS,
                message=f"Field '{self.field}' not present (optional)",
                severity=self.severity
            )
        
        value = data[self.field]
        
        if self.min_val is not None and value < self.min_val:
            return GuardailCheckResult(
                guard_type=GuardType.INPUT_VALIDATION,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Field '{self.field}' = {value} below minimum {self.min_val}",
                severity=self.severity
            )
        
        if self.max_val is not None and value > self.max_val:
            return GuardailCheckResult(
                guard_type=GuardType.INPUT_VALIDATION,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Field '{self.field}' = {value} exceeds maximum {self.max_val}",
                severity=self.severity
            )
        
        return GuardailCheckResult(
            guard_type=GuardType.INPUT_VALIDATION,
            guard_name=self.name,
            result=GuardResult.PASS,
            message=f"Field '{self.field}' value {value} in range [{self.min_val}, {self.max_val}]",
            severity=self.severity
        )


class ContentSizeGuard(BaseGuard):
    """Validates content size limits"""
    
    def __init__(self, field: str, max_size_kb: int, name: str = None):
        super().__init__(name or f"content_size_{field}")
        self.field = field
        self.max_size_kb = max_size_kb
    
    def check(self, data: Dict) -> GuardailCheckResult:
        """Validate content size"""
        if self.field not in data:
            return GuardailCheckResult(
                guard_type=GuardType.INPUT_VALIDATION,
                guard_name=self.name,
                result=GuardResult.PASS,
                message=f"Field '{self.field}' not present",
                severity=self.severity
            )
        
        content = data[self.field]
        size_kb = len(str(content).encode('utf-8')) / 1024
        
        if size_kb > self.max_size_kb:
            return GuardailCheckResult(
                guard_type=GuardType.INPUT_VALIDATION,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Content size {size_kb:.1f}KB exceeds limit {self.max_size_kb}KB",
                severity=self.severity
            )
        
        return GuardailCheckResult(
            guard_type=GuardType.INPUT_VALIDATION,
            guard_name=self.name,
            result=GuardResult.PASS,
            message=f"Content size {size_kb:.1f}KB within limit",
            severity=self.severity
        )


# ==============================================================================
# OUTPUT VALIDATION GUARDRAILS
# ==============================================================================

class QualityGuard(BaseGuard):
    """Validates output quality metrics"""
    
    def __init__(self, min_quality_score: float = 0.7, name: str = "quality_guard"):
        super().__init__(name)
        self.min_quality_score = min_quality_score
    
    def check(self, data: Dict) -> GuardailCheckResult:
        """Validate quality score"""
        quality_score = data.get('quality_score', 0.0)
        
        if quality_score < self.min_quality_score:
            return GuardailCheckResult(
                guard_type=GuardType.OUTPUT_VALIDATION,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Quality score {quality_score:.3f} below threshold {self.min_quality_score}",
                severity=self.severity,
                metadata={'quality_score': quality_score, 'threshold': self.min_quality_score}
            )
        
        return GuardailCheckResult(
            guard_type=GuardType.OUTPUT_VALIDATION,
            guard_name=self.name,
            result=GuardResult.PASS,
            message=f"Quality score {quality_score:.3f} meets threshold",
            severity=self.severity,
            metadata={'quality_score': quality_score}
        )


class ComplianceGuard(BaseGuard):
    """Validates compliance with policies"""
    
    def __init__(self, required_fields: List[str], name: str = "compliance_guard"):
        super().__init__(name)
        self.required_fields = required_fields
    
    def check(self, data: Dict) -> GuardailCheckResult:
        """Validate compliance"""
        missing = [f for f in self.required_fields if f not in data or not data[f]]
        
        if missing:
            return GuardailCheckResult(
                guard_type=GuardType.OUTPUT_VALIDATION,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Missing compliance fields: {missing}",
                severity="critical"
            )
        
        return GuardailCheckResult(
            guard_type=GuardType.OUTPUT_VALIDATION,
            guard_name=self.name,
            result=GuardResult.PASS,
            message="Compliance requirements met",
            severity=self.severity
        )


# ==============================================================================
# RL-SPECIFIC GUARDRAILS
# ==============================================================================

class RLActionBoundsGuard(BaseGuard):
    """Validates RL actions are within bounds"""
    
    def __init__(self, action_space: Dict[str, Dict], name: str = "rl_action_bounds"):
        super().__init__(name, severity="critical")
        self.action_space = action_space
    
    def check(self, data: Dict) -> GuardailCheckResult:
        """Validate action is valid"""
        action_name = data.get('action')
        if not action_name:
            return GuardailCheckResult(
                guard_type=GuardType.RL_ACTION_BOUNDS,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message="Action not specified",
                severity=self.severity
            )
        
        if action_name not in self.action_space:
            return GuardailCheckResult(
                guard_type=GuardType.RL_ACTION_BOUNDS,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Unknown action '{action_name}'. Valid actions: {list(self.action_space.keys())}",
                severity=self.severity
            )
        
        action_spec = self.action_space[action_name]
        action_params = data.get('parameters', {})
        
        # Validate parameters are within bounds
        param_bounds = action_spec.get('parameter_bounds', {})
        for param, bounds in param_bounds.items():
            if param in action_params:
                value = action_params[param]
                if 'min' in bounds and value < bounds['min']:
                    return GuardailCheckResult(
                        guard_type=GuardType.RL_ACTION_BOUNDS,
                        guard_name=self.name,
                        result=GuardResult.FAIL,
                        message=f"Parameter '{param}' = {value} below minimum {bounds['min']}",
                        severity=self.severity
                    )
                if 'max' in bounds and value > bounds['max']:
                    return GuardailCheckResult(
                        guard_type=GuardType.RL_ACTION_BOUNDS,
                        guard_name=self.name,
                        result=GuardResult.FAIL,
                        message=f"Parameter '{param}' = {value} exceeds maximum {bounds['max']}",
                        severity=self.severity
                    )
        
        return GuardailCheckResult(
            guard_type=GuardType.RL_ACTION_BOUNDS,
            guard_name=self.name,
            result=GuardResult.PASS,
            message=f"Action '{action_name}' with parameters within bounds",
            severity=self.severity
        )


class RLRewardClippingGuard(BaseGuard):
    """Validates and clips RL rewards to safe bounds"""
    
    def __init__(self, min_reward: float = -1.0, max_reward: float = 1.0, 
                 name: str = "rl_reward_clipping"):
        super().__init__(name)
        self.min_reward = min_reward
        self.max_reward = max_reward
    
    def check(self, data: Dict) -> GuardailCheckResult:
        """Validate and clip reward"""
        reward = data.get('reward', 0.0)
        clipped_reward = np.clip(reward, self.min_reward, self.max_reward)
        
        if reward != clipped_reward:
            logger.warning(f"Reward {reward:.3f} clipped to [{self.min_reward}, {self.max_reward}]")
        
        data['reward'] = clipped_reward  # Modify in-place
        
        return GuardailCheckResult(
            guard_type=GuardType.RL_ACTION_BOUNDS,
            guard_name=self.name,
            result=GuardResult.PASS,
            message=f"Reward clipped to [{self.min_reward}, {self.max_reward}]: {reward:.3f} -> {clipped_reward:.3f}",
            severity=self.severity,
            metadata={'original_reward': reward, 'clipped_reward': clipped_reward}
        )


class RLStateValidationGuard(BaseGuard):
    """Validates RL state is valid and complete"""
    
    def __init__(self, required_features: List[str], name: str = "rl_state_validation"):
        super().__init__(name)
        self.required_features = required_features
    
    def check(self, data: Dict) -> GuardailCheckResult:
        """Validate state"""
        features = data.get('features', {})
        missing = [f for f in self.required_features if f not in features]
        
        if missing:
            return GuardailCheckResult(
                guard_type=GuardType.RL_ACTION_BOUNDS,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Missing state features: {missing}",
                severity=self.severity
            )
        
        # Validate feature ranges
        for feature, value in features.items():
            if not isinstance(value, (int, float)):
                return GuardailCheckResult(
                    guard_type=GuardType.RL_ACTION_BOUNDS,
                    guard_name=self.name,
                    result=GuardResult.FAIL,
                    message=f"Feature '{feature}' must be numeric, got {type(value).__name__}",
                    severity=self.severity
                )
        
        return GuardailCheckResult(
            guard_type=GuardType.RL_ACTION_BOUNDS,
            guard_name=self.name,
            result=GuardResult.PASS,
            message=f"State valid with all {len(self.required_features)} required features",
            severity=self.severity
        )


# ==============================================================================
# RATE LIMITING & RESOURCE PROTECTION
# ==============================================================================

class RateLimitGuard(BaseGuard):
    """Rate limiting guardrail"""
    
    def __init__(self, max_requests_per_minute: int = 100, 
                 name: str = "rate_limit"):
        super().__init__(name)
        self.max_requests_per_minute = max_requests_per_minute
        self.request_timestamps = {}
    
    def check(self, data: Dict) -> GuardailCheckResult:
        """Check rate limit"""
        agent_id = data.get('agent_id', 'unknown')
        now = datetime.utcnow()
        
        if agent_id not in self.request_timestamps:
            self.request_timestamps[agent_id] = []
        
        # Remove old timestamps
        cutoff = now - timedelta(minutes=1)
        self.request_timestamps[agent_id] = [
            ts for ts in self.request_timestamps[agent_id] if ts > cutoff
        ]
        
        # Check limit
        if len(self.request_timestamps[agent_id]) >= self.max_requests_per_minute:
            return GuardailCheckResult(
                guard_type=GuardType.RATE_LIMITING,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Rate limit exceeded: {len(self.request_timestamps[agent_id])} requests in last minute",
                severity="high"
            )
        
        # Record request
        self.request_timestamps[agent_id].append(now)
        
        return GuardailCheckResult(
            guard_type=GuardType.RATE_LIMITING,
            guard_name=self.name,
            result=GuardResult.PASS,
            message=f"Rate limit OK: {len(self.request_timestamps[agent_id])}/{self.max_requests_per_minute} requests",
            severity=self.severity
        )


class ResourceProtectionGuard(BaseGuard):
    """Protects system resources (memory, CPU, tokens)"""
    
    def __init__(self, max_tokens_per_request: int = 10000, 
                 max_output_size_mb: float = 10.0,
                 name: str = "resource_protection"):
        super().__init__(name)
        self.max_tokens_per_request = max_tokens_per_request
        self.max_output_size_mb = max_output_size_mb
    
    def check(self, data: Dict) -> GuardailCheckResult:
        """Check resource usage"""
        tokens_used = data.get('tokens_used', 0)
        output = data.get('output', '')
        output_size_mb = len(str(output).encode('utf-8')) / (1024 * 1024)
        
        if tokens_used > self.max_tokens_per_request:
            return GuardailCheckResult(
                guard_type=GuardType.RESOURCE_PROTECTION,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Token usage {tokens_used} exceeds limit {self.max_tokens_per_request}",
                severity="high"
            )
        
        if output_size_mb > self.max_output_size_mb:
            return GuardailCheckResult(
                guard_type=GuardType.RESOURCE_PROTECTION,
                guard_name=self.name,
                result=GuardResult.FAIL,
                message=f"Output size {output_size_mb:.1f}MB exceeds limit {self.max_output_size_mb}MB",
                severity="high"
            )
        
        return GuardailCheckResult(
            guard_type=GuardType.RESOURCE_PROTECTION,
            guard_name=self.name,
            result=GuardResult.PASS,
            message=f"Resource usage OK: {tokens_used} tokens, {output_size_mb:.1f}MB output",
            severity=self.severity
        )


# ==============================================================================
# GUARDRAILS SERVICE
# ==============================================================================

class GuardrailsService:
    """Central guardrails service managing all guardrails"""
    
    def __init__(self, db_path: str = None):
        self.guardrails: Dict[str, List[BaseGuard]] = {
            'ingestion': [],
            'retrieval': [],
            'healing': [],
            'rl_agent': [],
            'global': []
        }
        self.db_path = db_path
        self.check_history = []
        self.max_history = 10000
    
    # ========================================================================
    # GUARDRAIL REGISTRATION
    # ========================================================================
    
    def register_guardrail(self, guardrail: BaseGuard, scope: str = 'global'):
        """Register a guardrail"""
        if scope not in self.guardrails:
            self.guardrails[scope] = []
        self.guardrails[scope].append(guardrail)
        logger.info(f"Registered guardrail '{guardrail.name}' for scope '{scope}'")
    
    def register_ingestion_guardrails(self):
        """Register guardrails for ingestion agent"""
        # Input validation
        self.register_guardrail(
            SchemaValidationGuard({
                'required': ['document_id', 'content'],
                'properties': {
                    'document_id': {'type': 'string'},
                    'content': {'type': 'string'},
                    'metadata': {'type': 'object'}
                }
            }),
            'ingestion'
        )
        
        # Content size limit
        self.register_guardrail(
            ContentSizeGuard('content', max_size_kb=10000),
            'ingestion'
        )
        
        # Output quality
        self.register_guardrail(
            QualityGuard(min_quality_score=0.7),
            'ingestion'
        )
        
        # Rate limiting
        self.register_guardrail(
            RateLimitGuard(max_requests_per_minute=100),
            'ingestion'
        )
    
    def register_retrieval_guardrails(self):
        """Register guardrails for retrieval agent"""
        # Input validation
        self.register_guardrail(
            SchemaValidationGuard({
                'required': ['query', 'top_k'],
                'properties': {
                    'query': {'type': 'string'},
                    'top_k': {'type': 'integer'}
                }
            }),
            'retrieval'
        )
        
        # Range validation
        self.register_guardrail(
            RangeValidationGuard('top_k', min_val=1, max_val=100),
            'retrieval'
        )
        
        # Quality output
        self.register_guardrail(
            QualityGuard(min_quality_score=0.6),
            'retrieval'
        )
        
        # Resource protection
        self.register_guardrail(
            ResourceProtectionGuard(max_tokens_per_request=5000),
            'retrieval'
        )
    
    def register_rl_guardrails(self):
        """Register guardrails for RL agents"""
        # Action bounds
        action_space = {
            'REINDEX': {
                'description': 'Re-index with new chunk size',
                'parameter_bounds': {
                    'new_chunk_size': {'min': 256, 'max': 2048},
                    'new_overlap': {'min': 0.0, 'max': 0.5}
                }
            },
            'RESAMPLE': {
                'description': 'Resample low-quality chunks',
                'parameter_bounds': {
                    'resample_threshold': {'min': 0.5, 'max': 0.95},
                    'sample_size': {'min': 0.1, 'max': 1.0}
                }
            },
            'REEMBED': {
                'description': 'Re-embed with newer model',
                'parameter_bounds': {}
            },
            'NO_OP': {
                'description': 'Do nothing',
                'parameter_bounds': {}
            }
        }
        
        self.register_guardrail(
            RLActionBoundsGuard(action_space),
            'rl_agent'
        )
        
        # Reward clipping
        self.register_guardrail(
            RLRewardClippingGuard(min_reward=-1.0, max_reward=1.0),
            'rl_agent'
        )
        
        # State validation
        self.register_guardrail(
            RLStateValidationGuard([
                'avg_quality_score',
                'low_quality_doc_count',
                'total_query_count',
                'avg_response_time_ms',
                'total_tokens_used',
                'reindex_attempts'
            ]),
            'rl_agent'
        )
    
    # ========================================================================
    # GUARDRAIL CHECKING
    # ========================================================================
    
    def check_input(self, data: Dict, scope: str = 'global') -> Tuple[bool, List[GuardailCheckResult]]:
        """Check all input guardrails"""
        return self._check_guardrails(data, scope)
    
    def check_output(self, data: Dict, scope: str = 'global') -> Tuple[bool, List[GuardailCheckResult]]:
        """Check all output guardrails"""
        return self._check_guardrails(data, scope)
    
    def check_ingestion_input(self, data: Dict) -> Tuple[bool, List[GuardailCheckResult]]:
        """Check ingestion input"""
        return self.check_input(data, 'ingestion')
    
    def check_retrieval_input(self, data: Dict) -> Tuple[bool, List[GuardailCheckResult]]:
        """Check retrieval input"""
        return self.check_input(data, 'retrieval')
    
    def check_rl_action(self, data: Dict) -> Tuple[bool, List[GuardailCheckResult]]:
        """Check RL action"""
        return self._check_guardrails(data, 'rl_agent')
    
    def check_rl_reward(self, data: Dict) -> Tuple[bool, List[GuardailCheckResult]]:
        """Check RL reward and clip if needed"""
        return self._check_guardrails(data, 'rl_agent')
    
    def _check_guardrails(self, data: Dict, scope: str) -> Tuple[bool, List[GuardailCheckResult]]:
        """Check all guardrails in scope"""
        results = []
        
        # Check global guardrails
        for guard in self.guardrails.get('global', []):
            result = guard.check(data)
            results.append(result)
        
        # Check scope-specific guardrails
        for guard in self.guardrails.get(scope, []):
            result = guard.check(data)
            results.append(result)
        
        # Log and store results
        for result in results:
            self.check_history.append(result.to_dict())
            if len(self.check_history) > self.max_history:
                self.check_history.pop(0)
            
            if result.result == GuardResult.FAIL:
                logger.warning(f"Guardrail FAILED: {result.guard_name} - {result.message}")
            elif result.result == GuardResult.WARN:
                logger.warning(f"Guardrail WARNING: {result.guard_name} - {result.message}")
        
        # Determine overall pass/fail
        failed = [r for r in results if r.result == GuardResult.FAIL]
        passed = len(failed) == 0
        
        return passed, results
    
    # ========================================================================
    # AUDIT & MONITORING
    # ========================================================================
    
    def get_check_history(self, limit: int = 100) -> List[Dict]:
        """Get recent check history"""
        return self.check_history[-limit:]
    
    def get_checks_by_guard(self, guard_name: str, limit: int = 100) -> List[Dict]:
        """Get history for specific guard"""
        return [c for c in self.check_history if c['guard_name'] == guard_name][-limit:]
    
    def get_failed_checks(self, limit: int = 100) -> List[Dict]:
        """Get failed checks"""
        return [c for c in self.check_history if c['result'] == 'fail'][-limit:]
    
    def get_guard_stats(self) -> Dict:
        """Get statistics on guardrail checks"""
        total_checks = len(self.check_history)
        passed = sum(1 for c in self.check_history if c['result'] == 'pass')
        failed = sum(1 for c in self.check_history if c['result'] == 'fail')
        warned = sum(1 for c in self.check_history if c['result'] == 'warn')
        
        # Group by scope
        by_guard = {}
        for check in self.check_history:
            guard = check['guard_name']
            if guard not in by_guard:
                by_guard[guard] = {'pass': 0, 'fail': 0, 'warn': 0}
            by_guard[guard][check['result']] += 1
        
        return {
            'total_checks': total_checks,
            'passed': passed,
            'failed': failed,
            'warned': warned,
            'pass_rate': passed / total_checks if total_checks > 0 else 0.0,
            'by_guard': by_guard
        }
    
    def save_to_database(self):
        """Save guardrail checks to database for audit"""
        if not self.db_path:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS guardrail_checks (
                    id INTEGER PRIMARY KEY,
                    guard_name TEXT,
                    guard_type TEXT,
                    result TEXT,
                    severity TEXT,
                    message TEXT,
                    metadata TEXT,
                    timestamp TEXT
                )
            """)
            
            # Insert recent checks
            for check in self.check_history[-100:]:
                cursor.execute("""
                    INSERT INTO guardrail_checks 
                    (guard_name, guard_type, result, severity, message, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    check['guard_name'],
                    check['guard_type'],
                    check['result'],
                    check['severity'],
                    check['message'],
                    json.dumps(check['metadata']),
                    check['timestamp']
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save guardrails to database: {e}")


# ==============================================================================
# FACTORY FOR EASY SERVICE CREATION
# ==============================================================================

def create_guardrails_service(db_path: str = None) -> GuardrailsService:
    """Factory to create and initialize guardrails service"""
    service = GuardrailsService(db_path)
    
    # Register standard guardrails for each scope
    service.register_ingestion_guardrails()
    service.register_retrieval_guardrails()
    service.register_rl_guardrails()
    
    logger.info("GuardrailsService initialized with all guardrails")
    return service
