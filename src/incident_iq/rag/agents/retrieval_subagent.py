"""
Retrieval SubAgent for RAG Master Agent
Specialized for information search and retrieval operations
"""
import json
import time
from typing import Dict, Any, List, Optional


class RetrievalSubAgent:
    """
    SubAgent specialized for information retrieval operations.
    
    Handles:
    - Query processing and intent understanding
    - Vector similarity search with ranking
    - Result filtering and reranking
    - Answer synthesis and citation
    - Context expansion and refinement
    """
    
    def __init__(self, services: Dict[str, Any], parent=None):
        """
        Initialize retrieval subagent.
        
        Args:
            services: Dictionary containing 'llm' and 'vectordb' service instances
            parent: Reference to parent RAGMasterAgent (optional)
        """
        self.services = services
        self.parent = parent
        self.name = "RetrievalSubAgent"
        self.llm_service = services.get("llm")
        self.vectordb_service = services.get("vectordb")
        
        # Configuration
        self.default_top_k = 5
        self.similarity_threshold = 0.7
        self.max_context_length = 4000
        
        # Initialize metrics
        self.metrics = {
            "queries_processed": 0,
            "total_results_returned": 0,
            "avg_similarity_score": 0.0,
            "processing_time_ms": 0
        }
    

    
    # ========================================================================
    # PUBLIC API METHODS
    # ========================================================================
    
    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute retrieval operation based on request.
        
        Args:
            request: Dictionary with retrieval details:
                {
                    'query': <search_query>,
                    'top_k': <number_of_results>,
                    'filters': <optional_metadata_filters>,
                    'config': <optional_config_overrides>
                }
        
        Returns:
            Dictionary with retrieval results
        """
        start_time = time.time()
        
        try:
            # Extract query from request
            query = request.get('query')
            top_k = request.get('top_k', self.default_top_k)
            filters = request.get('filters')
            config = request.get('config', {})
            
            if not query:
                raise ValueError("No query provided for retrieval")
            
            # Apply config overrides
            self._apply_config(config)
            
            # Execute retrieval
            result = self._retrieve_information(query, top_k, filters)
            
            # Update metrics
            elapsed_ms = int((time.time() - start_time) * 1000)
            self._update_metrics(result, elapsed_ms)
            
            # Notify parent if available
            if self.parent:
                self.parent.receive_subagent_result('retrieval', result)
            
            return result
            
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            error_result = {
                "success": False,
                "error": str(e),
                "query": request.get('query', ''),
                "time_ms": elapsed_ms
            }
            
            if self.parent:
                self.parent.receive_subagent_result('retrieval', error_result)
                
            return error_result
    
    def retrieve_information(self, query: str, top_k: int = None, 
                           filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Direct retrieval method (backward compatibility)."""
        request = {
            'query': query,
            'top_k': top_k or self.default_top_k,
            'filters': filters
        }
        return self.execute(request)
    
    def search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Simple search interface."""
        return self.retrieve_information(query, **kwargs)
    
    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================
    
    def _apply_config(self, config: Dict[str, Any]) -> None:
        """Apply configuration overrides."""
        self.default_top_k = config.get('top_k', self.default_top_k)
        self.similarity_threshold = config.get('similarity_threshold', self.similarity_threshold)
        self.max_context_length = config.get('max_context_length', self.max_context_length)
    
    def _retrieve_information(self, query: str, top_k: int, 
                            filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Core retrieval logic."""
        try:
            # Step 1: Generate query embedding
            query_embedding = self.llm_service.generate_embedding(query)
            
            # Step 2: Search vector database
            search_params = {
                'query_embedding': query_embedding,
                'top_k': top_k
            }
            
            if filters:
                search_params['where_filter'] = filters
            
            search_results = self.vectordb_service.search(**search_params)
            
            # Step 3: Process and format results
            if search_results and search_results.get('ids'):
                formatted_results = self._format_search_results(search_results)
                
                # Step 4: Filter by similarity threshold
                filtered_results = [
                    result for result in formatted_results 
                    if result.get('similarity', 0) >= self.similarity_threshold
                ]
                
                # Step 5: Synthesize answer if results found
                if filtered_results:
                    synthesized_answer = self._synthesize_answer(query, filtered_results)
                    
                    return {
                        "success": True,
                        "query": query,
                        "num_results": len(filtered_results),
                        "results": filtered_results,
                        "answer": synthesized_answer,
                        "avg_similarity": sum(r.get('similarity', 0) for r in filtered_results) / len(filtered_results)
                    }
                else:
                    return {
                        "success": True,
                        "query": query,
                        "num_results": 0,
                        "results": [],
                        "message": "No relevant documents found above similarity threshold"
                    }
            else:
                return {
                    "success": True,
                    "query": query,
                    "num_results": 0,
                    "results": [],
                    "message": "No documents found in vector database"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _format_search_results(self, search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format raw search results into structured format."""
        ids = search_results.get('ids', [[]])[0]
        documents = search_results.get('documents', [[]])[0]
        distances = search_results.get('distances', [[]])[0]
        metadatas = search_results.get('metadatas', [[]])[0]
        
        formatted_results = []
        
        for i in range(len(documents)):
            similarity = 1 - distances[i] if i < len(distances) else 0.0
            metadata = metadatas[i] if i < len(metadatas) else {}
            
            formatted_results.append({
                "chunk_id": ids[i] if i < len(ids) else f"chunk_{i}",
                "text": documents[i],
                "similarity": round(similarity, 4),
                "metadata": metadata,
                "source": metadata.get('source', 'unknown'),
                "doc_id": metadata.get('doc_id', 'unknown')
            })
        
        return formatted_results
    
    def _synthesize_answer(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Synthesize a coherent answer from search results."""
        try:
            # Limit context length
            context_chunks = []
            total_length = 0
            
            for i, result in enumerate(results):
                text = result.get('text', '')
                if total_length + len(text) <= self.max_context_length:
                    context_chunks.append(f"[Source {i+1}] {text}")
                    total_length += len(text)
                else:
                    break
            
            context = "\n\n".join(context_chunks)
            
            # Generate synthesis prompt
            prompt = f"""Based on the following context, provide a comprehensive answer to the user's question.

Context:
{context}

Question: {query}

Instructions:
- Provide a clear, accurate, and comprehensive answer
- Use information from the provided sources
- Cite sources using [Source N] notation
- If information is incomplete, acknowledge limitations
- Be factual and avoid speculation

Answer:"""
            
            # Generate answer using LLM
            answer = self.llm_service.generate_response(prompt)
            
            return answer.strip()
            
        except Exception as e:
            return f"Unable to synthesize answer: {str(e)}"
    
    def _update_metrics(self, result: Dict[str, Any], elapsed_ms: int) -> None:
        """Update retrieval metrics."""
        self.metrics["queries_processed"] += 1
        self.metrics["processing_time_ms"] += elapsed_ms
        
        if result.get("success"):
            num_results = result.get("num_results", 0)
            avg_similarity = result.get("avg_similarity", 0.0)
            
            self.metrics["total_results_returned"] += num_results
            
            # Update rolling average of similarity scores
            current_avg = self.metrics["avg_similarity_score"]
            queries_count = self.metrics["queries_processed"]
            
            if queries_count > 1:
                self.metrics["avg_similarity_score"] = (
                    (current_avg * (queries_count - 1) + avg_similarity) / queries_count
                )
            else:
                self.metrics["avg_similarity_score"] = avg_similarity
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get subagent metrics."""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset subagent metrics."""
        self.metrics = {
            "queries_processed": 0,
            "total_results_returned": 0,
            "avg_similarity_score": 0.0,
            "processing_time_ms": 0
        }