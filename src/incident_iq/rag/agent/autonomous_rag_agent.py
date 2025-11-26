"""
Autonomous Agentic RAG System

Master orchestrator with explicit service injection for LLM, VectorDB, and Config.
Provides: autonomous ingestion, retrieval, optimization, and full traceability.
"""
import os
import json
from typing import Any, Dict, List

# Import RAG tools (all require explicit service injection)
from ..tools.ingestion_tools import (
    extract_metadata_tool,
    chunk_document_tool,
    save_to_vectordb_tool,
    update_metadata_tracking_tool,
    ingest_sqlite_table_tool,
    record_agent_memory_tool,
)
from ..tools.retrieval_tools import (
    retrieve_context_tool,
    rerank_context_tool,
    answer_question_tool,
    traceability_tool,
)
from ..tools.healing_tools import (
    check_embedding_health_tool,
    get_context_cost_tool,
    optimize_chunk_size_tool,
)
from ..tools.adjust_config_tool import adjust_config_tool
from ..tools.services.llm_service import LLMService
from ..tools.services.vectordb_service import VectorDBService


class ConfigService:
    """Manages RAG system configuration."""
    def __init__(self, config_path: str = "rag_config.json"):
        self.config_path = config_path
        self._load()

    def _load(self):
        """Load config from file or initialize empty."""
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "RAG_K_FINAL": 5,
                "RAG_CHUNK_SIZE": 512,
                "LLM_TEMPERATURE": 0.3
            }

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        self._load()
        return self.config

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration."""
        self.config.update(updates)
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)


def _get_services():
    """Initialize and return services."""
    # Load LLM config
    config_dir = os.path.join(os.path.dirname(__file__), "..", "config")
    llm_config_path = os.getenv("LLM_CONFIG_PATH", os.path.join(config_dir, "llm_config.json"))
    
    try:
        with open(llm_config_path, "r") as f:
            llm_config = json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Warning: LLM config not found at {llm_config_path}. Using defaults.")
        llm_config = {"default_provider": "ollama", "llm_providers": {}, "embedding_providers": {}}
    
    llm_service = LLMService(llm_config)
    vectordb_service = VectorDBService(
        persist_directory=os.getenv("CHROMA_DB_PATH", "./chroma_db"),
        collection_name=os.getenv("CHROMA_COLLECTION", "rag_embeddings")
    )
    config_service = ConfigService()
    
    return llm_service, vectordb_service, config_service


class AutonomousRAGAgent:
    """Master orchestrator for autonomous RAG operations."""
    
    def __init__(self):
        """Initialize agent with services."""
        self.llm_service, self.vectordb_service, self.config_service = _get_services()

    def ingest_document(
        self, 
        text: str, 
        doc_id: str, 
        metadata: Dict[str, Any] = None, 
        rbac_namespace: str = "general"
    ) -> Dict[str, Any]:
        """Ingest a document end-to-end."""
        try:
            # Step 1: Extract metadata
            meta_response = extract_metadata_tool(text, llm_service=self.llm_service)
            meta_data = json.loads(meta_response) if isinstance(meta_response, str) else meta_response
            meta_json = json.dumps(meta_data.get('metadata', {}))
            
            # Step 2: Chunk document
            chunks_response = chunk_document_tool(text, doc_id)
            chunks_data = json.loads(chunks_response) if isinstance(chunks_response, str) else chunks_response
            
            if not chunks_data.get('success'):
                return {"success": False, "error": chunks_data.get('error', 'Chunking failed')}
            
            # Step 3: Save to vector DB
            save_response = save_to_vectordb_tool(
                json.dumps(chunks_data), 
                doc_id, 
                llm_service=self.llm_service, 
                vectordb_service=self.vectordb_service, 
                metadata=meta_json, 
                rbac_namespace=rbac_namespace
            )
            save_data = json.loads(save_response) if isinstance(save_response, str) else save_response
            chunks_saved = save_data.get('chunks_saved', 0)
            
            # Step 4: Update metadata tracking
            update_response = update_metadata_tracking_tool(
                doc_id, "document_ingestion", rbac_namespace, 
                meta_json, chunks_saved
            )
            
            return {
                "success": True,
                "doc_id": doc_id,
                "chunks_count": chunks_data.get('num_chunks', 0),
                "chunks_saved": chunks_saved,
                "metadata": meta_data.get('metadata', {})
            }
        except Exception as e:
            import traceback
            return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

    def ask_question(
        self, 
        question: str, 
        rbac_namespace: str = "general",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Answer a question with full traceability."""
        try:
            # Step 1: Retrieve context
            context_response = retrieve_context_tool(
                question, 
                llm_service=self.llm_service, 
                vectordb_service=self.vectordb_service,
                top_k=top_k,
                rbac_namespace=rbac_namespace
            )
            context_data = json.loads(context_response) if isinstance(context_response, str) else context_response
            
            if not context_data.get('success'):
                return {"success": False, "error": context_data.get('error', 'Retrieval failed')}
            
            # Step 2: Rerank context
            reranked_response = rerank_context_tool(
                json.dumps(context_data), 
                llm_service=self.llm_service
            )
            reranked_data = json.loads(reranked_response) if isinstance(reranked_response, str) else reranked_response
            
            # Step 3: Generate answer
            answer_response = answer_question_tool(
                question, 
                json.dumps(reranked_data), 
                llm_service=self.llm_service
            )
            answer_data = json.loads(answer_response) if isinstance(answer_response, str) else answer_response
            
            # Step 4: Generate traceability
            trace_response = traceability_tool(
                question, 
                json.dumps(reranked_data), 
                vectordb_service=self.vectordb_service
            )
            trace_data = json.loads(trace_response) if isinstance(trace_response, str) else trace_response
            
            return {
                "success": True,
                "question": question,
                "answer": answer_data.get('answer', 'No answer generated'),
                "sources": reranked_data.get('ranked_results', []),
                "traceability": trace_data.get('traceability', {})
            }
        except Exception as e:
            import traceback
            return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

    def optimize(self, performance_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize RAG parameters based on performance history."""
        try:
            result = optimize_chunk_size_tool(performance_history, llm_service=self.llm_service)
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def adjust_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust system configuration."""
        try:
            result = adjust_config_tool(self.config_service, updates)
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_health(self, embeddings: List[List[float]], doc_id: str) -> Dict[str, Any]:
        """Check embedding health and quality."""
        try:
            result = check_embedding_health_tool(embeddings, doc_id, llm_service=self.llm_service)
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def estimate_cost(self, context: List[Dict[str, str]], model_name: str = "gemini-2.5-pro") -> Dict[str, Any]:
        """Estimate token cost of context."""
        try:
            result = get_context_cost_tool(context, llm_service=self.llm_service, model_name=model_name)
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def record_memory(self, agent_name: str, memory_key: str, memory_value: str, memory_type: str = "context") -> Dict[str, Any]:
        """Record agent memory/logs for debugging and retrieval."""
        try:
            result = record_agent_memory_tool(agent_name, memory_key, memory_value, memory_type)
            return json.loads(result) if isinstance(result, str) else result
        except Exception as e:
            return {"success": False, "error": str(e)}
