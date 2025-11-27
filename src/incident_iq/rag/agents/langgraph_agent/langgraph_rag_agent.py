"""
LangGraph-based Agentic RAG System

Uses LangGraph for proper workflow orchestration with nodes and edges.
- Ingestion workflow (documents, tables, PDFs, Word, Text files)
- Retrieval workflow with traceability and Guardrails validation
- Optimization workflow
"""
import os
import json
import time
import uuid
from typing import Any, Dict, List, Annotated
from pathlib import Path
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Import Guardrails for response validation
try:
    from guardrails import Guard
    from guardrails.hub import hallucination_check, security_incident_policy
    HAS_GUARDRAILS = True
except ImportError:
    HAS_GUARDRAILS = False

# Import visualization
from ...visualization.langgraph_visualizer import create_visualization, save_visualization

# Import RAG tools
# Ingestion tools: extract_metadata_tool, chunk_document_tool, save_to_vectordb_tool, 
#                  update_metadata_tracking_tool, ingest_sqlite_table_tool,
#                  ingest_documents_from_path_tool
# Optional tools: record_agent_memory_tool, extract_document_text_tool (for future use)
from ...tools.ingestion_tools import (
    extract_metadata_tool,
    chunk_document_tool,
    save_to_vectordb_tool,
    update_metadata_tracking_tool,
    ingest_sqlite_table_tool,
    record_agent_memory_tool,
    ingest_documents_from_path_tool,
    extract_document_text_tool,
)
from ...tools.retrieval_tools import (
    retrieve_context_tool,
    rerank_context_tool,
    answer_question_tool,
    traceability_tool,
)
from ...tools.healing_tools import (
    check_embedding_health_tool,
    get_context_cost_tool,
    optimize_chunk_size_tool,
)
from ...tools.adjust_config_tool import adjust_config_tool
from ...tools.services.llm_service import LLMService
from ...tools.services.vectordb_service import VectorDBService
from ...config.env_config import EnvConfig
from ..healing_agent.rl_healing_agent import RLHealingAgent


class LangGraphRAGState:
    """State object for LangGraph workflow."""
    def __init__(self):
        self.document_text: str = ""
        self.doc_id: str = ""
        self.question: str = ""
        self.metadata: Dict[str, Any] = {}
        self.chunks: Dict[str, Any] = {}
        self.context: Dict[str, Any] = {}
        self.reranked_context: Dict[str, Any] = {}
        self.answer: str = ""
        self.traceability: Dict[str, Any] = {}
        self.performance_history: List[Dict[str, Any]] = []
        self.config_updates: Dict[str, Any] = {}
        self.errors: List[str] = []


class LangGraphRAGAgent:
    """LangGraph-based RAG agent with workflow orchestration."""
    
    def __init__(self):
        """Initialize agent and build workflow graph."""
        self.llm_service, self.vectordb_service = self._init_services()
        self.rl_healing_agent = self._init_rl_agent()
        self.ingestion_graph = self._build_ingestion_graph()
        self.retrieval_graph = self._build_retrieval_graph()
        self.optimization_graph = self._build_optimization_graph()
        self.guardrails = self._init_guardrails()
    
    def _init_guardrails(self):
        """Initialize Guardrails for different response modes."""
        if not HAS_GUARDRAILS:
            print("[WARNING] Guardrails not installed. Install with: pip install guardrails-ai")
            return {}
        
        try:
            guards = {}
            
            # Concise mode: Full validation (user-friendly responses)
            guards["concise"] = Guard.from_string(
                validators=[
                    hallucination_check(),
                    security_incident_policy()
                ],
                description="Ensure the solution is accurate, safe, and policy-compliant (user-friendly)."
            )
            
            # Internal mode: Hallucination check only (system integration)
            guards["internal"] = Guard.from_string(
                validators=[
                    hallucination_check()
                ],
                description="Only check for hallucinations in system integration mode."
            )
            
            # Verbose mode: No guardrails (full metadata for engineers)
            guards["verbose"] = None
            
            print("[✓] Guardrails initialized for response modes: concise, internal, verbose")
            return guards
            
        except Exception as e:
            print(f"[WARNING] Failed to initialize Guardrails: {e}")
            return {}

    def _init_services(self):
        """Initialize services using environment configuration."""
        # Get configuration paths from EnvConfig
        rag_config_path = EnvConfig.get_rag_config_path()
        llm_config_path = os.getenv("LLM_CONFIG_PATH", os.path.join(rag_config_path, "llm_config.json"))
        
        try:
            with open(llm_config_path, "r") as f:
                llm_config = json.load(f)
        except FileNotFoundError:
            llm_config = {"default_provider": "ollama", "llm_providers": {}, "embedding_providers": {}}
        
        llm_service = LLMService(llm_config)
        
        # Use EnvConfig for VectorDB paths
        chroma_db_path = EnvConfig.get_chroma_db_path()
        vectordb_service = VectorDBService(
            persist_directory=chroma_db_path,
            collection_name=os.getenv("CHROMA_COLLECTION", "rag_embeddings")
        )
        
        return llm_service, vectordb_service

    def _init_rl_agent(self):
        """Initialize RL Healing Agent using environment configuration."""
        try:
            db_path = EnvConfig.get_db_path()
            return RLHealingAgent(db_path)
        except Exception as e:
            print(f"Warning: Failed to initialize RL agent: {e}")
            return None

    def _build_ingestion_graph(self):
        """Build ingestion workflow graph.
        
        INGESTION WORKFLOW STAGES:
        1. extract_metadata_node: Uses extract_metadata_tool with LLM to generate semantic metadata
        2. chunk_document_node: Uses chunk_document_tool to split text into semantic chunks
        3. save_vectordb_node: Uses save_to_vectordb_tool to:
           - Generate embeddings for each chunk using LLM
           - Store embeddings in VectorDB (ChromaDB)
           - Persist metadata to SQLite (if available)
        4. update_tracking_node: Uses update_metadata_tracking_tool to record audit trail
        
        INGESTION PATHS:
        - Single Document: ingest_document(text, doc_id)
        - Table Ingestion: ingest_sqlite_table_tool for database rows
        - Batch Folder: ingest_documents_from_path_tool discovers files, then loops through each
        """
        graph = StateGraph(dict)
        
        # Define nodes
        def extract_metadata_node(state):
            """
            INGESTION STAGE 1: Extract Semantic Metadata
            
            TOOL: extract_metadata_tool
            WHEN: First step in document ingestion pipeline
            INPUT: text (raw document content), llm_service (for LLM processing)
            PROCESS:
              1. Uses LLM to analyze document text
              2. Extracts: title, summary (2-3 sentences), keywords (5-10), topics, doc_type
              3. Returns structured JSON metadata
            OUTPUT: state["metadata"] with LLM-extracted fields
            FALLBACK: Returns basic metadata if LLM processing fails
            """
            try:
                meta_response = extract_metadata_tool.invoke({"text": state["text"], "llm_service": self.llm_service})
                state["metadata"] = json.loads(meta_response) if isinstance(meta_response, str) else meta_response
                state["status"] = "metadata_extracted"
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Metadata extraction failed: {e}"]
            return state

        def chunk_document_node(state):
            """
            INGESTION STAGE 2: Split Into Semantic Chunks
            
            TOOL: chunk_document_tool
            WHEN: After metadata extraction
            INPUT: text (document content), doc_id (unique identifier)
            PROCESS:
              1. Uses RecursiveCharacterTextSplitter with Markdown-aware separators
              2. Default: chunk_size=500 chars, overlap=50 chars
              3. Splits on: \\n\\n##, \\n\\n, \\n, ". ", " ", ""
            OUTPUT: state["chunks"] with num_chunks and list of chunks
            PURPOSE: Create semantically coherent pieces for embedding
            """
            try:
                chunks_response = chunk_document_tool.invoke({"text": state["text"], "doc_id": state["doc_id"]})
                state["chunks"] = json.loads(chunks_response) if isinstance(chunks_response, str) else chunks_response
                state["status"] = "chunks_created"
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Chunking failed: {e}"]
            return state

        def save_vectordb_node(state):
            """
            INGESTION STAGE 3: Generate Embeddings & Store in VectorDB
            
            TOOL: save_to_vectordb_tool
            WHEN: After chunking
            INPUT: chunks (from chunk_document_tool), doc_id, services, metadata
            PROCESS:
              1. For each chunk:
                 a. Generates embedding using LLM's embedding model
                 b. Creates chunk_id = {doc_id}_chunk_{index}
              2. Batch adds to ChromaDB vector store:
                 - chunk_ids, embeddings, text, metadatas
              3. Optionally persists to SQLite (DocumentMetadataModel, ChunkEmbeddingDataModel)
            OUTPUT: state["save_result"] with chunks_saved count
            PURPOSE: Make documents searchable via semantic similarity
            """
            try:
                meta_json = json.dumps(state.get("metadata", {}).get("metadata", {}))
                save_response = save_to_vectordb_tool.invoke({
                    "chunks": json.dumps(state["chunks"]),
                    "doc_id": state["doc_id"],
                    "llm_service": self.llm_service,
                    "vectordb_service": self.vectordb_service,
                    "metadata": meta_json
                })
                state["save_result"] = json.loads(save_response) if isinstance(save_response, str) else save_response
                state["status"] = "saved_to_vectordb"
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"VectorDB save failed: {e}"]
            return state

        def update_tracking_node(state):
            """
            INGESTION STAGE 4: Record Audit Trail & Finalize
            
            TOOL: update_metadata_tracking_tool
            WHEN: After VectorDB persistence
            INPUT: doc_id, source_path, rbac_namespace, metadata, chunks_saved
            PROCESS:
              1. Updates DocumentTrackingModel in SQLite (if available)
              2. Records ingestion audit trail with timestamp
              3. Marks ingestion_status = 'COMPLETED'
              4. Stores metadata_tags as JSON for later querying
            OUTPUT: state["tracking_result"] with success status
            PURPOSE: Create immutable audit trail for compliance & debugging
            """
            try:
                meta_json = json.dumps(state.get("metadata", {}).get("metadata", {}))
                chunks_saved = state.get("save_result", {}).get("chunks_saved", 0)
                update_response = update_metadata_tracking_tool.invoke({
                    "doc_id": state["doc_id"],
                    "source_path": "document_ingestion",
                    "rbac_namespace": "general",
                    "metadata": meta_json,
                    "chunks_saved": chunks_saved
                })
                state["tracking_result"] = json.loads(update_response) if isinstance(update_response, str) else update_response
                state["status"] = "completed"
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Tracking update failed: {e}"]
            return state

        # Add nodes to graph
        graph.add_node("extract_metadata", extract_metadata_node)
        graph.add_node("chunk_document", chunk_document_node)
        graph.add_node("save_vectordb", save_vectordb_node)
        graph.add_node("update_tracking", update_tracking_node)

        # Add edges
        graph.add_edge(START, "extract_metadata")
        graph.add_edge("extract_metadata", "chunk_document")
        graph.add_edge("chunk_document", "save_vectordb")
        graph.add_edge("save_vectordb", "update_tracking")
        graph.add_edge("update_tracking", END)

        return graph.compile()

    def _build_retrieval_graph(self):
        """Build retrieval workflow graph with intelligent healing integration.
        
        RETRIEVAL WORKFLOW STAGES:
        1. retrieve_context_node: Uses retrieve_context_tool to get top-k relevant docs
        2. rerank_context_node: Uses rerank_context_tool to sort by relevance
        3. check_optimization: Decides if optimization needed (RL or heuristic)
        4. optimize_context: Uses get_context_cost_tool + optimize_chunk_size_tool
        5. answer_question_node: Uses answer_question_tool to generate answer
        6. traceability_node: Uses traceability_tool for audit trail
        
        RESPONSE MODES:
        - concise: User-friendly, applies hallucination_check + security_incident_policy guardrails
        - internal: System integration, applies hallucination_check guardrails only
        - verbose: Engineering view, no guardrails, shows all debug info
        """
        graph = StateGraph(dict)

        def retrieve_context_node(state):
            try:
                response_mode = state.get("response_mode", "concise")
                show_debug = response_mode in ["verbose", "internal"]
                
                if show_debug:
                    print(f"\n[🔍 RETRIEVE CONTEXT NODE - {response_mode.upper()} MODE]")
                    print(f"  Question: {state['question'][:80]}...")
                    print(f"  Retrieving top-k=5 relevant documents...")
                
                # TOOL: retrieve_context_tool
                # WHEN: Question answering starts - need to find relevant documents
                # INPUT: question (user query), k=5 (top results), services (LLM for embedding, VectorDB for search)
                # PROCESS: 
                #   1. Generates embedding for the question
                #   2. Performs semantic similarity search in VectorDB
                #   3. Returns top-5 most similar chunks with similarity scores
                context_response = retrieve_context_tool.invoke({
                    "question": state["question"],
                    "llm_service": self.llm_service,
                    "vectordb_service": self.vectordb_service,
                    "k": 5
                })
                state["context"] = json.loads(context_response) if isinstance(context_response, str) else context_response
                state["status"] = "context_retrieved"
                state["retrieval_quality"] = len(state["context"].get("context", [])) / 5.0  # Normalize to 0-1
                
                if show_debug:
                    ctx_items = state["context"].get("context", [])
                    print(f"  ✓ Retrieved {len(ctx_items)} documents (quality score: {state['retrieval_quality']:.2f})")
                    if response_mode == "verbose":
                        for i, ctx in enumerate(ctx_items[:3], 1):
                            doc_id = ctx.get("metadata", {}).get("doc_id", "unknown")
                            text_preview = ctx.get("text", "")[:60]
                            print(f"    [{i}] Doc: {doc_id} | {text_preview}...")
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Context retrieval failed: {e}"]
                state["retrieval_quality"] = 0.0
                if show_debug:
                    print(f"  ✗ Error: {e}")
            return state

        def rerank_context_node(state):
            try:
                response_mode = state.get("response_mode", "concise")
                show_debug = response_mode in ["verbose", "internal"]
                
                if show_debug:
                    print(f"\n[📊 RERANK CONTEXT NODE - {response_mode.upper()} MODE]")
                    initial_count = len(state.get("context", {}).get("context", []))
                    print(f"  Reranking {initial_count} documents for relevance...")
                
                # TOOL: rerank_context_tool
                # WHEN: After initial retrieval - need to improve result ordering
                # INPUT: context (raw retrieved chunks from retrieve_context_tool), llm_service
                # PROCESS:
                #   1. Uses LLM to re-evaluate relevance of each chunk
                #   2. Reorders results by relevance score (highest first)
                #   3. Filters out low-confidence matches
                reranked_response = rerank_context_tool.invoke({
                    "context": json.dumps(state.get("context", {})),
                    "llm_service": self.llm_service
                })
                state["reranked_context"] = json.loads(reranked_response) if isinstance(reranked_response, str) else reranked_response
                state["status"] = "context_reranked"
                
                if show_debug:
                    reranked_items = state["reranked_context"].get("reranked_context", [])
                    print(f"  ✓ Reranked to {len(reranked_items)} documents (sorted by relevance)")
                    if response_mode == "verbose":
                        for i, item in enumerate(reranked_items[:3], 1):
                            relevance_score = item.get("metadata", {}).get("relevance_score", "N/A")
                            doc_id = item.get("metadata", {}).get("doc_id", "unknown")
                            print(f"    [{i}] Score: {relevance_score} | Doc: {doc_id}")
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Context reranking failed: {e}"]
                if show_debug:
                    print(f"  ✗ Error: {e}")
            return state

        def check_optimization_needed(state):
            """Intelligent decision node using RL agent to check if healing/optimization is needed."""
            reranked = state.get("reranked_context", {}).get("reranked_context", [])
            num_results = len(reranked)
            
            # Calculate retrieval quality
            quality = min(1.0, num_results / 5)  # Normalized quality (5 is optimal)
            state["retrieval_quality"] = quality
            
            # Use RL agent for intelligent decision
            if self.rl_healing_agent and state.get("doc_id"):
                try:
                    recommendation = self.rl_healing_agent.recommend_healing(
                        doc_id=state.get("doc_id", "unknown"),
                        current_quality=quality
                    )
                    state["rl_recommendation"] = recommendation
                    
                    # Extract decision
                    should_optimize = recommendation['recommended_action'] != 'SKIP'
                    state["should_optimize"] = should_optimize
                    state["optimization_reason"] = recommendation['reasoning']
                    state["rl_action"] = recommendation['recommended_action']
                    
                except Exception as e:
                    # Fallback to simple heuristic if RL fails
                    should_optimize = quality < 0.6 or num_results < 3
                    state["should_optimize"] = should_optimize
                    state["optimization_reason"] = f"Quality={quality:.2f}, Results={num_results}"
                    print(f"Warning: RL agent failed: {e}")
            else:
                # Simple heuristic when RL agent not available
                should_optimize = quality < 0.6 or num_results < 3
                state["should_optimize"] = should_optimize
                state["optimization_reason"] = f"Quality={quality:.2f}, Results={num_results}"
            
            return state

        def optimize_context_node(state):
            """Apply healing/optimization to improve context quality and reduce tokens."""
            try:
                # Get cost estimate
                reranked = state.get("reranked_context", {}).get("reranked_context", [])
                context_list = [{"text": c.get("text", ""), "source": f"Doc {c.get('metadata', {}).get('doc_id', 'N/A')}"} 
                               for c in reranked]
                
                cost_response = get_context_cost_tool.invoke({
                    "context": context_list,
                    "llm_service": self.llm_service,
                    "model_name": "ollama"
                })
                cost_data = json.loads(cost_response) if isinstance(cost_response, str) else cost_response
                
                # Get optimization suggestions
                perf_history = state.get("performance_history", [])
                if not perf_history:
                    perf_history = [{"params": {"k": 5, "chunk_size": 512}, "metrics": {"cost": float(cost_data.get("estimated_cost_usd", 0))}}]
                
                optimize_response = optimize_chunk_size_tool.invoke({
                    "performance_history": perf_history,
                    "llm_service": self.llm_service
                })
                optimize_data = json.loads(optimize_response) if isinstance(optimize_response, str) else optimize_response
                
                state["optimization_result"] = {
                    "cost_analysis": cost_data,
                    "suggested_params": optimize_data.get("suggested_params", {}),
                    "tokens_before": cost_data.get("total_tokens", 0)
                }
                state["status"] = "optimized"
                
                # Log healing action if RL agent made a recommendation
                try:
                    if state.get("should_optimize") and state.get("rl_action") and state.get("rl_action") != "SKIP":
                        from ....database.models.rag_history_model import RAGHistoryModel
                        
                        print(f"[DEBUG] Logging healing action: should_optimize={state.get('should_optimize')}, rl_action={state.get('rl_action')}")
                        
                        action_taken = state.get("rl_action", "OPTIMIZE")
                        metrics = {
                            "strategy": action_taken,
                            "before_metrics": {"avg_quality": state.get("retrieval_quality", 0.0), "total_chunks": len(reranked)},
                            "after_metrics": {"avg_quality": min(1.0, state.get("retrieval_quality", 0.0) + 0.15)},
                            "improvement_delta": 0.15,  # Estimated
                            "cost_tokens": cost_data.get("total_tokens", 0),
                            "duration_ms": 0
                        }
                        
                        print(f"[DEBUG] Instantiating RAGHistoryModel for healing...")
                        rag_history = RAGHistoryModel()
                        print(f"[DEBUG] RAGHistoryModel connected to: {rag_history.db_path}")
                        
                        # Get doc_id from state or context
                        doc_id_to_log = state.get("doc_id")
                        print(f"[DEBUG] doc_id from state: {doc_id_to_log}")
                        
                        if not doc_id_to_log:
                            reranked = state.get("reranked_context", {}).get("reranked_context", [])
                            if reranked and len(reranked) > 0:
                                doc_id_to_log = reranked[0].get("metadata", {}).get("doc_id") or reranked[0].get("source", "unknown")
                                print(f"[DEBUG] doc_id extracted from context: {doc_id_to_log}")
                        
                        doc_id_to_log = doc_id_to_log or "unknown"
                        print(f"[DEBUG] Final doc_id_to_log: {doc_id_to_log}")
                        
                        healing_id = rag_history.log_healing(
                            target_doc_id=doc_id_to_log,
                            target_chunk_id=f"{state.get('doc_id', 'unknown')}_chunk_0",
                            metrics_json=json.dumps(metrics),
                            context_json=json.dumps({
                                "reason": state.get("optimization_reason", "quality_improvement"),
                                "alternatives_considered": ["SKIP", "REINDEX", "RE_EMBED"],
                                "expected_reward": state.get("rl_recommendation", {}).get("estimated_improvement", 0)
                            }),
                            action_taken=action_taken,
                            reward_signal=0.12,  # Estimated reward
                            agent_id="langgraph_agent",
                            session_id=state.get("session_id", "session_default")
                        )
                        
                        print(f"[DEBUG] Healing action logged successfully: healing_id={healing_id}, action={action_taken}")
                        state["healing_logged_id"] = healing_id
                        
                        # Verify it was written
                        rag_history.cursor.execute("SELECT COUNT(*) FROM rag_history_and_optimization WHERE event_type = 'HEAL'")
                        count = rag_history.cursor.fetchone()[0]
                        print(f"[DEBUG] Total HEAL events in database: {count}")
                        rag_history.close()
                        
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Failed to log healing action: {e}")
                    print(f"[TRACEBACK] {traceback.format_exc()}")
                    # Don't fail optimization if logging fails
                    
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Optimization analysis failed: {e}"]
                state["optimization_result"] = {"error": str(e)}
            return state

        def answer_question_node(state):
            try:
                response_mode = state.get("response_mode", "concise")
                show_debug = response_mode in ["verbose", "internal"]  # Show debug for verbose and internal modes
                
                if show_debug:
                    print(f"\n[📋 ANSWER GENERATION NODE - {response_mode.upper()} MODE]")
                    print(f"  Question: {state['question'][:80]}...")
                    print(f"  Response Mode: {response_mode}")
                    print(f"  Reranked Context Items: {len(state.get('reranked_context', {}).get('reranked_context', []))}")
                
                # TOOL: answer_question_tool
                # WHEN: After reranking - ready to synthesize final answer
                # INPUT: question (original user query), context (reranked chunks), llm_service
                # PROCESS:
                #   1. Uses LLM to synthesize coherent answer from context
                #   2. Formats answer based on response_mode
                #   3. Applies guardrails validation (concise/internal modes)
                # Generate answer using tool
                answer_response = answer_question_tool.invoke({
                    "question": state["question"],
                    "context": json.dumps(state.get("reranked_context", {})),
                    "llm_service": self.llm_service
                })
                state["answer"] = answer_response
                state["status"] = "answer_generated"
                
                if show_debug:
                    print(f"  ✓ Answer Generated ({len(str(answer_response).split())} words)")
                    if response_mode == "verbose":
                        print(f"  Answer Preview: {str(answer_response)[:150]}...")
                
                # Log query to database with metrics
                try:
                    from ....database.models.rag_history_model import RAGHistoryModel
                    
                    reranked = state.get("reranked_context", {}).get("reranked_context", [])
                    
                    if show_debug:
                        print(f"\n[📊 LOGGING QUERY TO DATABASE]")
                        print(f"  Reranked Sources: {len(reranked)}")
                    
                    metrics = {
                        "frequency": 1,
                        "avg_accuracy": state.get("retrieval_quality", 0.7),
                        "cost_tokens": len(state["question"].split()) * 10,  # Rough estimate
                        "latency_ms": 0,  # Would need timing
                        "user_feedback": 0.7,  # Default, will be updated by user
                        "quality_category": "warm" if state.get("retrieval_quality", 0) > 0.6 else "cold",
                        "sources_count": len(reranked),
                        "response_mode": response_mode
                    }
                    
                    rag_history = RAGHistoryModel()
                    if show_debug:
                        print(f"  Database Path: {rag_history.db_path}")
                    
                    # Get doc_id from context if not in state
                    doc_id_to_log = state.get("doc_id")
                    
                    if not doc_id_to_log and reranked and len(reranked) > 0:
                        # Extract from first retrieved document
                        doc_id_to_log = reranked[0].get("metadata", {}).get("doc_id") or reranked[0].get("source", "unknown")
                    
                    doc_id_to_log = doc_id_to_log or "unknown"
                    if show_debug:
                        print(f"  Target Doc ID: {doc_id_to_log}")
                    
                    query_id = rag_history.log_query(
                        query_text=state["question"],
                        target_doc_id=doc_id_to_log,
                        metrics_json=json.dumps(metrics),
                        context_json=json.dumps({
                            "retrieval_quality": state.get("retrieval_quality", 0.7),
                            "sources": len(reranked),
                            "answer_length": len(state["answer"].split()) if state["answer"] else 0,
                            "response_mode": response_mode
                        }),
                        agent_id="langgraph_agent",
                        session_id=state.get("session_id", "session_default")
                    )
                    
                    if show_debug:
                        print(f"  ✓ Query Logged: ID={query_id}")
                    
                    state["query_logged_id"] = query_id
                    
                    # Verify it was written
                    if response_mode == "verbose":
                        rag_history.cursor.execute("SELECT COUNT(*) FROM rag_history_and_optimization WHERE event_type = 'QUERY'")
                        count = rag_history.cursor.fetchone()[0]
                        print(f"  Database Total QUERY Events: {count}")
                    
                    rag_history.close()
                    
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Failed to log query: {e}")
                    if response_mode == "verbose":
                        print(f"[TRACEBACK] {traceback.format_exc()}")
                    # Don't fail the answer generation if logging fails
                    
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Answer generation failed: {e}"]
                state["answer"] = "Failed to generate answer"
                if show_debug:
                    print(f"  ✗ Error: {e}")
            
            return state

        def traceability_node(state):
            try:
                trace_response = traceability_tool.invoke({
                    "question": state["question"],
                    "context": json.dumps(state.get("reranked_context", {})),
                    "vectordb_service": self.vectordb_service
                })
                state["traceability"] = json.loads(trace_response) if isinstance(trace_response, str) else trace_response
                state["status"] = "completed"
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Traceability generation failed: {e}"]
            return state

        # Add nodes
        graph.add_node("retrieve_context", retrieve_context_node)
        graph.add_node("rerank_context", rerank_context_node)
        graph.add_node("check_optimization", check_optimization_needed)
        graph.add_node("optimize_context", optimize_context_node)
        graph.add_node("answer_question", answer_question_node)
        graph.add_node("traceability", traceability_node)

        # Add edges with conditional routing
        graph.add_edge(START, "retrieve_context")
        graph.add_edge("retrieve_context", "rerank_context")
        graph.add_edge("rerank_context", "check_optimization")
        
        # Conditional edge: if optimization needed, optimize; otherwise skip to answer
        def route_to_optimization(state):
            return "optimize_context" if state.get("should_optimize", False) else "answer_question"
        
        graph.add_conditional_edges("check_optimization", route_to_optimization, {
            "optimize_context": "optimize_context",
            "answer_question": "answer_question"
        })
        
        graph.add_edge("optimize_context", "answer_question")
        graph.add_edge("answer_question", "traceability")
        graph.add_edge("traceability", END)

        return graph.compile()

    def _build_optimization_graph(self):
        """Build optimization workflow graph."""
        graph = StateGraph(dict)

        def optimize_node(state):
            try:
                result = optimize_chunk_size_tool.invoke({
                    "performance_history": state["performance_history"],
                    "llm_service": self.llm_service
                })
                state["optimization_result"] = json.loads(result) if isinstance(result, str) else result
                state["status"] = "optimization_complete"
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Optimization failed: {e}"]
            return state

        def apply_config_node(state):
            try:
                # Pass config_service as None if not available
                result = adjust_config_tool.invoke({
                    "config_service": None,
                    "updates": state.get("config_updates", {})
                })
                state["config_result"] = json.loads(result) if isinstance(result, str) else result
                state["status"] = "completed"
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Config update failed: {e}"]
            return state

        # Add nodes
        graph.add_node("optimize", optimize_node)
        graph.add_node("apply_config", apply_config_node)

        # Add edges
        graph.add_edge(START, "optimize")
        graph.add_edge("optimize", "apply_config")
        graph.add_edge("apply_config", END)

        return graph.compile()

    def ingest_document(self, text: str, doc_id: str) -> Dict[str, Any]:
        """Ingest document using ingestion workflow."""
        initial_state = {
            "text": text,
            "doc_id": doc_id,
            "errors": [],
            "status": "started"
        }
        result = self.ingestion_graph.invoke(initial_state)
        return {
            "success": len(result.get("errors", [])) == 0,
            "doc_id": doc_id,
            "chunks_count": result.get("chunks", {}).get("num_chunks", 0),
            "chunks_saved": result.get("save_result", {}).get("chunks_saved", 0),
            "metadata": result.get("metadata", {}),
            "errors": result.get("errors", [])
        }

    def _apply_guardrails_validation(self, answer: str, response_mode: str) -> Dict[str, Any]:
        """Apply Guardrails validation based on response mode."""
        if not HAS_GUARDRAILS or response_mode == "verbose" or not self.guardrails.get(response_mode):
            return {
                "validated": True,
                "guardrails_applied": False,
                "answer": answer
            }
        
        try:
            guard = self.guardrails.get(response_mode)
            if not guard:
                return {
                    "validated": True,
                    "guardrails_applied": False,
                    "answer": answer
                }
            
            # Apply guard validation
            validated_response = guard.validate(answer)
            
            return {
                "validated": True,
                "guardrails_applied": True,
                "answer": str(validated_response),
                "validation_mode": response_mode
            }
        except Exception as e:
            print(f"[WARNING] Guardrails validation failed: {e}")
            # Return original answer if validation fails
            return {
                "validated": False,
                "guardrails_applied": False,
                "answer": answer,
                "validation_error": str(e)
            }

    def ask_question(self, question: str, performance_history: List[Dict[str, Any]] = None, doc_id: str = None, response_mode: str = "concise") -> Dict[str, Any]:
        """Answer question using intelligent retrieval workflow with RL healing agent.
        
        Args:
            question: User question
            performance_history: Historical performance data
            doc_id: Optional document ID to query
            response_mode: Response format:
                - "concise": End-user friendly (answer only)
                - "verbose": Engineer/RAG Admin (all metadata, traceability, RL info)
                - "internal": System/Integration (answer + structured data for updating tables)
            
        Returns:
            Response dict with answer and metadata based on response_mode
        """
        import uuid
        session_id = str(uuid.uuid4())  # Generate session ID for tracking
        
        # Create visualization tracker
        viz = create_visualization(session_id)
        start_time = time.time()
        
        initial_state = {
            "question": question,
            "doc_id": doc_id,
            "session_id": session_id,
            "response_mode": response_mode,
            "performance_history": performance_history or [],
            "errors": [],
            "status": "started"
        }
        
        # Track workflow execution
        viz.record_node_start("retrieve_and_answer_workflow", initial_state)
        
        try:
            result = self.retrieval_graph.invoke(initial_state)
            
            # Track successful completion
            result["execution_time_ms"] = (time.time() - start_time) * 1000
            viz.record_node_end("retrieve_and_answer_workflow", result)
            result["visualization"] = viz.get_trace_data()
            
        except Exception as e:
            viz.record_error("retrieve_and_answer_workflow", str(e))
            result = {"errors": [str(e)]}
        
        # Save visualization to logs and session_graph (suppress output in concise mode)
        try:
            import sys
            from io import StringIO
            
            if response_mode == "concise":
                # Suppress stdout during visualization save for concise mode
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                try:
                    viz_files = save_visualization(viz, output_dir="logs", graph=self.retrieval_graph)
                finally:
                    sys.stdout = old_stdout
            else:
                viz_files = save_visualization(viz, output_dir="logs", graph=self.retrieval_graph)
                print(f"[✓] Session visualization saved: {viz_files}")
        except Exception as e:
            print(f"[!] Failed to save visualization: {e}")
            import traceback
            traceback.print_exc()
        
        # Build response based on mode
        if response_mode == "concise":
            # End-user friendly: just answer, no metadata
            answer_text = result.get("answer", "")
            
            # Extract plain text answer (remove JSON wrapping if present)
            try:
                if isinstance(answer_text, str) and answer_text.strip().startswith("{"):
                    import json
                    parsed = json.loads(answer_text)
                    answer_text = parsed.get("answer", answer_text)
            except:
                pass  # Use raw answer if not JSON
            
            # Apply Guardrails validation for concise mode (hallucination_check + security_incident_policy)
            validation_result = self._apply_guardrails_validation(answer_text, response_mode)
            if not validation_result.get("validated"):
                print(f"[⚠] Guardrails validation warning: {validation_result.get('validation_error')}")
            validated_answer = validation_result.get("answer", answer_text)
            
            return {
                "success": len(result.get("errors", [])) == 0,
                "question": question,
                "answer": validated_answer,
                "session_id": session_id,
                "guardrails_applied": validation_result.get("guardrails_applied", False),
                "errors": result.get("errors", [])
            }
        elif response_mode == "internal":
            # System/Integration: clean answer text + structured metadata for database updates (no approval needed)
            reranked = result.get("reranked_context", {}).get("reranked_context", [])
            
            # Extract plain text answer (remove JSON wrapping if present)
            answer_text = result.get("answer", "")
            try:
                # Try to parse JSON answer and extract the text
                if isinstance(answer_text, str) and answer_text.strip().startswith("{"):
                    import json
                    parsed = json.loads(answer_text)
                    answer_text = parsed.get("answer", answer_text)
            except:
                pass  # Use raw answer if not JSON
            
            # Apply Guardrails validation for internal mode (hallucination_check only)
            validation_result = self._apply_guardrails_validation(answer_text, response_mode)
            if not validation_result.get("validated"):
                print(f"[⚠] Guardrails validation warning: {validation_result.get('validation_error')}")
            validated_answer = validation_result.get("answer", answer_text)
            
            return {
                "success": len(result.get("errors", [])) == 0,
                "answer": validated_answer,  # Plain text only
                "quality_score": result.get("retrieval_quality", 0.0),
                "sources_count": len(reranked),
                "source_docs": [{"doc_id": s.get("metadata", {}).get("doc_id") or s.get("source", "unknown"), 
                                "chunk_id": s.get("metadata", {}).get("chunk_id")} for s in reranked],
                "metadata": {
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "model": "langgraph_rag_agent",
                    "execution_time_ms": result.get("execution_time_ms", 0)
                },
                "guardrails_applied": validation_result.get("guardrails_applied", False),
                "errors": result.get("errors", [])
            }
        else:  # verbose mode (default for engineers/admins)
            # Full business intelligence: all metadata, traceability, RL info
            # NOTE: No guardrails for verbose mode - engineers need raw data for debugging
            reranked = result.get("reranked_context", {}).get("reranked_context", [])
            return {
                "success": len(result.get("errors", [])) == 0,
                "question": question,
                "answer": result.get("answer", ""),
                "sources": reranked,
                "sources_count": len(reranked),
                "traceability": result.get("traceability", {}),
                "retrieval_quality": result.get("retrieval_quality", 0.0),
                "optimization_applied": result.get("should_optimize", False),
                "optimization_reason": result.get("optimization_reason", ""),
                "rl_action": result.get("rl_action", "SKIP"),
                "rl_recommendation": {
                    "action": result.get("rl_info", {}).get("recommended_action", "N/A"),
                    "confidence": result.get("rl_info", {}).get("confidence", 0),
                    "expected_improvement": result.get("rl_info", {}).get("expected_improvement", 0),
                    "learning_stats": result.get("rl_info", {}).get("learning_stats", {})
                },
                "optimization_result": result.get("optimization_result", {}),
                "execution_time_ms": result.get("execution_time_ms", 0),
                "session_id": session_id,
                "visualization_data": result.get("visualization", {}),
                "guardrails_applied": False,
                "errors": result.get("errors", [])
            }

    def optimize_system(self, performance_history: List[Dict[str, Any]], config_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize system using optimization workflow."""
        initial_state = {
            "performance_history": performance_history,
            "config_updates": config_updates,
            "errors": [],
            "status": "started"
        }
        result = self.optimization_graph.invoke(initial_state)
        return {
            "success": len(result.get("errors", [])) == 0,
            "optimization": result.get("optimization_result", {}),
            "config_applied": result.get("config_result", {}),
            "errors": result.get("errors", [])
        }

    def invoke_chat(self, response_mode: str = "concise", show_history: bool = True) -> Dict[str, Any]:
        """
        Interactive chat mode with human feedback loop.
        
        CHAT WORKFLOW:
        1. Get user question
        2. Process through RAG agent with specified response_mode
        3. Display answer
        4. Ask for satisfaction feedback
        5. If satisfied -> ask new question, else -> try different approach
        6. Continue until user quits or satisfied
        
        Args:
            response_mode (str): "concise" (user), "internal" (system), "verbose" (engineer)
            show_history (bool): Show conversation history at end
        
        Returns:
            Dict with conversation_history, message_count, session_stats
        """
        from datetime import datetime
        import sys
        from io import StringIO
        
        print("\n" + "="*70)
        print("LANGGRAPH AGENT - INTERACTIVE CHAT MODE")
        print(f"Response Mode: {response_mode.upper()}")
        print("="*70 + "\n")
        
        conversation_history = []
        message_count = 0
        
        while True:
            # Get user question
            try:
                question = input("Ask a question (or 'quit' to exit): ").strip()
            except EOFError:
                question = "quit"
            
            if question.lower() in ['quit', 'exit', 'q']:
                break
            
            if not question:
                print("[ERROR] Please enter a valid question\n")
                continue
            
            # Process question
            print("\n[PROCESSING] Searching knowledge base...")
            try:
                # Suppress debug output
                old_stdout = sys.stdout
                sys.stdout = StringIO()
                
                response = self.ask_question(
                    question=question,
                    response_mode=response_mode
                )
                
                sys.stdout = old_stdout
            except Exception as e:
                sys.stdout = old_stdout
                print(f"[ERROR] Query failed: {e}\n")
                continue
            
            if not response.get("success"):
                print(f"[ERROR] {response.get('errors', 'Unknown error')}\n")
                continue
            
            # Display answer
            answer = response.get("answer", "No answer available")
            print(f"\nQ: {question}")
            print("-" * 70)
            print(f"A: {answer}\n")
            print("-" * 70)
            
            # Add to history
            conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "answer": answer,
                "response_mode": response_mode
            })
            message_count += 1
            
            # Ask for satisfaction
            while True:
                try:
                    feedback = input("\nSatisfied? (yes/no/followup): ").strip().lower()
                except EOFError:
                    feedback = "yes"
                
                if feedback in ['yes', 'y']:
                    print("[OK] Great! Ask another question or type 'quit' to exit.\n")
                    break
                elif feedback in ['no', 'n']:
                    print("[NOTE] Searching for alternative answers...\n")
                    # Retry with verbose mode for more details
                    try:
                        old_stdout = sys.stdout
                        sys.stdout = StringIO()
                        
                        response = self.ask_question(
                            question=question,
                            response_mode="verbose"
                        )
                        
                        sys.stdout = old_stdout
                    except Exception as e:
                        sys.stdout = old_stdout
                        print(f"[ERROR] Retry failed: {e}\n")
                        break
                    
                    answer = response.get("answer", "No answer available")
                    print(f"A (with more details): {answer}\n")
                    print("-" * 70)
                    break
                elif feedback in ['followup', 'f']:
                    print("[OK] Ask your follow-up question:\n")
                    break
                else:
                    print("[ERROR] Please enter: yes, no, or followup\n")
        
        # Session summary
        print("\n" + "="*70)
        print("SESSION SUMMARY")
        print("="*70)
        print(f"Total Questions: {message_count}")
        print(f"Response Mode: {response_mode}")
        
        if show_history and conversation_history:
            print("\nConversation History:")
            for i, entry in enumerate(conversation_history, 1):
                print(f"  {i}. Q: {entry['question'][:60]}...")
                print(f"     A: {entry['answer'][:80]}...")
        
        print("="*70 + "\n")
        
        # Save session
        import json
        import os
        history_dir = "data/chat_history"
        os.makedirs(history_dir, exist_ok=True)
        session_file = f"{history_dir}/chat_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        session_data = {
            "timestamp": datetime.now().isoformat(),
            "response_mode": response_mode,
            "message_count": message_count,
            "conversation_history": conversation_history
        }
        
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2, default=str)
        
        print(f"[OK] Session saved to: {session_file}\n")
        
        return {
            "success": True,
            "message_count": message_count,
            "conversation_history": conversation_history,
            "session_file": session_file
        }

    def invoke(self, operation: str, **kwargs) -> Dict[str, Any]:
        if operation == "ingest_document":
            return self.ingest_document(
                text=kwargs.get("text", ""),
                doc_id=kwargs.get("doc_id", "doc_default")
            )
        
        elif operation == "ingest_sqlite_table":
            config_path = Path(__file__).parent.parent.parent / "config" / "data_sources.json"
            
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            table_name = kwargs.get("table_name", "knowledge_base")
            sqlite_config = config.get("data_sources", {}).get("sqlite", {})
            tables_config = sqlite_config.get("ingestion_modes", {}).get("table_based", {}).get("tables_to_ingest", [])
            
            table_config = next((t for t in tables_config if t.get("name") == table_name), {})
            
            text_columns = kwargs.get("text_columns", table_config.get("text_columns", []))
            metadata_columns = kwargs.get("metadata_columns", table_config.get("metadata_columns", []))
            chunking_config = sqlite_config.get("chunking", {})
            
            result_json = ingest_sqlite_table_tool.invoke({
                "table_name": table_name,
                "doc_id": kwargs.get("doc_id", f"sqlite_{table_name}"),
                "rbac_namespace": kwargs.get("rbac_namespace", "general"),
                "text_columns": text_columns,
                "metadata_columns": metadata_columns,
                "db_path": EnvConfig.get_db_path(),
                "llm_service": self.llm_service,
                "vectordb_service": self.vectordb_service,
                "chunk_size": kwargs.get("chunk_size", chunking_config.get("chunk_size", 512)),
                "chunk_overlap": kwargs.get("chunk_overlap", chunking_config.get("overlap", 50))
            })
            
            return json.loads(result_json) if isinstance(result_json, str) else result_json
        
        elif operation == "ingest_from_path":
            # Ingest documents from file path or folder recursively
            # Calls ingest_documents_from_path_tool which returns discovered docs with generated doc_ids
            path = kwargs.get("path", "")
            doc_id_prefix = kwargs.get("doc_id_prefix", "doc")
            file_type = kwargs.get("file_type", "auto")  # auto, pdf, text, word
            recursive = kwargs.get("recursive", True)
            
            if not path:
                return {
                    "success": False,
                    "error": "path parameter required for ingest_from_path operation",
                    "documents_ingested": 0,
                    "errors": []
                }
            
            try:
                # Discover documents from path using the ingest_documents_from_path_tool
                discovery_result = ingest_documents_from_path_tool.invoke({
                    "path": path,
                    "doc_id_prefix": doc_id_prefix,
                    "file_type": file_type,
                    "recursive": recursive
                })
                
                discovery_data = json.loads(discovery_result) if isinstance(discovery_result, str) else discovery_result
                
                discovered_docs = discovery_data.get("discovered_documents", [])
                ingestion_errors = []
                ingestion_count = 0
                
                # Ingest each discovered document
                for doc in discovered_docs:
                    try:
                        doc_text = doc.get("text", "")
                        doc_id = doc.get("doc_id", f"{doc_id_prefix}_{ingestion_count}")
                        
                        # Call ingest_document to process each document
                        ingest_result = self.ingest_document(
                            text=doc_text,
                            doc_id=doc_id
                        )
                        
                        if ingest_result.get("success"):
                            ingestion_count += 1
                        else:
                            ingestion_errors.append({
                                "doc_id": doc_id,
                                "error": ingest_result.get("errors", ["Unknown error"])
                            })
                    except Exception as e:
                        ingestion_errors.append({
                            "doc_id": doc.get("doc_id", f"{doc_id_prefix}_{ingestion_count}"),
                            "error": str(e)
                        })
                
                return {
                    "success": len(ingestion_errors) == 0,
                    "documents_discovered": len(discovered_docs),
                    "documents_ingested": ingestion_count,
                    "documents_failed": len(ingestion_errors),
                    "errors": ingestion_errors,
                    "ingestion_details": {
                        "path": path,
                        "recursive": recursive,
                        "file_type": file_type,
                        "doc_id_prefix": doc_id_prefix
                    }
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "documents_ingested": 0,
                    "errors": [str(e)]
                }
        
        elif operation == "ask_question":
            return self.ask_question(
                question=kwargs.get("question", ""),
                performance_history=kwargs.get("performance_history"),
                doc_id=kwargs.get("doc_id"),
                response_mode=kwargs.get("response_mode", "concise")
            )
        
        elif operation == "optimize":
            return self.optimize_system(
                performance_history=kwargs.get("performance_history", []),
                config_updates=kwargs.get("config_updates", {})
            )
        
        elif operation == "chat":
            # Interactive chat mode with human feedback loop
            return self.invoke_chat(
                response_mode=kwargs.get("response_mode", "concise"),
                show_history=kwargs.get("show_history", True)
            )
        
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}. Available: ingest_document, ingest_sqlite_table, ingest_from_path, ask_question, optimize, chat"
            }


# ============================================================================
# CLI ENTRY POINT - Direct command-line invocation
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="LangGraph RAG Agent - Interactive Chat & Query Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
USAGE EXAMPLES:
  # Interactive chat mode (concise)
  python -m incident_iq.rag.agents.langgraph_agent --chat
  
  # Chat with verbose mode (full debug details)
  python -m incident_iq.rag.agents.langgraph_agent --chat --verbose
  
  # Ask single question (concise)
  python -m incident_iq.rag.agents.langgraph_agent --ask "What are main incident causes?"
  
  # Ask single question (verbose)
  python -m incident_iq.rag.agents.langgraph_agent --ask "What are main incident causes?" --verbose
  
  # Ingest knowledge_base table
  python -m incident_iq.rag.agents.langgraph_agent --ingest-table knowledge_base
  
RESPONSE MODES:
  --concise    User-friendly, with policy validation (default)
  --internal   System integration, structured data
  --verbose    Full debug details for engineers
        """
    )
    
    # Operation modes
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--chat",
        action="store_true",
        help="Start interactive chat mode with human feedback loop"
    )
    group.add_argument(
        "--ask",
        type=str,
        metavar="QUESTION",
        help="Ask a single question and exit"
    )
    group.add_argument(
        "--ingest-table",
        type=str,
        metavar="TABLE_NAME",
        help="Ingest SQLite table (default: knowledge_base)"
    )
    group.add_argument(
        "--ingest-path",
        type=str,
        metavar="PATH",
        help="Ingest documents from file path (PDF, TXT, DOCX)"
    )
    
    # Response mode
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--concise",
        action="store_const",
        const="concise",
        dest="mode",
        help="User-friendly, concise mode (default)"
    )
    mode_group.add_argument(
        "--internal",
        action="store_const",
        const="internal",
        dest="mode",
        help="System integration mode, structured data"
    )
    mode_group.add_argument(
        "--verbose",
        action="store_const",
        const="verbose",
        dest="mode",
        help="Full debug mode for engineers"
    )
    
    # Options
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Don't show conversation history at end (chat mode only)"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Recursively ingest from subdirectories (ingest-path only)"
    )
    
    args = parser.parse_args()
    
    # Default mode
    mode = args.mode or "concise"
    
    try:
        print(f"\n[INIT] Initializing LangGraph RAG Agent...")
        agent = LangGraphRAGAgent()
        print(f"[OK] Agent ready\n")
        
        if args.chat:
            # Interactive chat mode
            result = agent.invoke(
                operation="chat",
                response_mode=mode,
                show_history=not args.no_history
            )
            print(f"[OK] Chat completed: {result['message_count']} questions")
            
        elif args.ask:
            # Single question
            print(f"[QUERY] {args.ask}\n")
            result = agent.invoke(
                operation="ask_question",
                question=args.ask,
                response_mode=mode
            )
            
            if result.get("success"):
                print(f"[ANSWER]\n{result.get('answer', 'No answer')}\n")
            else:
                print(f"[ERROR] {result.get('errors', 'Unknown error')}\n")
            
        elif args.ingest_table:
            # Ingest SQLite table
            table_name = args.ingest_table
            print(f"[INGEST] Starting table ingestion: {table_name}\n")
            
            result = agent.invoke(
                operation="ingest_sqlite_table",
                table_name=table_name,
                doc_id=f"sqlite_{table_name}",
                rbac_namespace="general"
            )
            
            if result.get("success"):
                print(f"[OK] Successfully ingested {table_name}")
                print(f"    Records: {result.get('records_processed', 0)}")
                print(f"    Chunks: {result.get('total_chunks_saved', 0)}\n")
            else:
                print(f"[ERROR] {result.get('error', 'Ingestion failed')}\n")
                
        elif args.ingest_path:
            # Ingest from file path
            path = args.ingest_path
            print(f"[INGEST] Starting path ingestion: {path}\n")
            
            result = agent.invoke(
                operation="ingest_from_path",
                path=path,
                recursive=args.recursive,
                file_type="auto"
            )
            
            if result.get("success"):
                print(f"[OK] Successfully ingested from {path}")
                print(f"    Documents: {result.get('documents_ingested', 0)}")
                print(f"    Failed: {result.get('documents_failed', 0)}\n")
            else:
                print(f"[ERROR] {result.get('error', 'Ingestion failed')}\n")
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n[OK] Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
