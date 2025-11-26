"""Retrieval Agent Tools

A complete set of tools for a RAG Retrieval Agent with unified, working functions:
- retrieve_context_tool: Retrieve relevant documents
- rerank_context_tool: Rerank by relevance
- answer_question_tool: Generate answer
- traceability_tool: Full provenance tracking
"""
import json
from typing import List, Dict, Any
from langchain_core.tools import tool


# --- Unified retrieval tools ---

@tool
def retrieve_context_tool(question: str, llm_service, vectordb_service, rbac_namespace: str = "general", k: int = 5) -> str:
    """Retrieve relevant context from vector database."""
    try:
        query_embedding = llm_service.generate_embedding(question)
        results = vectordb_service.search(query_embedding, top_k=k)
        
        context_list = []
        if results.get('documents') and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                context_list.append({
                    "text": doc,
                    "score": float(results['distances'][0][i]) if results['distances'] else 0,
                    "metadata": results['metadatas'][0][i] if results.get('metadatas') else {}
                })
        
        return json.dumps({"success": True, "context": context_list})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def rerank_context_tool(context: str, llm_service) -> str:
    """Rerank retrieved context."""
    try:
        context_data = json.loads(context) if isinstance(context, str) else context
        reranked = sorted(context_data.get('context', []), key=lambda x: x.get('score', 0), reverse=True)
        return json.dumps({"success": True, "reranked_context": reranked})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def answer_question_tool(question: str, context: str, llm_service) -> str:
    """Generate answer based on context."""
    try:
        context_data = json.loads(context) if isinstance(context, str) else context
        context_texts = context_data.get('reranked_context', [])
        
        if not context_texts:
            return json.dumps({"success": True, "answer": "No context available to answer the question."})
        
        context_text = "\n\n".join([f"[Source: {c.get('metadata', {}).get('doc_id', 'N/A')}]\n{c['text']}" 
                                      for c in context_texts])
        
        prompt = f"""Based on the following context, answer the question concisely.

Context:
{context_text}

Question: {question}

Answer:"""
        
        answer = llm_service.generate_response(prompt)
        return json.dumps({"success": True, "answer": answer})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@tool
def traceability_tool(question: str, context: str, vectordb_service) -> str:
    """Provide full traceability for the answer."""
    try:
        context_data = json.loads(context) if isinstance(context, str) else context
        context_texts = context_data.get('reranked_context', [])
        
        trace = {
            "question": question,
            "sources_used": len(context_texts),
            "documents": [
                {
                    "doc_id": c.get('metadata', {}).get('doc_id', 'N/A'),
                    "chunk_index": c.get('metadata', {}).get('chunk_index', 'N/A'),
                    "similarity_score": float(c.get('score', 0)),
                    "text_preview": (c['text'][:100] + "...") if len(c['text']) > 100 else c['text']
                }
                for c in context_texts
            ]
        }
        return json.dumps({"success": True, "traceability": trace})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


# --- Deprecated: Pre-Retrieval Tools (for reference) ---
    """
    Retrieves the list of authorized hierarchical RBAC tags (permissions) for a given user ID.
    This is the first step in retrieval to establish security context.

    Args:
        user_id (str): The unique identifier for the querying user.
        mapping_service: Service object providing a .resolve_user_roles(user_id) method
                         that accesses the centralized role mapping JSON/DB.

    Returns:
        JSON string with 'success' and 'authorized_rbac_tags' list 
        (e.g., ["1", "1-3", "1-3-1"]).
    """
    try:
        # Example: user_id -> mapping_service -> ["1", "1-3", "1-3-1"]
        authorized_tags = mapping_service.resolve_user_roles(user_id)

        if not authorized_tags:
            return json.dumps({"success": True, "authorized_rbac_tags": ["general_public"]})

        return json.dumps({"success": True, "authorized_rbac_tags": authorized_tags})

    except Exception as e:
        return json.dumps({"success": False, "error": f"Failed to resolve permissions: {str(e)}"})


@tool
def rewrite_query_tool(query: str, llm_service) -> str:
    """
    Generates multiple, diverse queries (including keyword queries and declarative statements) 
    from a single user question to improve search recall and handle ambiguity.

    Args:
        query (str): The original user question.

    Returns:
        JSON string with 'success' and a list of 'optimized_queries'.
    """
    try:
        prompt = f"""Generate 3-5 alternative search queries (including keyword lists and rephrased questions) 
        that would help find the most relevant context for the user's question.

        Original Query: "{query}"

        Return JSON array of strings."""
        
        # Assume llm_service.generate_json handles the structured output.
        result = llm_service.generate_json(prompt)
        
        # Ensure result is a list of strings
        optimized_queries = result if isinstance(result, list) else json.loads(result)
        optimized_queries = [q for q in optimized_queries if isinstance(q, str)]

        # Always include the original query
        if query not in optimized_queries:
            optimized_queries.append(query)
            
        return json.dumps({"success": True, "optimized_queries": list(set(optimized_queries))})

    except Exception as e:
        # Fallback to just the original query
        return json.dumps({"success": True, "optimized_queries": [query]})


# --- 2. Core Retrieval Tool (with Hierarchical RBAC) ---

@tool
def retrieve_relevant_context_tool(queries: List[str], authorized_rbac_tags: List[str], llm_service, vectordb_service, k_per_query: int = 3) -> str:
    """
    Executes multiple vector searches across authorized RBAC collections (hierarchical VDB structure).
    
    Args:
        queries (List[str]): List of optimized search queries (from rewrite_query_tool).
        authorized_rbac_tags (List[str]): List of hierarchical access tags (e.g., ["1", "1-3", "1-3-1"]).
        llm_service: The language model service for generating embeddings.
        vectordb_service: The vector database service for querying.
        k_per_query (int): Number of top chunks to retrieve per query, per authorized tag.

    Returns:
        JSON string containing 'success', a list of unique 'raw_results' (chunks), 
        and the total number of chunks retrieved.
    """
    all_results = []
    
    # Set to track unique chunk_id + tag combinations to avoid duplicates
    seen_chunks = set() 
    
    try:
        # NOTE: vectordb_service and llm_service are assumed to be available in the context.
        # This function iterates through all authorized access levels (collections) and all queries.
        
        for rbac_tag in authorized_rbac_tags:
            # VDB Filtering: Use the RBAC tag to identify the specific VDB collection/index.
            # This relies on the ingestion process (Strategy 1) having created multiple 
            # collections based on the hierarchical tags.
            collection_name = f"rbac_{rbac_tag.replace('*', 'all')}" 
            
            try:
                collection = vectordb_service.get_collection(collection_name)
                
                for query in queries:
                    # Generate embedding for the query
                    query_embedding = llm_service.generate_embedding(query)
                    
                    # Perform search within the authorized collection
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=k_per_query,
                    )
                    
                    # Process Results
                    if results and results.get('documents'):
                        for i in range(len(results['documents'][0])):
                            metadata = results['metadatas'][0][i]
                            
                            chunk_id = metadata.get('doc_id', 'unknown') + metadata.get('chunk_index', '0')
                            unique_key = (chunk_id, rbac_tag)
                            
                            if unique_key not in seen_chunks:
                                seen_chunks.add(unique_key)
                                all_results.append({
                                    "chunk_text": results['documents'][0][i],
                                    "doc_id": metadata.get('doc_id', 'N/A'),
                                    "rbac_source_tag": rbac_tag,
                                    "score": results['distances'][0][i]
                                })
                                
            except Exception as e:
                # Log warning for collection access failure but continue
                print(f"Warning: Collection {collection_name} failed or is empty: {e}")


        return json.dumps({
            "success": True,
            "total_raw_results": len(all_results),
            "raw_results": all_results 
        })

    except Exception as e:
        return json.dumps({"success": False, "error": f"Retrieval failed: {str(e)}"})


# --- 3. Post-Retrieval Tools ---

@tool
def rerank_results_tool(query: str, raw_results: List[Dict[str, Any]], k_final: int = 5) -> str:
    """
    Reranks the raw retrieved chunks using a powerful cross-encoder model 
    to filter noise and select the most relevant chunks for synthesis.
    (Note: reranker_service is not implemented in this direct import version.)
    """
    if not raw_results:
        return json.dumps({"success": True, "final_context": []})

    try:
        # Placeholder: just return top k by score
        fallback_context = sorted(raw_results, key=lambda x: x['score'], reverse=True)[:k_final]
        return json.dumps({"success": True, "final_context": [
            {"text": item['chunk_text'], "source": f"Doc ID: {item['doc_id']} (RBAC: {item.get('rbac_source_tag', '')})"}
            for item in fallback_context
        ]})
    except Exception as e:
        return json.dumps({"success": False, "error": f"Reranking failed: {str(e)}"})

@tool
def synthesize_answer_tool(query: str, context: List[Dict[str, str]], llm_service) -> str:
    """
    Generates the final, grounded answer using the retrieved context.
    """
    if not context:
        return json.dumps({"success": False, "answer": "I do not have enough specific context to answer that question.", "sources": []})

    try:
        context_text = "\n\n--- Source Document ---\n\n".join([c['text'] for c in context])
        sources = [c['source'] for c in context]
        system_prompt = (
            "You are a professional corporate knowledge assistant. Your task is to provide a "
            "clear, concise, and accurate answer based ONLY on the CONTEXT provided below. "
            "If the context does not contain the answer, state explicitly that you cannot answer."
        )
        user_prompt = f"""
        CONTEXT:
        {context_text}
        
        QUESTION: 
        {query}
        """
        # Use llm_service directly
        final_answer = llm_service.generate_response(
            prompt=user_prompt
        )
        return json.dumps({
            "success": True,
            "answer": final_answer,
            "sources": list(set(sources))
        })
    except Exception as e:
        return json.dumps({"success": False, "error": f"Answer synthesis failed: {str(e)}"})