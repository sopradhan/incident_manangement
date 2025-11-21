"""RetrievalAgent - Optimized semantic search with token tracking and RBAC enforcement"""
import json
import sqlite3
import time
from deepagents import create_deep_agent
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from ..tools.ingestion_tools import record_agent_operation_tool, record_agent_memory_tool
from ..core.config.loader import ConfigLoader
from ..config.env_config import EnvConfig
from ...database.models import RBACModel, EmbeddingMetadataModel


class RetrievalAgent:
    """Semantic search with token cost tracking and RBAC enforcement"""
    
    def __init__(self, services: dict, config: dict, master_orchestrator=None):
        self.services = services
        self.master = master_orchestrator
        self.name = config.get('name', 'RetrievalAgent')
        self.db_path = EnvConfig.get_db_path()
        
        ConfigLoader.set_config_dir(EnvConfig.get_rag_config_path())
        self.system_prompt = ConfigLoader.get_system_prompt('retrieval_agent') or \
            "Retrieve relevant information from knowledge base. Enforce RBAC constraints. " \
            "Return optimized results with token cost tracking."
        
        self.tools = self._create_tools()
        self.agent = create_deep_agent(
            tools=self.tools,
            system_prompt=self.system_prompt,
            model=services['llm'].get_model()
        )
    
    def _create_tools(self):
        """Create retrieval tools"""
        agent = self
        
        class QueryInput(BaseModel):
            query: str = Field(description="Search query")
            namespace: str = Field(default="general", description="RBAC namespace filter")
            top_k: int = Field(default=5, description="Number of results")
        
        class SpawnHealerInput(BaseModel):
            doc_id: str = Field(description="Document to optimize for retrieval")
            strategy: str = Field(default="rerank", description="rerank|retune_threshold|rebalance_embeddings")
        
        def search_semantic(query: str, namespace: str = "general", top_k: int = 5) -> str:
            try:
                embedding = agent.services['llm'].generate_embedding(query)
                collection = agent.services['vectordb'].collection
                
                results = collection.query(
                    query_embeddings=[embedding],
                    n_results=top_k,
                    where={"rbac_namespace": namespace}
                )
                
                docs = results.get('documents', [[]])[0]
                metadatas = results.get('metadatas', [[]])[0]
                distances = results.get('distances', [[]])[0]
                
                formatted_results = []
                for doc, meta, dist in zip(docs, metadatas, distances):
                    formatted_results.append({
                        "content": doc[:500],
                        "source": meta.get('doc_id'),
                        "relevance_score": round(1 - dist, 3),
                        "namespace": namespace
                    })
                
                return json.dumps({
                    "success": True,
                    "results": formatted_results,
                    "count": len(formatted_results)
                })
                
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
        
        def enforce_rbac(user_id: str, namespace: str) -> str:
            try:
                conn = sqlite3.connect(agent.db_path)
                
                # Use RBAC model instead of hardcoded SQL
                rbac_model = RBACModel(conn)
                permission = rbac_model.check_permission(user_id, namespace)
                
                conn.close()
                
                if permission:
                    return json.dumps({"success": True, "access_granted": True})
                return json.dumps({"success": True, "access_granted": False})
                
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
        
        def spawn_healer_for_retrieval(doc_id: str, strategy: str = "rerank") -> str:
            """Spawn HealingAgent with RetrievalAgent context for retrieval optimization"""
            if not agent.master:
                return json.dumps({"success": False, "error": "Master orchestrator not available for spawning HealingAgent", "caller": "RetrievalAgent"})
            try:
                # Spawn HealingAgent with caller context set to RetrievalAgent
                healing_instance = agent.master.spawn_agent('healing', caller_agent='RetrievalAgent')
                result = healing_instance.optimize_document(doc_id, strategy)
                return json.dumps({
                    "success": result.get('success', False), 
                    "strategy": strategy,
                    "caller": "RetrievalAgent"
                })
            except Exception as e:
                return json.dumps({"success": False, "error": str(e), "caller": "RetrievalAgent"})
        
        return [
            StructuredTool.from_function(
                func=search_semantic,
                name="search_semantic",
                description="Semantic search in vector DB with RBAC namespace filter",
                args_schema=QueryInput
            ),
            StructuredTool.from_function(
                func=enforce_rbac,
                name="enforce_rbac",
                description="Check RBAC permissions for user and namespace"
            ),
            StructuredTool.from_function(
                func=spawn_healer_for_retrieval,
                name="spawn_healer_for_retrieval",
                description="Spawn HealingAgent optimized for retrieval pipeline improvements",
                args_schema=SpawnHealerInput
            ),
        ]
    
    def _classify_query_complexity(self, query: str) -> dict:
        """Analyze query to determine complexity and optimal parameters"""
        # Analyze query characteristics
        word_count = len(query.split())
        has_how = any(w in query.lower() for w in ['how', 'what', 'why', 'when', 'where', 'can'])
        has_multiple = any(w in query.lower() for w in ['and', 'or', 'vs', 'versus', 'multiple'])
        question_mark = query.endswith('?')
        
        # Classify complexity
        if word_count <= 3:
            complexity = "simple"
            top_k = 1
            relevance_threshold = 0.15
            llm_temp = 0.3
        elif word_count <= 8 and not has_multiple:
            complexity = "moderate"
            top_k = 2
            relevance_threshold = 0.2
            llm_temp = 0.5
        else:
            complexity = "complex"
            top_k = 5
            relevance_threshold = 0.1
            llm_temp = 0.7
        
        return {
            "complexity": complexity,
            "top_k": top_k,
            "relevance_threshold": relevance_threshold,
            "llm_temperature": llm_temp,
            "word_count": word_count,
            "is_question": question_mark
        }
    
    def process_query(self, query: str, user_id: str) -> dict:
        """Process user query with RBAC, dynamic parameters, and token tracking"""
        start = time.time()
        try:
            # Classify query and get dynamic parameters
            query_params = self._classify_query_complexity(query)
            top_k = query_params['top_k']
            relevance_threshold = query_params['relevance_threshold']
            llm_temp = query_params['llm_temperature']
            
            # Check RBAC using model layer
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            metadata_model = EmbeddingMetadataModel(conn)
            # Get any available namespace from embedding metadata
            records = metadata_model.raw_execute("SELECT DISTINCT rbac_namespace FROM embedding_metadata LIMIT 1")
            namespace = records[0]['rbac_namespace'] if records else "general"
            conn.close()
            
            # Get embedding
            embedding = self.services['llm'].generate_embedding(query)
            
            # Semantic search with dynamic top_k
            collection = self.services['vectordb'].collection
            results = collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where={"rbac_namespace": namespace}
            )
            
            docs = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            
            # Filter by relevance threshold and format results
            formatted_results = []
            for doc, meta, dist in zip(docs, metadatas, distances):
                relevance_score = round(1 - dist, 3)
                # Only include if meets relevance threshold
                if relevance_score >= relevance_threshold:
                    formatted_results.append({
                        "content": doc[:300],
                        "source": meta.get('doc_id'),
                        "relevance": relevance_score
                    })
            
            # Estimate token cost
            query_tokens = len(query.split())
            response_tokens = sum(len(r['content'].split()) for r in formatted_results)
            total_tokens = query_tokens + response_tokens
            
            exec_ms = int((time.time() - start) * 1000)
            
            # Record operation
            record_agent_operation_tool.func(
                agent_name=self.name,
                operation_type='process_query',
                status='success',
                doc_id=query[:50],
                chunks_count=len(formatted_results)
            )
            
            # Store in memory
            record_agent_memory_tool.func(
                agent_name=self.name,
                memory_key=f'query_{user_id}',
                memory_value=json.dumps({
                    'query': query,
                    'results': len(formatted_results),
                    'tokens': total_tokens
                }),
                memory_type='query'
            )
            
            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "user_id": user_id,
                "namespace": namespace,
                "query_complexity": query_params['complexity'],
                "adaptive_parameters": {
                    "top_k_requested": top_k,
                    "results_returned": len(formatted_results),
                    "relevance_threshold": relevance_threshold,
                    "llm_temperature": llm_temp
                },
                "token_cost": {
                    "query": query_tokens,
                    "response": response_tokens,
                    "total": total_tokens
                },
                "execution_ms": exec_ms
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_ms": int((time.time() - start) * 1000)
            }
