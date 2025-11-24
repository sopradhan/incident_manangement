import json
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict
from ...database.db.connection import get_connection  # [CHANGE LOG] Use centralized DB connection

logger = logging.getLogger(__name__)


class RLState:
    def __init__(self, features: Dict[str, float]):
        self.features = features
        self.vector = self._to_vector()
    
    def _to_vector(self) -> np.ndarray:
        return np.array([
            self.features.get('avg_quality_score', 0.5),
            self.features.get('low_quality_doc_count', 0) / 100,  # Normalize
            self.features.get('total_query_count', 0) / 1000,     # Normalize
            self.features.get('avg_response_time_ms', 1000) / 5000,  # Normalize
            self.features.get('total_tokens_used', 0) / 100000,   # Normalize
            self.features.get('reindex_attempts', 0) / 10         # Normalize
        ])
    
    def to_key(self) -> str:
        buckets = tuple(int(val * 10) for val in self.vector)  # 10 buckets per dimension
        return f"state_{buckets}"


class RLAction:
    ACTIONS = {
        "REINDEX": {
            "description": "Re-index with new chunk size",
            "parameters": {"new_chunk_size": 512, "new_overlap": 0.1}
        },
        "RESAMPLE": {
            "description": "Resample low-quality chunks",
            "parameters": {"resample_threshold": 0.85, "sample_size": 0.5}
        },
        "REEMBED": {
            "description": "Re-embed with newer model",
            "parameters": {"new_embedding_model": "enhanced"}
        },
        "NO_OP": {
            "description": "Do nothing",
            "parameters": {}
        }
    }
    
    def __init__(self, action_name: str):
        self.name = action_name
        self.spec = self.ACTIONS.get(action_name, {})
    
    @staticmethod
    def get_all_actions() -> List[str]:
        return list(RLAction.ACTIONS.keys())


class RewardCalculator:
    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or {
            "quality": 0.6,
            "cost": 0.3,
            "latency": 0.1
        }
    
    def calculate(self, metrics_before: Dict, metrics_after: Dict) -> float:
        """
        Calculate reward using multi-objective function
        
        R_t+1 = (W_Q × ΔQuality) + (W_C × ΔCost) - (W_L × ΔLatency)
        
        Args:
            metrics_before: Metrics before optimization
            metrics_after: Metrics after optimization
            
        Returns:
            Reward score (typically -1 to +1)
        """
        # Calculate deltas
        delta_quality = metrics_after.get('quality_score', 0) - metrics_before.get('quality_score', 0)
        delta_cost = metrics_before.get('tokens_used', 0) - metrics_after.get('tokens_used', 0)
        delta_latency = metrics_after.get('response_time_ms', 0) - metrics_before.get('response_time_ms', 0)
        
        # Normalize deltas
        delta_quality_norm = np.clip(delta_quality, -1.0, 1.0)
        delta_cost_norm = self._normalize_tokens(delta_cost)
        delta_latency_norm = self._normalize_latency(delta_latency)
        
        # Calculate reward
        reward = (self.weights['quality'] * delta_quality_norm + 
                 self.weights['cost'] * delta_cost_norm -
                 self.weights['latency'] * delta_latency_norm)
        
        logger.info(f"Reward components: ΔQ={delta_quality_norm:.3f}, ΔC={delta_cost_norm:.3f}, ΔL={delta_latency_norm:.3f}")
        logger.info(f"Total Reward: {reward:.3f}")
        
        return reward
    
    def _normalize_tokens(self, token_delta: float) -> float:
        return np.clip(token_delta / 1000, -1.0, 1.0)
    
    def _normalize_latency(self, latency_delta_ms: float) -> float:
        return np.clip(latency_delta_ms / 1000, -1.0, 1.0)


class QLearningPolicy:
    def __init__(self, alpha: float = 0.1, gamma: float = 0.95, epsilon: float = 0.1):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.experiences = []  # For experience replay
    
    def select_action(self, state: RLState) -> str:
        state_key = state.to_key()
        
        # Exploration vs Exploitation
        if np.random.random() < self.epsilon:
            # Explore: random action
            action = np.random.choice(RLAction.get_all_actions())
            logger.debug(f"Exploration: selected random action {action}")
        else:
            # Exploit: best action from Q-table
            q_values = self.q_table[state_key]
            
            if not q_values or all(v == 0 for v in q_values.values()):
                # All actions equally good (or untried), pick randomly
                action = np.random.choice(RLAction.get_all_actions())
            else:
                # Pick action with highest Q-value
                action = max(q_values, key=q_values.get)
            
            logger.debug(f"Exploitation: selected best action {action}")
        
        return action
    
    def update(self, state: RLState, action: str, reward: float, 
              next_state: RLState, done: bool) -> None:
        state_key = state.to_key()
        next_state_key = next_state.to_key()
        
        # Get current Q-value
        current_q = self.q_table[state_key][action]
        
        # Get maximum Q-value for next state
        if done:
            max_next_q = 0
        else:
            max_next_q = max(self.q_table[next_state_key].values()) \
                        if self.q_table[next_state_key] else 0
        
        # Q-Learning update
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state_key][action] = new_q
        
        logger.debug(f"Q-Update: Q({action}) {current_q:.3f} → {new_q:.3f}")
        
        # Store experience for replay
        self.experiences.append({
            'state': state_key,
            'action': action,
            'reward': reward,
            'next_state': next_state_key,
            'done': done
        })
        
        # Keep experience buffer manageable
        if len(self.experiences) > 10000:
            self.experiences.pop(0)
    
    def experience_replay(self, batch_size: int = 32) -> None:
        if len(self.experiences) < batch_size:
            return
        
        # Random sample
        batch = np.random.choice(self.experiences, batch_size, replace=False)
        
        logger.info(f"Experience Replay: learning from {batch_size} experiences")
        
        for exp in batch:
            # Re-update Q-table with this experience
            state_q = self.q_table[exp['state']][exp['action']]
            max_next_q = max(self.q_table[exp['next_state']].values()) \
                        if self.q_table[exp['next_state']] else 0
            
            new_q = state_q + self.alpha * (exp['reward'] + self.gamma * max_next_q - state_q)
            self.q_table[exp['state']][exp['action']] = new_q
    
    def decay_epsilon(self, episodes_completed: int, total_episodes: int) -> None:
        self.epsilon = 0.1 * (1 - episodes_completed / total_episodes)
        logger.debug(f"Epsilon decayed to {self.epsilon:.3f}")


class RLHealingAgent:
    def __init__(self, healing_agent, db_path: str = None):
        self.healing_agent = healing_agent
        self.db_path = db_path or "app.db"
        
        # Initialize RL components
        self.reward_calc = RewardCalculator()
        self.policy = QLearningPolicy(alpha=0.1, gamma=0.95, epsilon=0.1)
        
        logger.info("✓ RL Healing Agent initialized")
    
    def optimize_autonomously(self, document_id: str) -> Dict:
        logger.info(f"=== RL Optimization Start for {document_id} ===")
        
        # Step 1: Get current state
        state = self._get_state()
        logger.info(f"State: {state.features}")
        
        # Step 2: Select action
        action = self.policy.select_action(state)
        logger.info(f"Action selected: {action}")
        
        # Step 3: Execute action and measure metrics
        metrics_before = self._measure_metrics(document_id)
        
        if action == "REINDEX":
            result = self.healing_agent.optimize_document(document_id, strategy="reindex")
        elif action == "RESAMPLE":
            result = self.healing_agent.optimize_document(document_id, strategy="resample")
        elif action == "REEMBED":
            result = self.healing_agent.optimize_document(document_id, strategy="reembed")
        else:  # NO_OP
            result = {"success": True, "strategy": "NO_OP"}
        
        metrics_after = self._measure_metrics(document_id)
        
        # Step 4: Calculate reward
        reward = self.reward_calc.calculate(metrics_before, metrics_after)
        
        # Step 5: Get next state and update policy
        next_state = self._get_state()
        done = (action == "NO_OP")
        self.policy.update(state, action, reward, next_state, done)
        
        # Step 6: Store in agent_memory for future reference
        self._store_rl_experience(state, action, reward, metrics_before, metrics_after, result)
        
        logger.info(f"=== RL Optimization Complete ===")
        
        return {
            "success": True,
            "document_id": document_id,
            "action": action,
            "reward": reward,
            "metrics_before": metrics_before,
            "metrics_after": metrics_after,
            "optimization_result": result
        }
    
    def _get_state(self) -> RLState:
        try:
            health = self.healing_agent.analyze_health()
            
            features = {
                'avg_quality_score': health.get('avg_quality', 0.5),
                'low_quality_doc_count': health.get('poor_quality_documents', 0),
                'total_query_count': health.get('total_chunks', 0),  # Proxy for queries
                'avg_response_time_ms': 3000,  # TODO: Get from metrics
                'total_tokens_used': 0,  # TODO: Get from token tracking
                'reindex_attempts': 0  # TODO: Get from history
            }
            
            return RLState(features)
            
        except Exception as e:
            logger.error(f"Failed to get state: {e}")
            return RLState({})
    
    def _measure_metrics(self, document_id: str) -> Dict:
        try:
            # [CHANGE LOG] Using centralized get_connection() utility
            conn = get_connection()
            
            # Query embedding_metadata for quality
            quality_query = """
                SELECT AVG(quality_score) as avg_quality
                FROM embedding_metadata
                WHERE document_id = ?
            """
            quality_result = conn.execute(quality_query, (document_id,)).fetchone()
            
            # Query token usage
            tokens_query = """
                SELECT SUM(total_tokens) as total_tokens
                FROM token_usage
                WHERE timestamp > datetime('now', '-1 hour')
            """
            tokens_result = conn.execute(tokens_query).fetchone()
            
            conn.close()
            
            return {
                'quality_score': quality_result['avg_quality'] or 0.5 if quality_result else 0.5,
                'tokens_used': tokens_result['total_tokens'] or 0 if tokens_result else 0,
                'response_time_ms': 3000  # TODO: Get actual latency
            }
            
        except Exception as e:
            logger.error(f"Failed to measure metrics: {e}")
            return {
                'quality_score': 0.5,
                'tokens_used': 0,
                'response_time_ms': 3000
            }
    
    def _store_rl_experience(self, state: RLState, action: str, reward: float,
        try:
            from ...database.models import AgentMemoryModel
            
            # [CHANGE LOG] Using centralized get_connection() utility
            conn = get_connection()
            mem_model = AgentMemoryModel(conn)
            
            experience = {
                "state": state.features,
                "action": action,
                "reward": reward,
                "metrics_before": metrics_before,
                "metrics_after": metrics_after,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
            mem_model.record_memory(
                agent_name="RLHealingAgent",
                memory_key=f"rl_experience_{action}_{datetime.now().timestamp()}",
                memory_value=json.dumps(experience),
                memory_type="rl_experience"
            )
            
            conn.close()
            
        except Exception as e:
            logger.warning(f"Failed to store RL experience: {e}")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def example_usage():
    """Example usage of RL Healing Agent"""
    
    # Assume existing HealingAgent
    from healing_agent import HealingAgent
    
    # Wrap with RL
    healing_agent = HealingAgent({})  # Mock initialization
    rl_agent = RLHealingAgent(healing_agent)
    
    # Run optimization
    result = rl_agent.optimize_autonomously("doc_123")
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("RL Healing Agent Module - Ready for integration")
