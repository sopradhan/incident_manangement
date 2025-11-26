"""
LangGraph-based Agentic RAG System

Uses LangGraph for proper workflow orchestration with nodes and edges.
- Ingestion workflow
- Retrieval workflow with traceability
- Optimization workflow
"""
import os
import json
import time
from typing import Any, Dict, List, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Import visualization
from ...visualization.langgraph_visualizer import create_visualization, save_visualization

# Import RAG tools
from ...tools.ingestion_tools import (
    extract_metadata_tool,
    chunk_document_tool,
    save_to_vectordb_tool,
    update_metadata_tracking_tool,
    ingest_sqlite_table_tool,
    record_agent_memory_tool,
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
from ...agent.autonomous_rag_agent import ConfigService
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
        self.llm_service, self.vectordb_service, self.config_service = self._init_services()
        self.rl_healing_agent = self._init_rl_agent()
        self.ingestion_graph = self._build_ingestion_graph()
        self.retrieval_graph = self._build_retrieval_graph()
        self.optimization_graph = self._build_optimization_graph()

    def _init_services(self):
        """Initialize services."""
        config_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config")
        llm_config_path = os.getenv("LLM_CONFIG_PATH", os.path.join(config_dir, "llm_config.json"))
        
        try:
            with open(llm_config_path, "r") as f:
                llm_config = json.load(f)
        except FileNotFoundError:
            llm_config = {"default_provider": "ollama", "llm_providers": {}, "embedding_providers": {}}
        
        llm_service = LLMService(llm_config)
        vectordb_service = VectorDBService(
            persist_directory=os.getenv("CHROMA_DB_PATH", "./chroma_db"),
            collection_name=os.getenv("CHROMA_COLLECTION", "rag_embeddings")
        )
        config_service = ConfigService()
        
        return llm_service, vectordb_service, config_service

    def _init_rl_agent(self):
        """Initialize RL Healing Agent"""
        try:
            db_path = os.getenv("RAG_DB_PATH", "./chroma_db/rag.db")
            return RLHealingAgent(db_path)
        except Exception as e:
            print(f"Warning: Failed to initialize RL agent: {e}")
            return None

    def _build_ingestion_graph(self):
        """Build ingestion workflow graph."""
        graph = StateGraph(dict)
        
        # Define nodes
        def extract_metadata_node(state):
            try:
                meta_response = extract_metadata_tool.invoke({"text": state["text"], "llm_service": self.llm_service})
                state["metadata"] = json.loads(meta_response) if isinstance(meta_response, str) else meta_response
                state["status"] = "metadata_extracted"
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Metadata extraction failed: {e}"]
            return state

        def chunk_document_node(state):
            try:
                chunks_response = chunk_document_tool.invoke({"text": state["text"], "doc_id": state["doc_id"]})
                state["chunks"] = json.loads(chunks_response) if isinstance(chunks_response, str) else chunks_response
                state["status"] = "chunks_created"
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Chunking failed: {e}"]
            return state

        def save_vectordb_node(state):
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
        """Build retrieval workflow graph with intelligent healing integration."""
        graph = StateGraph(dict)

        def retrieve_context_node(state):
            try:
                context_response = retrieve_context_tool.invoke({
                    "question": state["question"],
                    "llm_service": self.llm_service,
                    "vectordb_service": self.vectordb_service,
                    "k": 5
                })
                state["context"] = json.loads(context_response) if isinstance(context_response, str) else context_response
                state["status"] = "context_retrieved"
                state["retrieval_quality"] = len(state["context"].get("context", [])) / 5.0  # Normalize to 0-1
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Context retrieval failed: {e}"]
                state["retrieval_quality"] = 0.0
            return state

        def rerank_context_node(state):
            try:
                reranked_response = rerank_context_tool.invoke({
                    "context": json.dumps(state.get("context", {})),
                    "llm_service": self.llm_service
                })
                state["reranked_context"] = json.loads(reranked_response) if isinstance(reranked_response, str) else reranked_response
                state["status"] = "context_reranked"
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Context reranking failed: {e}"]
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
                answer_response = answer_question_tool.invoke({
                    "question": state["question"],
                    "context": json.dumps(state.get("reranked_context", {})),
                    "llm_service": self.llm_service
                })
                state["answer"] = answer_response
                state["status"] = "answer_generated"
                
                # Log query to database with metrics
                try:
                    from ....database.models.rag_history_model import RAGHistoryModel
                    
                    DEBUG = state.get("response_mode") == "verbose"  # Only show debug for verbose mode
                    
                    if DEBUG: print(f"[DEBUG] Starting query logging...")
                    reranked = state.get("reranked_context", {}).get("reranked_context", [])
                    if DEBUG: print(f"[DEBUG] Reranked context items: {len(reranked)}")
                    
                    metrics = {
                        "frequency": 1,
                        "avg_accuracy": state.get("retrieval_quality", 0.7),
                        "cost_tokens": len(state["question"].split()) * 10,  # Rough estimate
                        "latency_ms": 0,  # Would need timing
                        "user_feedback": 0.7,  # Default, will be updated by user
                        "quality_category": "warm" if state.get("retrieval_quality", 0) > 0.6 else "cold",
                        "sources_count": len(reranked)
                    }
                    
                    if DEBUG: print(f"[DEBUG] Instantiating RAGHistoryModel...")
                    rag_history = RAGHistoryModel()
                    if DEBUG: print(f"[DEBUG] RAGHistoryModel connected to: {rag_history.db_path}")
                    
                    # Get doc_id from context if not in state
                    doc_id_to_log = state.get("doc_id")
                    if DEBUG: print(f"[DEBUG] doc_id from state: {doc_id_to_log}")
                    
                    if not doc_id_to_log and reranked and len(reranked) > 0:
                        # Extract from first retrieved document
                        doc_id_to_log = reranked[0].get("metadata", {}).get("doc_id") or reranked[0].get("source", "unknown")
                        if DEBUG: print(f"[DEBUG] doc_id extracted from context: {doc_id_to_log}")
                    
                    doc_id_to_log = doc_id_to_log or "unknown"
                    if DEBUG: print(f"[DEBUG] Final doc_id_to_log: {doc_id_to_log}")
                    
                    query_id = rag_history.log_query(
                        query_text=state["question"],
                        target_doc_id=doc_id_to_log,
                        metrics_json=json.dumps(metrics),
                        context_json=json.dumps({
                            "retrieval_quality": state.get("retrieval_quality", 0.7),
                            "sources": len(reranked),
                            "answer_length": len(state["answer"].split()) if state["answer"] else 0
                        }),
                        agent_id="langgraph_agent",
                        session_id=state.get("session_id", "session_default")
                    )
                    
                    if DEBUG: print(f"[DEBUG] Query logged successfully: query_id={query_id}, question='{state['question'][:50]}...'")
                    state["query_logged_id"] = query_id
                    
                    # Verify it was written
                    rag_history.cursor.execute("SELECT COUNT(*) FROM rag_history_and_optimization WHERE event_type = 'QUERY'")
                    count = rag_history.cursor.fetchone()[0]
                    if DEBUG: print(f"[DEBUG] Total QUERY events in database: {count}")
                    rag_history.close()
                    
                except Exception as e:
                    import traceback
                    print(f"[ERROR] Failed to log query: {e}")
                    print(f"[TRACEBACK] {traceback.format_exc()}")
                    # Don't fail the answer generation if logging fails
                    
            except Exception as e:
                state["errors"] = state.get("errors", []) + [f"Answer generation failed: {e}"]
                state["answer"] = "Failed to generate answer"
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
                result = adjust_config_tool.invoke({
                    "config_service": self.config_service,
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
            
            return {
                "success": len(result.get("errors", [])) == 0,
                "question": question,
                "answer": answer_text,
                "session_id": session_id,
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
            
            return {
                "success": len(result.get("errors", [])) == 0,
                "answer": answer_text,  # Plain text only
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
                "errors": result.get("errors", [])
            }
        else:  # verbose mode (default for engineers/admins)
            # Full business intelligence: all metadata, traceability, RL info
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
