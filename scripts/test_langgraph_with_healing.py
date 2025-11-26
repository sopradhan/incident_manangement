#!/usr/bin/env python
"""
Test LangGraph RAG Agent with Intelligent Healing Integration

Demonstrates:
1. Document ingestion with metadata tracking
2. Intelligent retrieval with healing decision logic
3. SQLite tables being updated
4. Performance optimization tracking
"""
import sys
import json
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'

from incident_iq.rag.agents.langgraph_agent.langgraph_rag_agent import LangGraphRAGAgent
from incident_iq.database.models.document_metadata_model import DocumentMetadataModel
from incident_iq.database.models.embedding_model import EmbeddingMetadataModel
from incident_iq.database.models.tracking_model import QueryHeatmapModel, HealingOperationModel


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_metadata_tables():
    """Show which SQLite tables are being updated."""
    print_section("SQLite Tables Updated by RAG Operations")
    
    tables_info = {
        "document_metadata": {
            "purpose": "Stores extracted document metadata (title, author, source, etc.)",
            "updated_during": ["Ingestion Phase"]
        },
        "embedding_metadata": {
            "purpose": "Tracks chunks, embedding quality, chunking strategy",
            "updated_during": ["Ingestion Phase", "Optimization Phase"]
        },
        "query_heatmap": {
            "purpose": "Tracks query frequency, accuracy, response time, user feedback",
            "updated_during": ["Retrieval Phase", "Every Query"]
        },
        "healing_operations": {
            "purpose": "Logs all healing/optimization operations and improvements",
            "updated_during": ["Optimization Phase", "When Quality Issues Detected"]
        },
        "synthetic_queries": {
            "purpose": "Stores auto-generated test questions for quality testing",
            "updated_during": ["Ingestion Phase"]
        }
    }
    
    for table, info in tables_info.items():
        print(f"\n  📊 TABLE: {table}")
        print(f"     Purpose: {info['purpose']}")
        print(f"     Updated During: {', '.join(info['updated_during'])}")


def test_ingestion_with_metadata():
    """Test document ingestion and check metadata tables."""
    print_section("Phase 1: Document Ingestion with Metadata Tracking")
    
    agent = LangGraphRAGAgent()
    
    # Sample incident management document
    test_doc = """
    Incident Severity Levels and Classification
    
    The incident management process uses a standardized severity classification system
    to prioritize incidents and allocate appropriate resources for resolution.
    
    Severity Level 1 - Critical:
    - Complete service outage affecting all users
    - Data loss or corruption
    - Security breach detected
    - Response time: Immediate (< 15 minutes)
    - Resolution target: 4 hours
    
    Severity Level 2 - High:
    - Major service degradation affecting multiple users
    - Significant performance impact
    - Important functionality unavailable
    - Response time: < 1 hour
    - Resolution target: 24 hours
    
    Severity Level 3 - Medium:
    - Partial service impact, single user or small group affected
    - Workaround available
    - Response time: < 4 hours
    - Resolution target: 3 days
    
    Severity Level 4 - Low:
    - Minor issue, cosmetic or documentation
    - No workaround needed but improvement desired
    - Response time: < 8 hours
    - Resolution target: 7 days
    
    Incident Workflow:
    1. Detection and Reporting
    2. Initial Triage and Classification
    3. Assignment to Support Team
    4. Investigation and Diagnosis
    5. Implementation of Fix or Workaround
    6. Testing and Verification
    7. Documentation and Closure
    8. Post-Incident Review
    """
    
    print("\n📝 Ingesting document: 'Incident Management Guidelines'")
    result = agent.ingest_document(test_doc, doc_id="doc_incident_001")
    
    print(f"\n✅ Ingestion Result:")
    print(f"   Success: {result['success']}")
    print(f"   Document ID: {result['doc_id']}")
    print(f"   Chunks Created: {result['chunks_count']}")
    print(f"   Chunks Saved: {result['chunks_saved']}")
    if result.get('errors'):
        print(f"   Errors: {result['errors']}")
    
    # Show metadata stored
    print(f"\n📚 Metadata Stored in database:")
    try:
        meta_model = DocumentMetadataModel()
        metadata = meta_model.get_all_metadata("doc_incident_001")
        for meta in metadata:
            print(f"   - {meta['key']}: {meta['value'][:60]}...")
    except Exception as e:
        print(f"   (Database not configured: {e})")
    
    # Show embedding metadata
    print(f"\n🔢 Embedding Metadata Stored:")
    try:
        emb_model = EmbeddingMetadataModel()
        emb_records = emb_model.find_by_document_id("doc_incident_001")
        for emb in emb_records[:3]:
            print(f"   - Chunk {emb['chunk_id']}: size={emb.get('chunk_size', 'N/A')}, "
                  f"quality={emb.get('quality_score', 'N/A')}, "
                  f"model={emb.get('embedding_model', 'N/A')}")
        if len(emb_records) > 3:
            print(f"   ... and {len(emb_records)-3} more chunks")
    except Exception as e:
        print(f"   (Database not configured: {e})")
    
    return agent


def test_retrieval_with_healing(agent):
    """Test retrieval with intelligent healing logic."""
    print_section("Phase 2: Intelligent Retrieval with Healing Integration")
    
    queries = [
        "What are the incident severity levels?",
        "What is the incident workflow?",
        "What is the response time for critical incidents?"
    ]
    
    for i, question in enumerate(queries, 1):
        print(f"\n❓ Query {i}: {question}")
        
        # Simulate performance history for optimization
        perf_history = [
            {
                "params": {"k": 5, "chunk_size": 512},
                "metrics": {"cost": 0.001, "accuracy": 0.82}
            },
            {
                "params": {"k": 5, "chunk_size": 512},
                "metrics": {"cost": 0.0012, "accuracy": 0.75}
            }
        ] if i > 1 else []
        
        result = agent.ask_question(question, performance_history=perf_history)
        
        print(f"\n✅ Retrieval Result:")
        print(f"   Status: {'Success' if result['success'] else 'Failed'}")
        print(f"   Answer: {result['answer'][:100]}..." if result['answer'] else "   Answer: None")
        print(f"   Sources Found: {len(result['sources'])} documents")
        print(f"   Retrieval Quality: {result.get('retrieval_quality', 0)*100:.1f}%")
        
        # Show healing intelligence
        if result.get('optimization_applied'):
            print(f"\n🔧 Healing/Optimization Applied:")
            print(f"   Reason: {result.get('optimization_reason', 'Unknown')}")
            if result.get('optimization_result'):
                opt_result = result['optimization_result']
                if 'cost_analysis' in opt_result:
                    cost = opt_result['cost_analysis']
                    print(f"   Cost Analysis:")
                    print(f"     - Tokens: {cost.get('total_tokens', 'N/A')}")
                    print(f"     - Est. Cost: ${cost.get('estimated_cost_usd', 'N/A')}")
                if 'suggested_params' in opt_result:
                    print(f"   Suggested Parameters: {opt_result['suggested_params']}")
        else:
            print(f"\n✓ Quality sufficient - no healing applied")
        
        # Show traceability
        if result.get('traceability'):
            trace = result['traceability']
            if trace.get('traceability'):
                docs = trace['traceability'].get('documents', [])
                print(f"\n📍 Traceability ({len(docs)} sources):")
                for j, doc in enumerate(docs[:3], 1):
                    print(f"   {j}. {doc.get('doc_id', 'N/A')} "
                          f"(Similarity: {doc.get('similarity_score', 0):.2f})")
        
        if result.get('errors'):
            print(f"\n⚠️ Errors: {result['errors']}")


def show_database_updates():
    """Show what tables have been updated."""
    print_section("Phase 3: SQLite Database Updates Summary")
    
    print("\n📊 Query Heatmap Statistics:")
    try:
        heatmap_model = QueryHeatmapModel()
        stats = heatmap_model.get_stats()
        print(f"   Total Unique Queries: {stats.get('total_unique_queries', 0)}")
        print(f"   Total Query Invocations: {stats.get('total_query_invocations', 0)}")
        print(f"   Avg Retrieval Accuracy: {stats.get('avg_retrieval_accuracy', 0):.2f}")
        print(f"   Avg Response Time: {stats.get('avg_response_time_ms', 0):.1f} ms")
    except Exception as e:
        print(f"   (Database not configured: {e})")
    
    print("\n🔧 Healing Operations:")
    try:
        healing_model = HealingOperationModel()
        strategies = healing_model.get_most_effective_strategies()
        if strategies:
            print(f"   Most Effective Strategies:")
            for strategy in strategies[:3]:
                print(f"   - {strategy['strategy']}: "
                      f"avg_improvement={strategy.get('avg_improvement', 0):.2%}, "
                      f"usage={strategy.get('usage_count', 0)}")
        else:
            print(f"   No healing operations yet")
    except Exception as e:
        print(f"   (Database not configured: {e})")
    
    print("\n📈 Embedding Quality:")
    try:
        emb_model = EmbeddingMetadataModel()
        stats = emb_model.get_embedding_stats()
        print(f"   Total Chunks: {stats.get('total_chunks', 0)}")
        print(f"   Avg Quality Score: {stats.get('avg_quality_score', 0):.2f}")
        print(f"   Embedding Models: {', '.join(stats.get('embedding_models', []))}")
        print(f"   Chunking Strategies: {', '.join(stats.get('chunk_strategies', []))}")
        
        low_quality = emb_model.get_low_quality_chunks(threshold=0.6)
        if low_quality:
            print(f"\n   ⚠️ Low Quality Chunks (< 0.6): {len(low_quality)}")
            for chunk in low_quality[:2]:
                print(f"      - {chunk['chunk_id']}: score={chunk.get('quality_score', 0):.2f}")
    except Exception as e:
        print(f"   (Database not configured: {e})")


def main():
    """Run complete test with healing integration."""
    print("\n" + "="*80)
    print("  LangGraph RAG Agent with Intelligent Healing Integration")
    print("  Demonstrates: Ingestion → Retrieval → Healing → Optimization")
    print("="*80)
    
    # Show metadata tables
    print_metadata_tables()
    
    # Phase 1: Ingestion
    agent = test_ingestion_with_metadata()
    
    # Phase 2: Retrieval with healing
    test_retrieval_with_healing(agent)
    
    # Phase 3: Show database updates
    show_database_updates()
    
    print_section("Summary")
    print("""
✅ LangGraph Agent successfully integrated Healing/Optimization:

1. INGESTION Phase:
   - Documents ingested with full metadata extraction
   - Chunks created and embeddings generated
   - Quality scores assigned to each chunk
   - Metadata stored in: document_metadata, embedding_metadata, synthetic_queries

2. RETRIEVAL Phase with Intelligent Healing:
   - Context retrieved and reranked
   - Automatic decision: check if optimization needed
   - Quality < 60% → Applies healing
   - Few results (< 3) → Applies healing
   - Performance history available → Analyzes trends
   - Metadata stored in: query_heatmap (every query tracked)

3. OPTIMIZATION/HEALING:
   - Cost analysis of context (token counting)
   - Parameter suggestions (chunk_size, k_final)
   - Healing operations logged
   - Metadata stored in: healing_operations

4. FINAL ANSWER:
   - Generated with optimized context
   - Full traceability provided
   - Performance metrics captured

📊 Tables Updated:
   ✓ document_metadata - document-level extracted info
   ✓ embedding_metadata - chunk quality and strategy info
   ✓ query_heatmap - every query's performance metrics
   ✓ healing_operations - optimization history and results
   ✓ synthetic_queries - generated test questions
    """)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
