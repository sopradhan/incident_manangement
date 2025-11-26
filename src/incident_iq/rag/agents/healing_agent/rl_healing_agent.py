"""
Reinforcement Learning-based Healing Agent
Purpose: Intelligently optimize RAG system using RL to maximize quality while minimizing cost
Date: 2025-11-26

RL Architecture:
- State: Document quality, query accuracy, token cost
- Actions: SKIP, OPTIMIZE, REINDEX, RE_EMBED
- Reward: (Quality_Improvement - Cost) * Confidence
- Learning: Track effectiveness and improve decision-making over time
"""
import json
import sqlite3
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import os


@dataclass
class RLState:
    """Current system state for RL agent decision-making"""
    quality_score: float
    query_accuracy: float
    chunk_count: int
    avg_token_cost: float
    reindex_count: int
    last_healing_delta: float
    query_frequency: int
    user_feedback: float


@dataclass
class RLAction:
    """Action to be taken by the agent"""
    action: str  # SKIP, OPTIMIZE, REINDEX, RE_EMBED
    params: Dict[str, Any]
    estimated_improvement: float
    estimated_cost: float
    confidence: float


class RLHealingAgent:
    """
    Reinforcement Learning-based healing agent for RAG optimization
    
    Learning Strategy:
    - Epsilon-greedy: Explore new strategies vs exploit known good ones
    - Q-learning: Update value estimates based on observed rewards
    - Contextual bandits: Consider document characteristics for decisions
    """
    
    def __init__(self, db_path: str, initial_epsilon: float = 0.3):
        """
        Initialize RL Healing Agent
        
        Args:
            db_path: Path to SQLite database
            initial_epsilon: Initial exploration rate (0-1)
        """
        self.db_path = db_path
        self.epsilon = initial_epsilon  # Exploration rate
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        
        # Q-values: state_action_pair -> value (learning memory)
        self.q_values: Dict[str, float] = {}
        
        # Action statistics for learning
        self.action_history: Dict[str, Dict[str, float]] = {
            'SKIP': {'count': 0, 'total_reward': 0, 'avg_reward': 0},
            'OPTIMIZE': {'count': 0, 'total_reward': 0, 'avg_reward': 0},
            'REINDEX': {'count': 0, 'total_reward': 0, 'avg_reward': 0},
            'RE_EMBED': {'count': 0, 'total_reward': 0, 'avg_reward': 0},
        }
        
        self._init_db()
    
    def _init_db(self):
        """Ensure database tables exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verify tables exist
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='document_metadata'"
            )
            if not cursor.fetchone():
                raise RuntimeError("Database schema not initialized. Run migration first!")
            
            conn.close()
        except Exception as e:
            raise RuntimeError(f"Database initialization failed: {e}")
    
    def decide_action(self, state: RLState, doc_id: str) -> RLAction:
        """
        Use RL to decide which action to take
        
        Args:
            state: Current system state
            doc_id: Document being evaluated
        
        Returns:
            RLAction with chosen action and parameters
        """
        # Epsilon-greedy strategy
        if np.random.random() < self.epsilon:
            # Explore: randomly choose action
            action = np.random.choice(['SKIP', 'OPTIMIZE', 'REINDEX', 'RE_EMBED'])
        else:
            # Exploit: choose best known action
            action = self._get_best_action(state, doc_id)
        
        # Generate action details
        rl_action = self._generate_action_details(action, state, doc_id)
        
        return rl_action
    
    def _get_best_action(self, state: RLState, doc_id: str) -> str:
        """
        Choose action with highest expected value based on learning history
        """
        # Score each action
        action_scores = {}
        
        for action in ['SKIP', 'OPTIMIZE', 'REINDEX', 'RE_EMBED']:
            stats = self.action_history[action]
            
            if stats['count'] == 0:
                # No data yet, neutral score
                action_scores[action] = 0.5
            else:
                # Q-value approach: average reward adjusted for action cost
                base_reward = stats['avg_reward']
                
                # Adjust based on state
                if action == 'SKIP':
                    # Only good if quality is already high
                    adjustment = 1.0 if state.quality_score > 0.75 else -1.0
                
                elif action == 'OPTIMIZE':
                    # Good if quality is poor and cost is reasonable
                    if state.quality_score < 0.6 and state.avg_token_cost < 2000:
                        adjustment = 1.5
                    elif state.quality_score < 0.6:
                        adjustment = 0.8
                    else:
                        adjustment = -0.5
                
                elif action == 'REINDEX':
                    # Good if re-indexing hasn't been done much
                    if state.reindex_count < 3:
                        adjustment = 1.0 if state.quality_score < 0.65 else -0.5
                    else:
                        adjustment = -1.0
                
                elif action == 'RE_EMBED':
                    # Good for fresh perspectives, but costly
                    if state.quality_score < 0.5:
                        adjustment = 2.0
                    elif state.avg_token_cost < 1000:
                        adjustment = 0.5
                    else:
                        adjustment = -1.5
                
                action_scores[action] = base_reward + adjustment
        
        # Choose action with highest score
        best_action = max(action_scores, key=action_scores.get)
        return best_action
    
    def _generate_action_details(self, action: str, state: RLState, doc_id: str) -> RLAction:
        """
        Generate detailed parameters and estimates for the chosen action
        """
        if action == 'SKIP':
            return RLAction(
                action='SKIP',
                params={},
                estimated_improvement=0,
                estimated_cost=0,
                confidence=0.95 if state.quality_score > 0.75 else 0.5
            )
        
        elif action == 'OPTIMIZE':
            # Suggest chunk size optimization
            current_size = 512
            if state.quality_score < 0.6:
                suggested_size = 256  # Smaller chunks for low quality
                improvement = 0.15
                confidence = 0.82
            else:
                suggested_size = 384  # Balance
                improvement = 0.08
                confidence = 0.70
            
            return RLAction(
                action='OPTIMIZE',
                params={
                    'new_chunk_size': suggested_size,
                    'new_overlap': int(suggested_size * 0.1),
                    'strategy': 'recursive_splitter'
                },
                estimated_improvement=improvement,
                estimated_cost=500,  # tokens
                confidence=confidence
            )
        
        elif action == 'REINDEX':
            # Re-index with same parameters
            return RLAction(
                action='REINDEX',
                params={
                    'clear_cache': True,
                    'recompute_embeddings': True
                },
                estimated_improvement=0.12 if state.reindex_count < 2 else 0.05,
                estimated_cost=300,
                confidence=0.75 if state.reindex_count < 2 else 0.55
            )
        
        elif action == 'RE_EMBED':
            # Use different embedding model
            return RLAction(
                action='RE_EMBED',
                params={
                    'new_model': 'mistral',  # Switch from ollama default
                    'preserve_old_embeddings': True
                },
                estimated_improvement=0.25,
                estimated_cost=800,
                confidence=0.68
            )
    
    def observe_reward(self, action: RLAction, actual_reward: float, session_id: str = None):
        """
        Update RL values based on observed reward
        
        Args:
            action: Action that was taken
            actual_reward: Observed reward (quality improvement - cost)
            session_id: Session identifier for tracking
        """
        # Update Q-values
        action_name = action.action
        stats = self.action_history[action_name]
        
        # Update statistics
        stats['count'] += 1
        stats['total_reward'] += actual_reward
        stats['avg_reward'] = stats['total_reward'] / stats['count']
        
        # Decay epsilon (explore less over time)
        self.epsilon = max(0.05, self.epsilon * 0.995)
        
        # Log to database
        self._log_rl_decision(action, actual_reward, session_id)
    
    def _log_rl_decision(self, action: RLAction, reward: float, session_id: str):
        """Log RL decision to database for analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            state_json = json.dumps({
                'action': action.action,
                'params': action.params,
                'estimated_improvement': action.estimated_improvement,
                'confidence': action.confidence
            })
            
            context_json = json.dumps({
                'reward_achieved': reward,
                'q_values': self.action_history,
                'epsilon': self.epsilon
            })
            
            cursor.execute("""
                INSERT INTO rag_history_and_optimization
                (event_type, timestamp, action_taken, reward_signal, context_json, agent_id, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                'HEAL',
                datetime.now().isoformat(),
                action.action,
                reward,
                context_json,
                'rl_healing_agent',
                session_id
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Warning: Failed to log RL decision: {e}")
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """
        Get current learning statistics
        """
        total_decisions = sum(stats['count'] for stats in self.action_history.values())
        
        return {
            'total_decisions': total_decisions,
            'epsilon': self.epsilon,
            'actions': {
                action: {
                    'count': stats['count'],
                    'percentage': (stats['count'] / total_decisions * 100) if total_decisions > 0 else 0,
                    'avg_reward': round(stats['avg_reward'], 4),
                    'total_reward': round(stats['total_reward'], 2)
                }
                for action, stats in self.action_history.items()
            },
            'best_action': max(
                self.action_history.items(),
                key=lambda x: x[1]['avg_reward'] if x[1]['count'] > 0 else 0
            )[0] if any(s['count'] > 0 for s in self.action_history.values()) else 'N/A'
        }
    
    def recommend_healing(self, doc_id: str, current_quality: float) -> Dict[str, Any]:
        """
        Get healing recommendation for a specific document
        
        Args:
            doc_id: Document ID
            current_quality: Current quality score (0-1)
        
        Returns:
            Recommendation with action and reasoning
        """
        # Create state
        state = self._build_state_from_db(doc_id, current_quality)
        
        # Get action
        action = self.decide_action(state, doc_id)
        
        # Return recommendation
        return {
            'doc_id': doc_id,
            'current_quality': current_quality,
            'recommended_action': action.action,
            'parameters': action.params,
            'expected_improvement': action.estimated_improvement,
            'estimated_cost': action.estimated_cost,
            'confidence': action.confidence,
            'reasoning': self._generate_reasoning(action, state),
            'learning_stats': self.get_learning_stats()
        }
    
    def _build_state_from_db(self, doc_id: str, current_quality: float) -> RLState:
        """Build state from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get document info
            cursor.execute("""
                SELECT chunk_size_char FROM document_metadata WHERE doc_id = ?
            """, (doc_id,))
            doc_info = cursor.fetchone()
            
            # Get chunk stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as chunk_count,
                    AVG(reindex_count) as avg_reindex
                FROM chunk_embedding_data
                WHERE doc_id = ?
            """, (doc_id,))
            chunk_stats = cursor.fetchone()
            
            # Get query performance
            cursor.execute("""
                SELECT 
                    COUNT(*) as query_count,
                    AVG(CAST(json_extract(metrics_json, '$.avg_accuracy') AS FLOAT)) as avg_accuracy,
                    AVG(CAST(json_extract(metrics_json, '$.cost_tokens') AS FLOAT)) as avg_cost,
                    AVG(CAST(json_extract(metrics_json, '$.user_feedback') AS FLOAT)) as avg_feedback
                FROM rag_history_and_optimization
                WHERE target_doc_id = ? AND event_type = 'QUERY'
            """, (doc_id,))
            query_stats = cursor.fetchone()
            
            conn.close()
            
            return RLState(
                quality_score=current_quality,
                query_accuracy=query_stats[1] or 0.7 if query_stats else 0.7,
                chunk_count=chunk_stats[0] if chunk_stats else 0,
                avg_token_cost=query_stats[2] or 1000 if query_stats else 1000,
                reindex_count=int(chunk_stats[1] or 0) if chunk_stats else 0,
                last_healing_delta=0.1,  # Default
                query_frequency=query_stats[0] if query_stats else 0,
                user_feedback=query_stats[3] or 0.7 if query_stats else 0.7
            )
        except Exception as e:
            # Return default state on error
            return RLState(
                quality_score=current_quality,
                query_accuracy=0.7,
                chunk_count=0,
                avg_token_cost=1000,
                reindex_count=0,
                last_healing_delta=0.1,
                query_frequency=0,
                user_feedback=0.7
            )
    
    def _generate_reasoning(self, action: RLAction, state: RLState) -> str:
        """Generate human-readable reasoning for the action"""
        reasons = {
            'SKIP': "System quality is good. No action needed.",
            'OPTIMIZE': "Quality is below target. Optimizing chunk parameters for better retrieval.",
            'REINDEX': "Regenerating embeddings to refresh semantic understanding.",
            'RE_EMBED': "Switching embedding model for better quality understanding."
        }
        
        return reasons.get(action.action, "Action selected based on learning history.")


def example_usage():
    """Example of how to use the RL Healing Agent"""
    
    # Initialize agent
    db_path = "./chroma_db/rag.db"
    agent = RLHealingAgent(db_path)
    
    # Get recommendation
    recommendation = agent.recommend_healing(
        doc_id="doc_001",
        current_quality=0.55
    )
    
    print("\n📊 RL Healing Agent Recommendation:")
    print(json.dumps(recommendation, indent=2))
    
    # Simulate action and observe reward
    action = RLAction(
        action=recommendation['recommended_action'],
        params=recommendation['parameters'],
        estimated_improvement=recommendation['expected_improvement'],
        estimated_cost=recommendation['estimated_cost'],
        confidence=recommendation['confidence']
    )
    
    # Observe actual reward (in real system, this comes from actual healing results)
    actual_reward = 0.12  # Achieved 12% improvement
    agent.observe_reward(action, actual_reward, session_id="session_123")
    
    # Check learning progress
    stats = agent.get_learning_stats()
    print("\n📈 RL Agent Learning Stats:")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    example_usage()
