"""
Agent Operation Models - Tracks agent operations, token usage, and memory
"""
from typing import List, Dict, Any, Optional
import json
from .base_model import BaseModel


class AgentOperationModel(BaseModel):
    """Model for agent_operations table"""
    
    table = 'agent_operations'
    fields = ['operation_id', 'agent_name', 'operation_type', 'query', 'retrieved_chunks',
              'reranker_scores', 'final_response', 'user_feedback', 'response_time_ms',
              'token_count', 'metadata', 'timestamp']
    
    def log_operation(self, agent_name: str, operation_type: str,
                     query: Optional[str] = None,
                     retrieved_chunks: Optional[List[str]] = None,
                     reranker_scores: Optional[List[float]] = None,
                     final_response: Optional[str] = None,
                     user_feedback: Optional[int] = None,
                     response_time_ms: Optional[int] = None,
                     token_count: Optional[int] = None,
                     metadata: Optional[Dict] = None) -> int:
        """
        Log an agent operation
        
        Args:
            agent_name: Name of the agent
            operation_type: Type of operation (ingest, retrieve, heal, etc.)
            query: User query (if applicable)
            retrieved_chunks: Chunks retrieved by agent
            reranker_scores: Reranker scores for chunks
            final_response: Final response from agent
            user_feedback: User feedback score
            response_time_ms: Response time in milliseconds
            token_count: Token count used
            metadata: Additional metadata
            
        Returns:
            Last inserted row ID
        """
        return self.insert({
            'agent_name': agent_name,
            'operation_type': operation_type,
            'query': query,
            'retrieved_chunks': json.dumps(retrieved_chunks) if retrieved_chunks else None,
            'reranker_scores': json.dumps(reranker_scores) if reranker_scores else None,
            'final_response': final_response,
            'user_feedback': user_feedback,
            'response_time_ms': response_time_ms,
            'token_count': token_count,
            'metadata': json.dumps(metadata) if metadata else None
        })
    
    def get_operations_by_agent(self, agent_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get operations for a specific agent
        
        Args:
            agent_name: Agent name filter
            limit: Maximum results
            
        Returns:
            List of operations
        """
        return self.raw_execute("""
            SELECT * FROM agent_operations
            WHERE agent_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (agent_name, limit))
    
    def get_operations_by_type(self, operation_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get operations of specific type
        
        Args:
            operation_type: Operation type filter
            limit: Maximum results
            
        Returns:
            List of operations
        """
        return self.raw_execute("""
            SELECT * FROM agent_operations
            WHERE operation_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (operation_type, limit))
    
    def get_operations_with_feedback(self) -> List[Dict[str, Any]]:
        """
        Get operations that have user feedback
        
        Returns:
            List of operations with user feedback
        """
        return self.raw_execute("""
            SELECT * FROM agent_operations
            WHERE user_feedback IS NOT NULL
            ORDER BY timestamp DESC
        """)
    
    def get_recent_operations_count(self, hours: int = 24) -> int:
        """
        Get count of operations in last N hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Count of recent operations
        """
        rows = self.raw_execute(f"""
            SELECT COUNT(*) as count FROM agent_operations 
            WHERE timestamp > datetime('now', '-{hours} hours')
        """)
        return rows[0]['count'] if rows else 0
    
    def get_total_tokens_used(self) -> int:
        """
        Get total tokens used across all operations
        
        Returns:
            Total token count
        """
        rows = self.raw_execute("SELECT SUM(total_tokens) as total FROM llm_token_usage")
        return rows[0]['total'] if rows and rows[0]['total'] else 0


class TokenUsageModel(BaseModel):
    """Model for llm_token_usage table"""
    
    table = 'llm_token_usage'
    fields = ['usage_id', 'agent_name', 'operation_id', 'provider', 'model',
              'prompt_tokens', 'completion_tokens', 'total_tokens',
              'estimated_cost', 'timestamp']
    
    def log_token_usage(self, agent_name: str, operation_id: Optional[int],
                       provider: str, model: str,
                       prompt_tokens: int, completion_tokens: int,
                       estimated_cost: float = 0.0) -> int:
        """
        Log LLM token usage
        
        Args:
            agent_name: Agent name
            operation_id: Associated operation ID
            provider: LLM provider (openai, anthropic, ollama, etc.)
            model: Model name
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in completion
            estimated_cost: Estimated cost
            
        Returns:
            Last inserted row ID
        """
        total_tokens = prompt_tokens + completion_tokens
        return self.insert({
            'agent_name': agent_name,
            'operation_id': operation_id,
            'provider': provider,
            'model': model,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens,
            'estimated_cost': estimated_cost
        })
    
    def get_token_usage_by_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Get token usage summary for an agent
        
        Args:
            agent_name: Agent name
            
        Returns:
            Dictionary with token usage stats
        """
        rows = self.raw_execute("""
            SELECT
                COUNT(*) as call_count,
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(completion_tokens) as total_completion_tokens,
                SUM(total_tokens) as total_tokens,
                SUM(estimated_cost) as total_cost,
                AVG(prompt_tokens) as avg_prompt_tokens,
                AVG(total_tokens) as avg_total_tokens
            FROM llm_token_usage
            WHERE agent_name = ?
        """, (agent_name,))
        
        if rows and rows[0]:
            return dict(rows[0])
        return {}
    
    def get_token_usage_by_model(self) -> List[Dict[str, Any]]:
        """
        Get token usage grouped by model
        
        Returns:
            List of model usage statistics
        """
        return self.raw_execute("""
            SELECT
                model,
                provider,
                COUNT(*) as call_count,
                SUM(total_tokens) as total_tokens,
                SUM(estimated_cost) as total_cost,
                AVG(total_tokens) as avg_tokens
            FROM llm_token_usage
            GROUP BY model, provider
            ORDER BY total_cost DESC
        """)
    
    def get_total_cost(self) -> float:
        """
        Get total estimated cost across all token usage
        
        Returns:
            Total estimated cost
        """
        rows = self.raw_execute("SELECT SUM(estimated_cost) as total FROM llm_token_usage")
        return rows[0]['total'] if rows and rows[0]['total'] else 0.0


class AgentMemoryModel(BaseModel):
    """Model for agent_memory table"""
    
    table = 'agent_memory'
    fields = ['memory_id', 'agent_name', 'memory_key', 'memory_value', 'memory_type', 'timestamp']
    
    def store_memory(self, agent_name: str, memory_key: str, memory_value: str,
                    memory_type: str = 'execution_result') -> int:
        """
        Store memory/context for an agent
        
        Args:
            agent_name: Agent name
            memory_key: Memory key
            memory_value: Memory value
            memory_type: Type of memory (execution_result, context, learned_pattern, etc.)
            
        Returns:
            Last inserted row ID
        """
        return self.insert({
            'agent_name': agent_name,
            'memory_key': memory_key,
            'memory_value': memory_value,
            'memory_type': memory_type
        })
    
    def get_memory(self, agent_name: str, memory_key: str) -> Optional[str]:
        """
        Retrieve stored memory for an agent
        
        Args:
            agent_name: Agent name
            memory_key: Memory key
            
        Returns:
            Memory value or None
        """
        rows = self.raw_execute("""
            SELECT memory_value FROM agent_memory
            WHERE agent_name = ? AND memory_key = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (agent_name, memory_key))
        
        return rows[0]['memory_value'] if rows else None
    
    def get_all_agent_memory(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        Get all memory records for an agent
        
        Args:
            agent_name: Agent name
            
        Returns:
            List of memory records
        """
        return self.raw_execute("""
            SELECT * FROM agent_memory
            WHERE agent_name = ?
            ORDER BY timestamp DESC
        """, (agent_name,))
    
    def get_memory_by_type(self, agent_name: str, memory_type: str) -> List[Dict[str, Any]]:
        """
        Get memory records by type for an agent
        
        Args:
            agent_name: Agent name
            memory_type: Memory type filter
            
        Returns:
            List of memory records
        """
        return self.raw_execute("""
            SELECT * FROM agent_memory
            WHERE agent_name = ? AND memory_type = ?
            ORDER BY timestamp DESC
        """, (agent_name, memory_type))
    
    def clear_agent_memory(self, agent_name: str) -> None:
        """
        Clear all memory for an agent
        
        Args:
            agent_name: Agent name
        """
        self.conn.execute(
            "DELETE FROM agent_memory WHERE agent_name = ?",
            (agent_name,)
        )
        self.conn.commit()
