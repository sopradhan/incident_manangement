#!/usr/bin/env python3
"""
Test script to verify metadata is being saved to optimized SQLite schema
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from incident_iq.database.models.document_metadata_model import DocumentMetadataModel
from incident_iq.database.models.chunk_embedding_data_model import ChunkEmbeddingDataModel
from incident_iq.database.models.rag_history_model import RAGHistoryModel


def main():
    """Test the optimized schema models"""
    
    print("=" * 80)
    print("TESTING OPTIMIZED SCHEMA MODELS")
    print("=" * 80)
    
    project_root = Path(__file__).parent.parent
    db_path = str(project_root / "chroma_db" / "rag.db")
    
    print(f"\nDatabase: {db_path}\n")
    
    # Test DocumentMetadataModel
    print("=" * 80)
    print("1. DOCUMENT METADATA MODEL")
    print("=" * 80)
    
    doc_model = DocumentMetadataModel(db_path)
    
    # Get existing documents
    docs = doc_model.get_all()
    print(f"\nTotal documents in DB: {doc_model.count()}")
    
    if docs:
        print(f"\nDocuments:")
        for doc in docs[:5]:
            print(f"  - {doc['doc_id']}: {doc['title']} (author: {doc['author']})")
            print(f"    Namespace: {doc['rbac_namespace']}, Strategy: {doc['chunk_strategy']}")
            print(f"    Last Ingested: {doc['last_ingested']}")
    else:
        print("\nNo documents found in database")
    
    doc_model.close()
    
    # Test ChunkEmbeddingDataModel
    print("\n" + "=" * 80)
    print("2. CHUNK EMBEDDING DATA MODEL")
    print("=" * 80)
    
    chunk_model = ChunkEmbeddingDataModel(db_path)
    
    stats = chunk_model.get_statistics()
    print(f"\nChunk Statistics:")
    print(f"  Total Chunks: {stats.get('total_chunks', 0)}")
    print(f"  Avg Quality: {stats.get('avg_quality', 0):.2f}")
    print(f"  Min Quality: {stats.get('min_quality', 0):.2f}")
    print(f"  Max Quality: {stats.get('max_quality', 0):.2f}")
    
    # Get low quality chunks
    low_quality = chunk_model.get_low_quality_chunks(threshold=0.7)
    if low_quality:
        print(f"\nLow Quality Chunks (< 0.7):")
        for chunk in low_quality[:5]:
            print(f"  - {chunk['chunk_id']}: quality={chunk['quality_score']:.2f}")
    
    # Get chunks by doc
    if docs:
        first_doc = docs[0]
        doc_chunks = chunk_model.get_by_doc_id(first_doc['doc_id'])
        print(f"\nChunks for '{first_doc['doc_id']}': {len(doc_chunks)}")
        if doc_chunks:
            for chunk in doc_chunks[:3]:
                print(f"  - {chunk['chunk_id']}: model={chunk['embedding_model']}, quality={chunk['quality_score']}")
    
    chunk_model.close()
    
    # Test RAGHistoryModel
    print("\n" + "=" * 80)
    print("3. RAG HISTORY MODEL")
    print("=" * 80)
    
    history_model = RAGHistoryModel(db_path)
    
    stats = history_model.get_statistics()
    print(f"\nHistory Statistics:")
    print(f"  Total Records: {stats.get('total', 0)}")
    
    if stats.get('total', 0) > 0:
        for event_type in ['QUERY', 'HEAL', 'SYNTHETIC_TEST']:
            count = stats.get(event_type, 0)
            if count > 0:
                print(f"  {event_type}: {count}")
        
        # Get recent queries
        queries = history_model.get_by_event_type('QUERY', limit=5)
        if queries:
            print(f"\nRecent Queries ({len(queries)}):")
            for q in queries[:3]:
                print(f"  - {q['query_text'][:60]}")
                print(f"    Timestamp: {q['timestamp']}, Quality: {q.get('reward_signal', 'N/A')}")
    else:
        print("  No history records found")
    
    history_model.close()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    doc_count = DocumentMetadataModel(db_path).count()
    
    print(f"""
✓ DocumentMetadataModel: Connected and working
✓ ChunkEmbeddingDataModel: Connected and working  
✓ RAGHistoryModel: Connected and working

Database Status:
  - Documents: {doc_count}
  - Chunks: {stats.get('total_chunks', 0)}
  - History Records: {stats.get('total', 0)}

Tables:
  ✓ document_metadata
  ✓ chunk_embedding_data
  ✓ rag_history_and_optimization
""")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
