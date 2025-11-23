"""
RL Models - Q-Learning state management, episode tracking, and optimization history
"""
from typing import List, Dict, Any, Optional
import json
from .base_model import BaseModel


class RLQTableModel(BaseModel):
    """Model for rl_q_table - Stores Q-Learning state-action values"""
    
    table = 'rl_q_table'
    fields = ['q_id', 'state_key', 'action', 'q_value', 'visits', 'last_updated']
    
    def get_or_create_q_value(self, state_key: str, action: str) -> float:
        """
        Get Q-value for state-action pair, create if not exists
        
        Args:
            state_key: State identifier
            action: Action identifier
            
        Returns:
            Q-value (0.0 if new)
        """
        rows = self.raw_execute("""
            SELECT q_value FROM rl_q_table
            WHERE state_key = ? AND action = ?
        """, (state_key, action))
        
        if rows:
            return rows[0]['q_value']
        else:
            self.insert({
                'state_key': state_key,
                'action': action,
                'q_value': 0.0,
                'visits': 0
            })
            return 0.0
    
    def update_q_value(self, state_key: str, action: str, q_value: float) -> None:
        """
        Update Q-value for state-action pair
        
        Args:
            state_key: State identifier
            action: Action identifier
            q_value: New Q-value
        """
        self.raw_execute("""
            UPDATE rl_q_table
            SET q_value = ?, visits = visits + 1, last_updated = datetime('now')
            WHERE state_key = ? AND action = ?
        """, (q_value, state_key, action))
    
    def get_best_action(self, state_key: str) -> Optional[Dict[str, Any]]:
        """
        Get action with highest Q-value for a state
        
        Args:
            state_key: State identifier
            
        Returns:
            Best action record or None
        """
        rows = self.raw_execute("""
            SELECT * FROM rl_q_table
            WHERE state_key = ?
            ORDER BY q_value DESC
            LIMIT 1
        """, (state_key,))
        
        return rows[0] if rows else None
    
    def get_actions_for_state(self, state_key: str) -> List[Dict[str, Any]]:
        """
        Get all actions and Q-values for a state
        
        Args:
            state_key: State identifier
            
        Returns:
            List of action records for state
        """
        return self.raw_execute("""
            SELECT * FROM rl_q_table
            WHERE state_key = ?
            ORDER BY q_value DESC
        """, (state_key,))
    
    def get_visit_count(self, state_key: str, action: str) -> int:
        """
        Get visit count for state-action pair
        
        Args:
            state_key: State identifier
            action: Action identifier
            
        Returns:
            Number of times this pair was visited
        """
        rows = self.raw_execute("""
            SELECT visits FROM rl_q_table
            WHERE state_key = ? AND action = ?
        """, (state_key, action))
        
        return rows[0]['visits'] if rows else 0
    
    def reset_q_table(self) -> None:
        """
        Reset all Q-values to 0.0 (restart learning)
        """
        self.conn.execute("DELETE FROM rl_q_table")
        self.conn.commit()


class RLEpisodeModel(BaseModel):
    """Model for rl_episodes - Tracks RL training episodes"""
    
    table = 'rl_episodes'
    fields = ['episode_id', 'document_id', 'episode_number', 'initial_state', 
              'final_state', 'total_reward', 'total_steps', 'status', 
              'started_at', 'completed_at', 'duration_ms']
    
    def create_episode(self, document_id: str, episode_number: int,
                      initial_state: str) -> int:
        """
        Create new RL episode
        
        Args:
            document_id: Document being optimized
            episode_number: Episode sequence number
            initial_state: Initial state representation
            
        Returns:
            Episode ID
        """
        return self.insert({
            'document_id': document_id,
            'episode_number': episode_number,
            'initial_state': initial_state,
            'status': 'running'
        })
    
    def complete_episode(self, episode_id: int, final_state: str,
                        total_reward: float, total_steps: int,
                        duration_ms: int) -> None:
        """
        Mark episode as completed
        
        Args:
            episode_id: Episode identifier
            final_state: Final state representation
            total_reward: Total reward accumulated
            total_steps: Total steps taken
            duration_ms: Duration in milliseconds
        """
        self.raw_execute("""
            UPDATE rl_episodes
            SET final_state = ?, total_reward = ?, total_steps = ?,
                duration_ms = ?, status = 'completed', completed_at = datetime('now')
            WHERE episode_id = ?
        """, (final_state, total_reward, total_steps, duration_ms, episode_id))
    
    def get_episodes_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all episodes for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of episode records
        """
        return self.raw_execute("""
            SELECT * FROM rl_episodes
            WHERE document_id = ?
            ORDER BY episode_number DESC
        """, (document_id,))
    
    def get_episode_stats(self, document_id: str) -> Dict[str, Any]:
        """
        Get statistics for episodes of a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            Dictionary with episode statistics
        """
        rows = self.raw_execute("""
            SELECT
                COUNT(*) as total_episodes,
                AVG(total_reward) as avg_reward,
                MAX(total_reward) as max_reward,
                MIN(total_reward) as min_reward,
                AVG(total_steps) as avg_steps,
                AVG(duration_ms) as avg_duration_ms
            FROM rl_episodes
            WHERE document_id = ?
        """, (document_id,))
        
        if rows:
            return dict(rows[0])
        return {}
    
    def get_recent_episodes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent episodes across all documents
        
        Args:
            limit: Maximum number of episodes
            
        Returns:
            List of recent episode records
        """
        return self.raw_execute("""
            SELECT * FROM rl_episodes
            ORDER BY started_at DESC
            LIMIT ?
        """, (limit,))
    
    def get_best_episode(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get best episode (highest reward) for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            Best episode record or None
        """
        rows = self.raw_execute("""
            SELECT * FROM rl_episodes
            WHERE document_id = ?
            ORDER BY total_reward DESC
            LIMIT 1
        """, (document_id,))
        
        return rows[0] if rows else None


class RLExperienceBufferModel(BaseModel):
    """Model for rl_experience_buffer - Stores experience replay data"""
    
    table = 'rl_experience_buffer'
    fields = ['experience_id', 'episode_id', 'step_number', 'state_key', 
              'action', 'reward', 'next_state_key', 'done', 'timestamp']
    
    def store_experience(self, episode_id: int, step_number: int,
                        state_key: str, action: str, reward: float,
                        next_state_key: str, done: bool = False) -> int:
        """
        Store experience tuple for replay buffer
        
        Args:
            episode_id: Associated episode
            step_number: Step within episode
            state_key: Current state
            action: Action taken
            reward: Reward received
            next_state_key: Resulting state
            done: Whether episode ended
            
        Returns:
            Experience ID
        """
        return self.insert({
            'episode_id': episode_id,
            'step_number': step_number,
            'state_key': state_key,
            'action': action,
            'reward': reward,
            'next_state_key': next_state_key,
            'done': 1 if done else 0
        })
    
    def get_episode_experiences(self, episode_id: int) -> List[Dict[str, Any]]:
        """
        Get all experiences from an episode
        
        Args:
            episode_id: Episode identifier
            
        Returns:
            List of experience records
        """
        return self.raw_execute("""
            SELECT * FROM rl_experience_buffer
            WHERE episode_id = ?
            ORDER BY step_number
        """, (episode_id,))
    
    def get_random_batch(self, batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        Get random batch of experiences for training
        
        Args:
            batch_size: Batch size
            
        Returns:
            List of random experience records
        """
        return self.raw_execute(f"""
            SELECT * FROM rl_experience_buffer
            ORDER BY RANDOM()
            LIMIT ?
        """, (batch_size,))
    
    def get_buffer_size(self) -> int:
        """
        Get total number of stored experiences
        
        Returns:
            Buffer size
        """
        rows = self.raw_execute("SELECT COUNT(*) as count FROM rl_experience_buffer")
        return rows[0]['count'] if rows else 0
    
    def clear_old_experiences(self, keep_episodes: int = 100) -> None:
        """
        Clear old experiences keeping only recent episodes
        
        Args:
            keep_episodes: Number of recent episodes to keep
        """
        self.conn.execute("""
            DELETE FROM rl_experience_buffer
            WHERE episode_id NOT IN (
                SELECT episode_id FROM rl_episodes
                ORDER BY episode_id DESC
                LIMIT ?
            )
        """, (keep_episodes,))
        self.conn.commit()


class RLOptimizationModel(BaseModel):
    """Model for rl_optimizations - Audit trail of RL optimizations"""
    
    table = 'rl_optimizations'
    fields = ['optimization_id', 'document_id', 'episode_id', 'action_taken',
              'metrics_before', 'metrics_after', 'quality_delta', 'cost_delta',
              'latency_delta', 'reward', 'successful', 'timestamp']
    
    def record_optimization(self, document_id: str, episode_id: int,
                          action_taken: str, metrics_before: Dict[str, Any],
                          metrics_after: Dict[str, Any], reward: float,
                          successful: bool = True) -> int:
        """
        Record an RL optimization action and its results
        
        Args:
            document_id: Document being optimized
            episode_id: Associated episode
            action_taken: Action applied
            metrics_before: Metrics before action
            metrics_after: Metrics after action
            reward: Reward for this action
            successful: Whether action was successful
            
        Returns:
            Optimization ID
        """
        import json
        
        quality_delta = metrics_after.get('quality', 0) - metrics_before.get('quality', 0)
        cost_delta = metrics_after.get('cost', 0) - metrics_before.get('cost', 0)
        latency_delta = metrics_after.get('latency', 0) - metrics_before.get('latency', 0)
        
        return self.insert({
            'document_id': document_id,
            'episode_id': episode_id,
            'action_taken': action_taken,
            'metrics_before': json.dumps(metrics_before),
            'metrics_after': json.dumps(metrics_after),
            'quality_delta': quality_delta,
            'cost_delta': cost_delta,
            'latency_delta': latency_delta,
            'reward': reward,
            'successful': 1 if successful else 0
        })
    
    def get_optimizations_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get all optimizations for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of optimization records
        """
        return self.raw_execute("""
            SELECT * FROM rl_optimizations
            WHERE document_id = ?
            ORDER BY timestamp DESC
        """, (document_id,))
    
    def get_successful_optimizations(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Get successful optimizations for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of successful optimization records
        """
        return self.raw_execute("""
            SELECT * FROM rl_optimizations
            WHERE document_id = ? AND successful = 1
            ORDER BY timestamp DESC
        """, (document_id,))
    
    def get_action_effectiveness(self, action_taken: str) -> Dict[str, Any]:
        """
        Get effectiveness metrics for an action across all documents
        
        Args:
            action_taken: Action to analyze
            
        Returns:
            Dictionary with effectiveness metrics
        """
        rows = self.raw_execute("""
            SELECT
                COUNT(*) as total_uses,
                SUM(CASE WHEN successful = 1 THEN 1 ELSE 0 END) as successful_uses,
                AVG(reward) as avg_reward,
                AVG(quality_delta) as avg_quality_improvement,
                AVG(cost_delta) as avg_cost_delta,
                AVG(latency_delta) as avg_latency_delta
            FROM rl_optimizations
            WHERE action_taken = ?
        """, (action_taken,))
        
        if rows:
            return dict(rows[0])
        return {}
    
    def get_cumulative_improvements(self, document_id: str) -> Dict[str, float]:
        """
        Get cumulative improvements for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            Dictionary with cumulative metrics
        """
        rows = self.raw_execute("""
            SELECT
                SUM(quality_delta) as total_quality_improvement,
                SUM(cost_delta) as total_cost_change,
                SUM(latency_delta) as total_latency_improvement,
                SUM(reward) as total_reward
            FROM rl_optimizations
            WHERE document_id = ?
        """, (document_id,))
        
        if rows and rows[0]:
            return dict(rows[0])
        return {}


class RLPolicyMetricsModel(BaseModel):
    """Model for rl_policy_metrics - Tracks RL policy performance over time"""
    
    table = 'rl_policy_metrics'
    fields = ['metric_id', 'episode_id', 'avg_reward', 'max_reward', 'min_reward',
              'epsilon', 'alpha', 'gamma', 'total_episodes', 'exploration_rate',
              'exploitation_rate', 'timestamp']
    
    def record_metrics(self, episode_id: int, avg_reward: float,
                      max_reward: float, min_reward: float,
                      epsilon: float, alpha: float, gamma: float,
                      total_episodes: int) -> int:
        """
        Record policy metrics at episode checkpoint
        
        Args:
            episode_id: Associated episode
            avg_reward: Average reward so far
            max_reward: Maximum reward achieved
            min_reward: Minimum reward achieved
            epsilon: Exploration parameter
            alpha: Learning rate
            gamma: Discount factor
            total_episodes: Total episodes completed
            
        Returns:
            Metric ID
        """
        exploration_rate = epsilon
        exploitation_rate = 1.0 - epsilon
        
        return self.insert({
            'episode_id': episode_id,
            'avg_reward': avg_reward,
            'max_reward': max_reward,
            'min_reward': min_reward,
            'epsilon': epsilon,
            'alpha': alpha,
            'gamma': gamma,
            'total_episodes': total_episodes,
            'exploration_rate': exploration_rate,
            'exploitation_rate': exploitation_rate
        })
    
    def get_episode_metrics(self, episode_id: int) -> Optional[Dict[str, Any]]:
        """
        Get metrics for a specific episode
        
        Args:
            episode_id: Episode identifier
            
        Returns:
            Metrics record or None
        """
        rows = self.raw_execute("""
            SELECT * FROM rl_policy_metrics
            WHERE episode_id = ?
        """, (episode_id,))
        
        return rows[0] if rows else None
    
    def get_learning_trend(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent metrics showing learning trend
        
        Args:
            limit: Number of recent metrics
            
        Returns:
            List of metric records
        """
        return self.raw_execute("""
            SELECT * FROM rl_policy_metrics
            ORDER BY episode_id DESC
            LIMIT ?
        """, (limit,))
    
    def get_hyperparameters_progression(self) -> List[Dict[str, Any]]:
        """
        Get how hyperparameters changed over training
        
        Returns:
            List of metrics showing parameter progression
        """
        return self.raw_execute("""
            SELECT episode_id, epsilon, alpha, gamma, exploration_rate
            FROM rl_policy_metrics
            ORDER BY episode_id
        """)


class RLActionStatsModel(BaseModel):
    """Model for rl_action_stats - Aggregated action performance statistics"""
    
    table = 'rl_action_stats'
    fields = ['action_id', 'action_name', 'total_taken', 'total_reward',
              'avg_reward', 'success_count', 'success_rate',
              'avg_quality_improvement', 'avg_cost_savings', 'last_used', 'updated_at']
    
    def get_or_create_action(self, action_name: str) -> Dict[str, Any]:
        """
        Get action stats or create new entry
        
        Args:
            action_name: Action identifier
            
        Returns:
            Action stats record
        """
        rows = self.raw_execute("""
            SELECT * FROM rl_action_stats
            WHERE action_name = ?
        """, (action_name,))
        
        if rows:
            return rows[0]
        else:
            self.insert({
                'action_name': action_name,
                'total_taken': 0,
                'total_reward': 0.0,
                'avg_reward': 0.0,
                'success_count': 0,
                'success_rate': 0.0,
                'avg_quality_improvement': 0.0,
                'avg_cost_savings': 0.0
            })
            return self.raw_execute("""
                SELECT * FROM rl_action_stats
                WHERE action_name = ?
            """, (action_name,))[0]
    
    def update_action_stats(self, action_name: str, reward: float,
                           successful: bool, quality_improvement: float = 0.0,
                           cost_savings: float = 0.0) -> None:
        """
        Update aggregated stats for an action
        
        Args:
            action_name: Action identifier
            reward: Reward received
            successful: Whether action was successful
            quality_improvement: Quality metric improvement
            cost_savings: Cost savings achieved
        """
        self.get_or_create_action(action_name)
        
        self.raw_execute("""
            UPDATE rl_action_stats
            SET total_taken = total_taken + 1,
                total_reward = total_reward + ?,
                success_count = success_count + ?,
                avg_reward = (total_reward + ?) / (total_taken + 1),
                success_rate = CAST(success_count + ? AS FLOAT) / (total_taken + 1),
                avg_quality_improvement = (avg_quality_improvement * total_taken + ?) / (total_taken + 1),
                avg_cost_savings = (avg_cost_savings * total_taken + ?) / (total_taken + 1),
                last_used = datetime('now'),
                updated_at = datetime('now')
            WHERE action_name = ?
        """, (reward, 1 if successful else 0, reward,
              1 if successful else 0, quality_improvement, cost_savings, action_name))
    
    def get_top_actions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing actions by average reward
        
        Args:
            limit: Number of top actions
            
        Returns:
            List of top action records
        """
        return self.raw_execute("""
            SELECT * FROM rl_action_stats
            ORDER BY avg_reward DESC
            LIMIT ?
        """, (limit,))
    
    def get_most_used_actions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most frequently used actions
        
        Args:
            limit: Number of actions
            
        Returns:
            List of frequently used action records
        """
        return self.raw_execute("""
            SELECT * FROM rl_action_stats
            ORDER BY total_taken DESC
            LIMIT ?
        """, (limit,))
    
    def get_action_ranking(self) -> List[Dict[str, Any]]:
        """
        Get all actions ranked by effectiveness (success_rate * avg_reward)
        
        Returns:
            List of action records ranked
        """
        return self.raw_execute("""
            SELECT *,
                   (success_rate * avg_reward) as effectiveness_score
            FROM rl_action_stats
            ORDER BY effectiveness_score DESC
        """)
    
    def get_action_stats(self, action_name: str) -> Optional[Dict[str, Any]]:
        """
        Get full stats for a specific action
        
        Args:
            action_name: Action identifier
            
        Returns:
            Action stats or None
        """
        rows = self.raw_execute("""
            SELECT * FROM rl_action_stats
            WHERE action_name = ?
        """, (action_name,))
        
        return rows[0] if rows else None
