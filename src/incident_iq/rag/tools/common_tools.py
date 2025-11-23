"""
Common Tools
Shared utility tools for all agents
Uses model-based database layer for consistent data access
"""
import json
import sqlite3
from typing import Dict, Any
from langchain_core.tools import tool
from ...database.models.document_model import DocumentModel
from ...database.models.embedding_model import EmbeddingMetadataModel
from ...database.models.agent_model import AgentOperationModel, TokenUsageModel
from ...database.models.tracking_model import QueryHeatmapModel, HealingOperationModel
from ...database.models.rbac_model import RBACModel


@tool
def get_system_status_tool(db_service, vectordb_service) -> str:
    """
    Get comprehensive system status using model-based access.

    Args:
        db_service: Database service instance
        vectordb_service: Vector DB service instance

    Returns:
        JSON string with system status
    """
    try:
        # Get connection from db_service
        conn = sqlite3.connect(db_service.db_path)
        conn.row_factory = sqlite3.Row

        # Initialize models
        doc_model = DocumentModel(conn)
        emb_model = EmbeddingMetadataModel(conn)
        ops_model = AgentOperationModel(conn)
        token_model = TokenUsageModel(conn)
        rbac_model = RBACModel(conn)
        healing_model = HealingOperationModel(conn)
        heatmap_model = QueryHeatmapModel(conn)

        # Document counts
        total_docs = doc_model.count()
        total_chunks = emb_model.count()
        vector_count = vectordb_service.count()

        # Operation stats
        total_ops = ops_model.count()
        recent_ops = ops_model.get_recent_operations_count(24)

        # Token usage
        tokens = token_model.get_total_tokens_used()

        # Query heatmap stats
        heatmap_stats = heatmap_model.get_stats()

        # RBAC stats
        total_users = rbac_model.get_total_users_count()

        # Healing stats
        total_healing = healing_model.count()

        conn.close()

        return json.dumps({
            "success": True,
            "documents": {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "vector_embeddings": vector_count
            },
            "operations": {
                "total_operations": total_ops,
                "recent_operations_24h": recent_ops,
                "total_tokens_used": tokens
            },
            "queries": {
                "total_unique_queries": heatmap_stats.get('total_unique_queries', 0),
                "total_invocations": heatmap_stats.get('total_query_invocations', 0),
                "avg_retrieval_accuracy": round(heatmap_stats.get('avg_retrieval_accuracy', 0), 2),
                "avg_response_time_ms": round(heatmap_stats.get('avg_response_time_ms', 0), 0)
            },
            "rbac": {
                "total_users": total_users
            },
            "healing": {
                "total_healing_operations": total_healing
            }
        })

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@tool
def query_database_tool(sql_query: str, db_service) -> str:
    """
    Execute a SQL query on the database (read-only).

    Args:
        sql_query: SQL SELECT query
        db_service: Database service instance

    Returns:
        JSON string with query results
    """
    try:
        # Security: Only allow SELECT queries
        if not sql_query.strip().upper().startswith('SELECT'):
            return json.dumps({
                "success": False,
                "error": "Only SELECT queries are allowed"
            })

        results = db_service.query(sql_query)

        return json.dumps({
            "success": True,
            "num_rows": len(results),
            "results": results[:100]  # Limit to 100 rows
        })

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })
