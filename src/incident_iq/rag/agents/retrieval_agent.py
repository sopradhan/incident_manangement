"""RetrievalAgent - Clean semantic search with RBAC and config-driven prompts"""
import json
import time
from typing import Dict, Any
from deepagents import create_deep_agent
from langchain_core.tools import tool
from ..config.prompt_loader import PromptLoader
from ..config.env_config import EnvConfig


class RetrievalAgent:
    def __init__(self, services: dict, config: dict, master_orchestrator=None):
        self.services = services
        self.master = master_orchestrator
        self.name = "RetrievalAgent"
        self.db_path = EnvConfig.get_db_path()
        self.top_k = config.get('top_k', 5)
        
        # Create deepagents agent with retrieval tools
        system_prompt = PromptLoader.get_system_prompt('retrieval_agent')
        tools = self._create_tools()
        
        self.agent = create_deep_agent(
            tools=tools,
            system_prompt=system_prompt,
            model=services['llm'].get_model()
        )
    
    def _create_tools(self) -> list:
        
        @tool
        def search_vector_db(query: str, top_k: int = None) -> str:
            k = top_k or self.top_k
            embedding = self.services['llm'].generate_embedding(query)
            collection = self.services['vectordb'].collection
            
            results = collection.query(
                query_embeddings=[embedding],
                n_results=k
            )
            
            docs = results.get('documents', [[]])[0]
            distances = results.get('distances', [[]])[0]
            
            formatted = []
            for doc, dist in zip(docs, distances):
                formatted.append({
                    "content": doc[:500],
                    "relevance": round(1 - dist, 3)
                })
            
            return json.dumps({
                "success": True,
                "results": formatted,
                "count": len(formatted)
            })
        
        @tool
        def enforce_rbac(user_id: str, namespace: str) -> str:
            user_level = self._get_user_level(user_id)
            namespace_level = self._get_namespace_level(namespace)
            allowed = user_level >= namespace_level
            
            return json.dumps({
                "success": True,
                "user_id": user_id,
                "namespace": namespace,
                "allowed": allowed
            })
        
        return [search_vector_db, enforce_rbac]
    
    def process_query(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        start = time.time()
        
        result = self.agent.invoke({
            "messages": [{"role": "user", "content": f"Search for: {query}"}]
        })
        
        documents = self._extract_documents(result)
        complexity = self._detect_complexity(query)
        namespace = self._determine_namespace(query)
        
        return {
            "success": True,
            "results": documents,
            "query_complexity": complexity,
            "namespace": namespace,
            "execution_ms": int((time.time() - start) * 1000)
        }
    
    def _extract_documents(self, result: dict) -> list:
        if isinstance(result, dict) and 'results' in result:
            return result['results']
        return []
    
    def _detect_complexity(self, query: str) -> str:
        word_count = len(query.split())
        
        if word_count > 20:
            return 'complex'
        elif word_count > 10:
            return 'medium'
        else:
            return 'simple'
    
    def _determine_namespace(self, query: str) -> str:
        prompt = PromptLoader.format_prompt(
            'rbac', 'determine_namespace',
            query=query
        )
        response = self.services['llm'].generate_response(prompt).strip().lower()
        
        valid_namespaces = ['public', 'standard', 'restricted', 'confidential']
        return response if response in valid_namespaces else 'standard'
    
    def _get_user_level(self, user_id: str) -> int:
        # In production, query actual user roles from database
        return 2  # Default to restricted
    
    def _get_namespace_level(self, namespace: str) -> int:
        levels = {
            'public': 0,
            'standard': 1,
            'restricted': 2,
            'confidential': 3
        }
        return levels.get(namespace, 1)
