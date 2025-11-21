"""
Healing Tools
Tools for REFRAG self-healing: heatmap analysis, quality detection, reindexing
NO RAW SQL - All queries through model methods
"""
import json
import hashlib
import sqlite3
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from ...database.models.tracking_model import QueryHeatmapModel, HealingOperationModel, SyntheticQueryModel
from ...database.models.embedding_model import EmbeddingMetadataModel
from ...database.models.document_model import DocumentModel


@tool
def analyze_heatmap_tool(db_service) -> str:
    """
    Analyze query heatmap to find optimization opportunities.
    NO RAW SQL - Uses QueryHeatmapModel methods
    
    Args:
        db_service: Database service instance
        
    Returns:
        JSON string with heatmap analysis
    """
    try:
        # Get connection and initialize model
        conn = sqlite3.connect(db_service.db_path)
        conn.row_factory = sqlite3.Row
        heatmap_model = QueryHeatmapModel(conn)
        
        # Get analysis using model methods - NO RAW SQL
        analysis = heatmap_model.get_heatmap_analysis()
        avg_fb = heatmap_model.get_avg_user_feedback()
        
        # Generate recommendations
        recommendations = []
        
        if analysis['cold_spots']:
            recommendations.append({
                "type": "cold_spots",
                "count": len(analysis['cold_spots']),
                "action": "Generate synthetic questions for low-frequency queries"
            })
        
        if analysis['poor_quality']:
            recommendations.append({
                "type": "poor_quality",
                "count": len(analysis['poor_quality']),
                "action": "Reindex documents with poor retrieval accuracy"
            })
        
        if analysis['slow_queries']:
            recommendations.append({
                "type": "slow_queries",
                "count": len(analysis['slow_queries']),
                "action": "Optimize chunking strategy for slow queries"
            })
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "total_queries": len(analysis['cold_spots']) + len(analysis['poor_quality']) + len(analysis['slow_queries']),
            "avg_user_feedback": round(avg_fb, 2) if avg_fb else None,
            "cold_spots": analysis['cold_spots'][:5],
            "poor_quality": analysis['poor_quality'][:5],
            "slow_queries": analysis['slow_queries'][:5],
            "recommendations": recommendations
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool
def detect_low_quality_tool(threshold: float, db_service) -> str:
    """
    Detect low-quality embeddings that need reindexing.
    NO RAW SQL - Uses EmbeddingMetadataModel methods
    
    Args:
        threshold: Quality score threshold (0.0-1.0)
        db_service: Database service instance
        
    Returns:
        JSON string with low-quality documents
    """
    try:
        # Get connection and initialize model
        conn = sqlite3.connect(db_service.db_path)
        conn.row_factory = sqlite3.Row
        emb_model = EmbeddingMetadataModel(conn)
        
        # Get low-quality documents using model method - NO RAW SQL
        low_quality = emb_model.get_low_quality_documents(threshold)
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "threshold": threshold,
            "num_documents": len(low_quality),
            "documents": [
                {
                    "document_id": doc['document_id'],
                    "avg_quality": round(doc['avg_quality'], 3),
                    "num_chunks": doc['num_chunks']
                }
                for doc in low_quality
            ]
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool
def generate_synthetic_questions_tool(doc_id: str, count: int, llm_service, db_service) -> str:
    """
    Generate synthetic questions for a document to improve retrieval.
    NO RAW SQL - Uses DocumentModel and SyntheticQueryModel methods
    
    Args:
        doc_id: Document ID
        count: Number of questions to generate
        llm_service: LLM service instance
        db_service: Database service instance
        
    Returns:
        JSON string with generated questions
    """
    try:
        # Get connection and initialize models
        conn = sqlite3.connect(db_service.db_path)
        conn.row_factory = sqlite3.Row
        doc_model = DocumentModel(conn)
        synth_model = SyntheticQueryModel(conn)
        
        # Get document content using model method - NO RAW SQL
        doc = doc_model.find_by_id(doc_id)
        if not doc:
            conn.close()
            return json.dumps({
                "success": False,
                "error": f"Document not found: {doc_id}"
            })
        
        content = doc_model.get_content_by_id(doc_id)[:3000]  # Limit to first 3000 chars
        
        # Generate questions
        prompt = f"""Generate {count} diverse, realistic questions that this document could answer.

Make questions vary in:
- Complexity (simple facts to multi-hop reasoning)
- Specificity (broad overview to specific details)
- Phrasing (different ways to ask the same thing)

Document excerpt:
{content}

Respond ONLY with valid JSON in this format:
{{
    "questions": ["question1", "question2", ...]
}}
"""
        
        result = llm_service.generate_json(prompt)
        questions = result.get('questions', [])
        
        # Store synthetic questions using model method - NO RAW SQL
        for question in questions:
            synth_model.store_synthetic_question(doc_id, question)
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "doc_id": doc_id,
            "num_questions": len(questions),
            "questions": questions
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool
def reindex_documents_tool(doc_ids: str, new_strategy: str, 
                          vectordb_service, db_service, llm_service) -> str:
    """
    Re-chunk and re-embed documents with new strategy.
    NO RAW SQL - Uses DocumentModel and EmbeddingMetadataModel methods
    
    Args:
        doc_ids: JSON list of document IDs
        new_strategy: New chunking strategy ('recursive', 'semantic', etc.)
        vectordb_service: Vector DB service instance
        db_service: Database service instance
        llm_service: LLM service instance
        
    Returns:
        JSON string with reindexing results
    """
    try:
        doc_id_list = json.loads(doc_ids)
        
        # Get connection and initialize models
        conn = sqlite3.connect(db_service.db_path)
        conn.row_factory = sqlite3.Row
        doc_model = DocumentModel(conn)
        emb_model = EmbeddingMetadataModel(conn)
        
        results = {
            "reindexed_count": 0,
            "total_new_chunks": 0,
            "documents": []
        }
        
        for doc_id in doc_id_list:
            # Get document using model method - NO RAW SQL
            doc = doc_model.find_by_id(doc_id)
            
            if not doc:
                continue
            
            content = doc_model.get_content_by_id(doc_id)
            
            # Delete old embeddings
            vectordb_service.delete_by_document(doc_id)
            
            # Re-chunk (using ingestion tools)
            from tools.ingestion_tools import chunk_document_tool, generate_embeddings_tool
            
            chunks_result = chunk_document_tool(content, new_strategy, 500, 50)
            embeddings_result = generate_embeddings_tool(chunks_result, llm_service)
            
            chunks_data = json.loads(embeddings_result)
            
            if chunks_data.get('success'):
                num_chunks = chunks_data['num_embeddings']
                
                # Update reindex count using model method - NO RAW SQL
                emb_model.increment_reindex_count(doc_id, new_strategy)
                
                results['reindexed_count'] += 1
                results['total_new_chunks'] += num_chunks
                results['documents'].append({
                    "doc_id": doc_id,
                    "num_chunks": num_chunks,
                    "strategy": new_strategy
                })
        
        conn.close()
        
        return json.dumps({
            "success": True,
            "new_strategy": new_strategy,
            **results
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool
def optimize_chunk_strategy_tool(doc_id: str, vectordb_service, db_service, llm_service) -> str:
    """
    Test different chunking strategies and select the best one.
    NO RAW SQL - Uses DocumentModel methods
    
    Args:
        doc_id: Document ID
        vectordb_service: Vector DB service instance
        db_service: Database service instance
        llm_service: LLM service instance
        
    Returns:
        JSON string with optimization results
    """
    try:
        # Get connection and initialize model
        conn = sqlite3.connect(db_service.db_path)
        conn.row_factory = sqlite3.Row
        doc_model = DocumentModel(conn)
        
        # Get document using model method - NO RAW SQL
        doc = doc_model.find_by_id(doc_id)
        if not doc:
            conn.close()
            return json.dumps({
                "success": False,
                "error": f"Document not found: {doc_id}"
            })
        
        content = doc_model.get_content_by_id(doc_id)
        conn.close()
        
        # Test different strategies
        strategies = ['recursive', 'character', 'token']
        results = []
        
        from tools.ingestion_tools import chunk_document_tool
        
        for strategy in strategies:
            chunks_result = chunk_document_tool(content, strategy, 500, 50)
            chunks_data = json.loads(chunks_result)
            
            if chunks_data.get('success'):
                results.append({
                    "strategy": strategy,
                    "num_chunks": chunks_data['num_chunks'],
                    "avg_chunk_size": sum(c['size'] for c in chunks_data['chunks']) / chunks_data['num_chunks']
                })
        
        # Select best strategy (fewest chunks with reasonable size)
        best = min(results, key=lambda x: abs(x['avg_chunk_size'] - 500))
        
        return json.dumps({
            "success": True,
            "doc_id": doc_id,
            "tested_strategies": results,
            "recommended_strategy": best['strategy'],
            "reasoning": f"Best average chunk size: {best['avg_chunk_size']:.0f} chars"
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })
