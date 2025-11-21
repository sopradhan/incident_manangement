"""
Tracking Models - Tracks healing operations and query heatmaps
"""
from typing import List, Dict, Any, Optional
import json
from .base_model import BaseModel


class HealingOperationModel(BaseModel):
    """Model for healing_operations table"""
    
    table = 'healing_operations'
    fields = ['healing_id', 'strategy', 'target_docs', 'reason', 'actions_taken',
              'before_metrics', 'after_metrics', 'improvement_delta', 'timestamp']
    
    def log_healing_operation(self, strategy: str, target_docs: List[str],
                             reason: str, actions_taken: Dict,
                             before_metrics: Dict, after_metrics: Dict,
                             improvement_delta: float) -> int:
        """
        Log a healing operation
        
        Args:
            strategy: Healing strategy used
            target_docs: Documents targeted for healing
            reason: Reason for healing
            actions_taken: Actions taken during healing
            before_metrics: Metrics before healing
            after_metrics: Metrics after healing
            improvement_delta: Improvement achieved
            
        Returns:
            Last inserted row ID
        """
        return self.insert({
            'strategy': strategy,
            'target_docs': json.dumps(target_docs),
            'reason': reason,
            'actions_taken': json.dumps(actions_taken),
            'before_metrics': json.dumps(before_metrics),
            'after_metrics': json.dumps(after_metrics),
            'improvement_delta': improvement_delta
        })
    
    def get_healing_operations_by_strategy(self, strategy: str) -> List[Dict[str, Any]]:
        """
        Get healing operations by strategy
        
        Args:
            strategy: Strategy filter
            
        Returns:
            List of healing operations
        """
        return self.raw_execute("""
            SELECT * FROM healing_operations
            WHERE strategy = ?
            ORDER BY timestamp DESC
        """, (strategy,))
    
    def get_most_effective_strategies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most effective healing strategies
        
        Args:
            limit: Number to return
            
        Returns:
            List of strategies ordered by improvement
        """
        return self.raw_execute("""
            SELECT
                strategy,
                COUNT(*) as usage_count,
                AVG(improvement_delta) as avg_improvement,
                MAX(improvement_delta) as max_improvement,
                MIN(improvement_delta) as min_improvement
            FROM healing_operations
            GROUP BY strategy
            ORDER BY avg_improvement DESC
            LIMIT ?
        """, (limit,))
    
    def get_total_improvement(self, strategy: Optional[str] = None) -> float:
        """
        Get total improvement from healing operations
        
        Args:
            strategy: Optional strategy filter
            
        Returns:
            Total improvement delta
        """
        if strategy:
            rows = self.raw_execute(
                "SELECT SUM(improvement_delta) as total FROM healing_operations WHERE strategy = ?",
                (strategy,)
            )
        else:
            rows = self.raw_execute("SELECT SUM(improvement_delta) as total FROM healing_operations")
        
        return rows[0]['total'] if rows and rows[0]['total'] else 0.0


class QueryHeatmapModel(BaseModel):
    """Model for query_heatmap table"""
    
    table = 'query_heatmap'
    fields = ['heatmap_id', 'query_hash', 'query_example', 'frequency',
              'avg_retrieval_accuracy', 'avg_response_time_ms', 'avg_user_feedback',
              'quality_category', 'last_queried']
    
    def update_or_create_heatmap(self, query_hash: str, query_example: str,
                                retrieval_accuracy: float, response_time_ms: int,
                                user_feedback: Optional[int] = None):
        """
        Update existing query heatmap or create new one
        
        Args:
            query_hash: Hash of the query
            query_example: Example query text
            retrieval_accuracy: Retrieval accuracy score
            response_time_ms: Response time
            user_feedback: User feedback score
        """
        existing = self.raw_execute(
            "SELECT * FROM query_heatmap WHERE query_hash = ?",
            (query_hash,)
        )
        
        if existing:
            # Update existing entry
            row = existing[0]
            new_freq = row['frequency'] + 1
            new_accuracy = (row['avg_retrieval_accuracy'] * row['frequency'] + retrieval_accuracy) / new_freq
            new_time = (row['avg_response_time_ms'] * row['frequency'] + response_time_ms) / new_freq
            
            if user_feedback:
                if row['avg_user_feedback']:
                    new_feedback = (row['avg_user_feedback'] * row['frequency'] + user_feedback) / new_freq
                else:
                    new_feedback = user_feedback
            else:
                new_feedback = row['avg_user_feedback']
            
            self.raw_execute("""
                UPDATE query_heatmap
                SET frequency = ?, avg_retrieval_accuracy = ?,
                    avg_response_time_ms = ?, avg_user_feedback = ?,
                    last_queried = CURRENT_TIMESTAMP
                WHERE query_hash = ?
            """, (new_freq, new_accuracy, new_time, new_feedback, query_hash))
        else:
            # Insert new entry
            self.insert({
                'query_hash': query_hash,
                'query_example': query_example,
                'frequency': 1,
                'avg_retrieval_accuracy': retrieval_accuracy,
                'avg_response_time_ms': response_time_ms,
                'avg_user_feedback': user_feedback,
                'quality_category': 'warm'
            })
    
    def get_cold_spots(self, threshold: int = 10, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get low-frequency queries (cold spots)
        
        Args:
            threshold: Frequency threshold
            limit: Maximum results
            
        Returns:
            List of cold spot queries
        """
        return self.raw_execute("""
            SELECT * FROM query_heatmap
            WHERE frequency < ?
            ORDER BY frequency ASC
            LIMIT ?
        """, (threshold, limit))
    
    def get_poor_quality_queries(self, threshold: float = 3.0, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get poor quality queries
        
        Args:
            threshold: User feedback threshold
            limit: Maximum results
            
        Returns:
            List of poor quality queries
        """
        return self.raw_execute("""
            SELECT * FROM query_heatmap
            WHERE avg_user_feedback IS NOT NULL AND avg_user_feedback < ?
            ORDER BY avg_user_feedback ASC
            LIMIT ?
        """, (threshold, limit))
    
    def get_slow_queries(self, threshold_ms: int = 5000, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get slow queries
        
        Args:
            threshold_ms: Response time threshold
            limit: Maximum results
            
        Returns:
            List of slow queries
        """
        return self.raw_execute("""
            SELECT * FROM query_heatmap
            WHERE avg_response_time_ms > ?
            ORDER BY avg_response_time_ms DESC
            LIMIT ?
        """, (threshold_ms, limit))
    
    def get_heatmap_analysis(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get comprehensive heatmap analysis
        
        Returns:
            Dictionary with cold_spots, poor_quality, and slow_queries
        """
        return {
            'cold_spots': self.get_cold_spots(),
            'poor_quality': self.get_poor_quality_queries(),
            'slow_queries': self.get_slow_queries()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get query heatmap statistics
        
        Returns:
            Dictionary with heatmap statistics
        """
        stats = {}
        
        # Total queries
        result = self.raw_execute("SELECT COUNT(*) as count FROM query_heatmap")
        stats['total_unique_queries'] = result[0]['count'] if result else 0
        
        # Total frequency
        result = self.raw_execute("SELECT SUM(frequency) as total FROM query_heatmap")
        stats['total_query_invocations'] = result[0]['total'] if result and result[0]['total'] else 0
        
        # Average accuracy
        result = self.raw_execute("SELECT AVG(avg_retrieval_accuracy) as avg FROM query_heatmap")
        stats['avg_retrieval_accuracy'] = result[0]['avg'] if result and result[0]['avg'] else 0.0
        
        # Average response time
        result = self.raw_execute("SELECT AVG(avg_response_time_ms) as avg FROM query_heatmap")
        stats['avg_response_time_ms'] = result[0]['avg'] if result and result[0]['avg'] else 0.0
        
        # Quality distribution
        result = self.raw_execute("""
            SELECT
                quality_category,
                COUNT(*) as count
            FROM query_heatmap
            GROUP BY quality_category
        """)
        stats['quality_distribution'] = {row['quality_category']: row['count'] for row in result} if result else {}
        
        return stats
    
    def get_avg_user_feedback(self) -> float:
        """
        Get average user feedback score for all queries
        
        Returns:
            Average user feedback score
        """
        rows = self.raw_execute("""
            SELECT AVG(avg_user_feedback) as avg_fb 
            FROM query_heatmap 
            WHERE avg_user_feedback IS NOT NULL
        """)
        return rows[0]['avg_fb'] if rows and rows[0]['avg_fb'] else 0.0


class SyntheticQueryModel(BaseModel):
    """Model for synthetic_queries table"""
    
    table = 'synthetic_queries'
    fields = ['synthetic_id', 'doc_id', 'question', 'expected_answer',
              'generated_date', 'last_tested', 'test_accuracy']
    
    def store_synthetic_question(self, doc_id: str, question: str,
                                expected_answer: Optional[str] = None) -> int:
        """
        Store a synthetic question for a document
        
        Args:
            doc_id: Document ID
            question: Generated question
            expected_answer: Optional expected answer
            
        Returns:
            Last inserted row ID
        """
        return self.insert({
            'doc_id': doc_id,
            'question': question,
            'expected_answer': expected_answer
        })
    
    def get_synthetic_questions_for_document(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Get all synthetic questions for a document
        
        Args:
            doc_id: Document ID
            
        Returns:
            List of synthetic questions
        """
        return self.raw_execute(
            "SELECT * FROM synthetic_queries WHERE doc_id = ? ORDER BY generated_date DESC",
            (doc_id,)
        )
