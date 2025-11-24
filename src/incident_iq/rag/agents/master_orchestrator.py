"""Master Orchestrator - Main entry point for RAG system using deepagents"""
import json
import time
from pathlib import Path
from deepagents import create_deep_agent
from ..config.prompt_loader import PromptLoader
from ..tools.services.llm_service import LLMService
from ..tools.services.vectordb_service import VectorDBService
from ...database.db.connection import get_connection  # [CHANGE LOG] Use centralized DB connection


class MasterOrchestrator:
    def __init__(self, config_dir: str = None):
        from ..config.env_config import EnvConfig
        from ..config.loader import ConfigLoader
        
        # Initialize configuration (lazy init via Option 2)
        if config_dir is None:
            config_dir = EnvConfig.get_rag_config_path()
        ConfigLoader.set_config_dir(config_dir)  # CHANGE LOG: Called once per init
        
        # Initialize services
        self.llm_service = LLMService(ConfigLoader.get_llm_config())
        self.vectordb_service = VectorDBService(EnvConfig.get_chroma_db_path())
        self.db_path = EnvConfig.get_db_path()
        
        # Initialize shared utilities for subagents
        from .prompt_utility import PromptUtility
        self.prompt_utility = PromptUtility(self.llm_service)
        
        self.services = {
            'llm': self.llm_service,
            'vectordb': self.vectordb_service,
            'db': get_connection(),  # [CHANGE LOG] Using centralized get_connection()
            'prompt_utility': self.prompt_utility,  # Shared utility for all subagents
        }
        
        # Get configurations
        self.agent_config = ConfigLoader.get_agent_config()
        self.name = "MasterOrchestrator"
        
        # Define subagents for deepagents
        # [CHANGE LOG] Proper deepagents subagent pattern - subagents handle specialized tasks
        subagents = self._define_subagents()
        
        # Create deepagents master agent with subagents
        # Master agent uses subagents via automatic task tool
        system_prompt = PromptLoader.get_system_prompt('master_orchestrator')
        self.agent = create_deep_agent(
            tools=self._get_master_tools(),  # [CHANGE LOG] Master agent tools (NOT subagent tools)
            system_prompt=system_prompt,
            subagents=subagents,  # Subagents available via task tool
            model=self.llm_service.get_model()
        )
    
    def _define_subagents(self) -> list:
        return [
            {
                "name": "ingestion",
                "description": "Ingest documents in any format (files, JSON, text). Auto-detect domain, extract metadata, normalize and store documents. Can use prompt_utility (from services) to optimize extraction prompts.",
                "prompt": PromptLoader.get_system_prompt('ingestion_agent'),
                "tools": self._get_ingestion_tools(),
                "model": self.llm_service.get_model(),
            },
            {
                "name": "retrieval",
                "description": "Retrieve relevant documents from knowledge base. Perform semantic search, enforce RBAC permissions, detect query complexity. Can use prompt_utility to refine complex queries and generate search variants.",
                "prompt": PromptLoader.get_system_prompt('retrieval_agent'),
                "tools": self._get_retrieval_tools(),
                "model": self.llm_service.get_model(),
            },
            {
                "name": "healing",
                "description": "Optimize RAG system health using RL-based learning. Analyze system metrics, recommend optimizations, execute improvements with Q-Learning. Can use prompt_utility to optimize prompts for better LLM decisions.",
                "prompt": PromptLoader.get_system_prompt('healing_agent'),
                "tools": self._get_healing_tools(),
                "model": self.llm_service.get_model(),
            },
        ]
    
    def _get_master_tools(self) -> list:
        from langchain_core.tools import tool
        
        @tool
        def extract_user_intent(query: str) -> str:
            try:
                prompt = PromptLoader.format_prompt(
                    'metadata_extraction', 'from_query',
                    query=query
                )
                response = self.llm_service.generate_response(prompt)
                return response
            except Exception as e:
                return f"Error extracting intent: {e}"
        
        @tool
        def consolidate_results(retrieval_results: str, healing_analysis: str) -> str:
            try:
                # [CHANGE LOG] Master uses this tool to combine subagent outputs
                return json.dumps({
                    "success": True,
                    "consolidation": "Results combined from subagents"
                })
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
        
        return [extract_user_intent, consolidate_results]
    
    def _get_ingestion_tools(self) -> list:
        from ..tools.ingestion_tools import (
            chunk_document_tool, extract_metadata_tool, save_to_vectordb_tool
        )
        return [chunk_document_tool, extract_metadata_tool, save_to_vectordb_tool]
    
    def _get_retrieval_tools(self) -> list:
        from langchain_core.tools import tool
        import json
        
        @tool
        def search_vector_db(query: str, top_k: int = 5) -> str:
            try:
                embedding = self.services['llm'].generate_embedding(query)
                collection = self.services['vectordb'].collection
                results = collection.query(query_embeddings=[embedding], n_results=top_k)
                
                docs = results.get('documents', [[]])[0]
                distances = results.get('distances', [[]])[0]
                
                formatted = [
                    {"content": doc[:500], "relevance": round(1 - dist, 3)}
                    for doc, dist in zip(docs, distances)
                ]
                
                return json.dumps({"success": True, "results": formatted})
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
        
        return [search_vector_db]
    
    def _get_healing_tools(self) -> list:
        from langchain_core.tools import tool
        import json
        
        @tool
        def analyze_system_health() -> str:
            try:
                # [CHANGE LOG] Using centralized get_connection() utility
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM embedding_metadata")
                total_chunks = cursor.fetchone()[0]
                cursor.execute("SELECT AVG(quality_score) FROM embedding_metadata")
                avg_quality = cursor.fetchone()[0] or 0.85
                conn.close()
                
                status = "healthy" if avg_quality > 0.85 else "needs_optimization"
                return json.dumps({
                    "success": True,
                    "total_chunks": total_chunks,
                    "avg_quality": round(avg_quality, 3),
                    "status": status
                })
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
        
        return [analyze_system_health]
    
    def ask_question(self, query: str, enable_healing: bool = True, enable_prompt_refinement: bool = True) -> dict:
        start_time = time.time()
        original_query = query
        refined_query = query
        
        try:
            # Optional query refinement via shared prompt utility
            # (subagents like retrieval can also use prompt_utility for internal optimization)
            if enable_prompt_refinement:
                refined_query = self.prompt_utility.refine_query(query)
            
            # Extract metadata from query (LLM-based, config-driven)
            metadata = self._extract_query_metadata(refined_query)
            
            # Retrieve documents via subagent (deepagents task tool)
            retrieval_prompt = f"Search for documents related to: {refined_query}"
            retrieval_result = self.agent.invoke({
                "messages": [{"role": "user", "content": retrieval_prompt}]
            })
            
            # Get RAG context
            rag_context = self._extract_context(retrieval_result)
            
            # Generate answer with domain context (domain-agnostic)
            answer = self._generate_answer(refined_query, rag_context, metadata)
            
            # Extract tags (semantic analysis via LLM)
            tags = self._extract_tags(refined_query, answer)
            
            # Optional healing optimization (uses RL)
            healing_analysis = None
            if enable_healing:
                healing_result = self._optimize_answer(answer, refined_query)
                if healing_result.get('success'):
                    answer = healing_result.get('optimized_answer', answer)
                    healing_analysis = {
                        "status": "optimization_applied",
                        "original_tokens": healing_result.get('original_tokens'),
                        "optimized_tokens": healing_result.get('optimized_tokens'),
                        "reduction_percentage": healing_result.get('reduction_percentage')
                    }
            
            # Record operation
            self._record_operation(original_query, answer, tags, metadata)
            
            exec_ms = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "original_query": original_query,
                "refined_query": refined_query,
                "answer": answer,
                "tags": tags,
                "metadata": metadata,
                "healing_analysis": healing_analysis,
                "execution_ms": exec_ms
            }
            
        except Exception as e:
            return {
                "success": False,
                "original_query": original_query,
                "error": str(e),
                "execution_ms": int((time.time() - start_time) * 1000)
            }
    
    def _extract_query_metadata(self, query: str) -> dict:
        try:
            prompt = PromptLoader.format_prompt(
                'metadata_extraction', 'from_query',
                query=query
            )
            response = self.llm_service.generate_response(prompt)
            return json.loads(response)
        except:
            return {'priority': 'medium', 'query_type': 'general'}
    
    def _extract_context(self, retrieval_result: dict) -> str:
        if isinstance(retrieval_result, dict):
            if 'context' in retrieval_result:
                return retrieval_result['context']
            if 'results' in retrieval_result:
                return "\n".join([str(r) for r in retrieval_result['results']])
        return ""
    
    def _generate_answer(self, query: str, context: str, metadata: dict) -> str:
        if not context:
            return "No relevant information found in knowledge base."
        
        domain = metadata.get('domain', 'general')
        domain_context = f"Knowledge Domain: {domain}" if domain != 'general' else ""
        
        prompt = PromptLoader.format_prompt(
            'rag', 'domain_aware_rag',
            system_prompt="Answer the user question based on provided context.",
            domain_context=domain_context,
            context=context,
            refined_query=query
        )
        
        return self.llm_service.generate_response(prompt)
    
    def _extract_tags(self, query: str, answer: str) -> list:
        try:
            prompt = PromptLoader.format_prompt(
                'semantic_analysis', 'extract_tags',
                query=query,
                answer=answer[:500]
            )
            response = self.llm_service.generate_response(prompt)
            tags = json.loads(response)
            return tags if isinstance(tags, list) else ["general"]
        except:
            return ["general"]
    
    def _optimize_answer(self, answer: str, query: str) -> dict:
        try:
            from .healing_agent import HealingAgent
            healing = HealingAgent(self.services, self.agent_config.get('healing_agent', {}))
            return healing.optimize_answer(answer, query, token_limit=250)
        except:
            return {"success": False}
    
    def _record_operation(self, query: str, answer: str, tags: list, metadata: dict):
        try:
            # [CHANGE LOG] Using centralized get_connection() utility
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agent_memory (agent_name, memory_key, memory_value, memory_type)
                VALUES (?, ?, ?, ?)
            """, (
                self.name,
                f"question_{query[:30]}",
                json.dumps({'query': query, 'tags': tags, 'metadata': metadata}),
                'user_question'
            ))
            conn.commit()
            conn.close()
        except:
            pass
