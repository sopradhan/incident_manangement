"""HealingAgent - RAG system optimization with RL-based learning and config-driven prompts"""
import json
import time
from deepagents import create_deep_agent
from langchain_core.tools import tool
from ..config.prompt_loader import PromptLoader
from ..config.env_config import EnvConfig
from ..config.loader import ConfigLoader
from .rl_healing_agent import RLHealingAgent, RLState
from ...database.db.connection import get_connection  # [CHANGE LOG] Use centralized DB connection


class HealingAgent:
    def __init__(self, services: dict, config: dict, master_orchestrator=None):
        self.services = services
        self.master = master_orchestrator
        self.name = "HealingAgent"
        self.db_path = EnvConfig.get_db_path()
        self.config = config
        
        # Initialize RL healing agent (Q-Learning)
        # [CHANGE LOG] Integrating existing rl_healing_agent.py for autonomous RL optimization
        self.rl_agent = RLHealingAgent(self, self.db_path)
        
        # Create deepagents agent with healing tools
        system_prompt = PromptLoader.get_system_prompt('healing_agent')
        tools = self._create_tools()
        
        self.agent = create_deep_agent(
            tools=tools,
            system_prompt=system_prompt,
            model=services['llm'].get_model()
        )
    
    def _create_tools(self) -> list:
        
        @tool
        def analyze_health() -> str:
            metrics = self.analyze_health()
            return json.dumps({"success": True, **metrics})
        
        @tool
        def optimize_chunk(doc_id: str, strategy: str) -> str:
            result = self.rl_agent.execute_action(strategy, doc_id)
            return json.dumps({"success": True, "result": result})
        
        return [analyze_health, optimize_chunk]
    
    def optimize_answer(self, answer: str, query: str, token_limit: int = 250) -> dict:
        start = time.time()
        
        current_tokens = len(answer.split())
        
        prompt = PromptLoader.format_prompt(
            'answer_optimization', 'optimize_answer',
            token_limit=token_limit,
            answer=answer
        )
        
        optimized = self.services['llm'].generate_response(prompt)
        optimized_tokens = len(optimized.split())
        
        quality = self._check_quality(answer, optimized)
        
        if self.master:
            from ..tools.ingestion_tools import record_agent_memory_tool
            record_agent_memory_tool.func(
                agent_name=self.name,
                memory_key=f'answer_optimization_{query[:30]}',
                memory_value=json.dumps({
                    'original_tokens': current_tokens,
                    'optimized_tokens': optimized_tokens,
                    'quality_maintained': quality
                }),
                memory_type='answer_optimization'
            )
        
        exec_ms = int((time.time() - start) * 1000)
        
        return {
            "success": True,
            "original_tokens": current_tokens,
            "optimized_tokens": optimized_tokens,
            "token_reduction": current_tokens - optimized_tokens,
            "reduction_percentage": round(
                (current_tokens - optimized_tokens) / current_tokens * 100, 1
            ) if current_tokens > 0 else 0,
            "quality_maintained": quality,
            "optimized_answer": optimized,
            "execution_ms": exec_ms
        }
    
    def analyze_health(self) -> dict:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM embedding_metadata")
        total_chunks = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT 
                AVG(quality_score) as avg_quality,
                COUNT(CASE WHEN quality_score < 0.85 THEN 1 END) as low_quality_count
            FROM embedding_metadata
        """)
        result = cursor.fetchone()
        avg_quality = result['avg_quality'] or 0.85
        low_quality_docs = result['low_quality_count'] or 0
        
        cursor.execute("SELECT COUNT(*) FROM agent_operation WHERE operation_type = 'query'")
        total_queries = cursor.fetchone()[0]
        
        conn.close()
        
        status = "healthy" if avg_quality > 0.85 else "needs_optimization"
        
        metrics = {
            "success": True,
            "total_chunks": total_chunks,
            "avg_quality": round(avg_quality, 3),
            "poor_quality_documents": low_quality_docs,
            "total_queries": total_queries,
            "status": status,
            "embedding_models": ["all_minilm_l6_v2"],
            "chunk_strategies": ["recursive"]
        }
        
        rl_state = RLState({
            "avg_quality_score": avg_quality,
            "low_quality_doc_count": low_quality_docs,
            "total_query_count": total_queries,
            "avg_response_time_ms": 1000,
            "total_tokens_used": 0,
            "reindex_attempts": 0
        })
        
        if self.rl_agent:
            action = self.rl_agent.select_action(rl_state)
            metrics["rl_recommended_action"] = action
        
        return metrics
    
    def suggest_optimization(self, doc_id: str, num_chunks: int) -> dict:
        return {
            "success": True,
            "doc_id": doc_id,
            "num_chunks": num_chunks,
            "strategies": ["reindex", "resample"],
            "reasoning": "Optimize chunk boundaries and embeddings"
        }
    
    def optimize_document(self, doc_id: str, strategy: str) -> dict:
        return {
            "success": True,
            "doc_id": doc_id,
            "strategy": strategy,
            "chunks_optimized": 0
        }
    
    def _check_quality(self, original: str, optimized: str) -> float:
        prompt = PromptLoader.format_prompt(
            'answer_optimization', 'quality_check',
            original_answer=original[:500],
            optimized_answer=optimized[:500]
        )
        
        response = self.services['llm'].generate_response(prompt)
        
        import re
        numbers = re.findall(r'\d+', response)
        return float(numbers[0]) / 100 if numbers else 0.85
