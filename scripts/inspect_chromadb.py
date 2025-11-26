"""
ChromaDB Inspector - View embeddings and documents stored in ChromaDB
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from incident_iq.rag.tools.services.vectordb_service import VectorDBService

def inspect_chromadb():
    """Inspect ChromaDB collection."""
    print("\n" + "=" * 80)
    print("🔍 CHROMADB INSPECTOR")
    print("=" * 80)
    
    # Initialize VectorDB service
    vdb = VectorDBService(
        persist_directory="./chroma_db",
        collection_name="rag_embeddings"
    )
    
    # Get collection stats
    count = vdb.count()
    print(f"\n📊 Collection Stats:")
    print(f"   Total documents: {count}")
    
    if count == 0:
        print("   ⚠️  Collection is empty")
        return
    
    # Peek at first 5 documents
    print(f"\n📄 First 5 Documents:")
    peek_result = vdb.peek(limit=5)
    
    if peek_result.get('ids'):
        for i, doc_id in enumerate(peek_result['ids'], 1):
            doc_text = peek_result['documents'][i-1] if peek_result.get('documents') else "N/A"
            metadata = peek_result['metadatas'][i-1] if peek_result.get('metadatas') else {}
            embedding = peek_result['embeddings'][i-1] if peek_result.get('embeddings') else None
            
            print(f"\n   [{i}] ID: {doc_id}")
            print(f"       Text: {doc_text[:100]}...")
            print(f"       Metadata: {json.dumps(metadata, indent=14)}")
            if embedding:
                print(f"       Embedding dim: {len(embedding)}, first 3 values: {embedding[:3]}")
    
    # Test similarity search
    print(f"\n🔎 Testing Similarity Search:")
    test_query = "incident severity levels"
    print(f"   Query: '{test_query}'")
    
    # Generate embedding for query
    from incident_iq.rag.tools.services.llm_service import LLMService
    import os
    
    config_dir = os.path.join(os.path.dirname(__file__), "..", "src", "incident_iq", "rag", "config")
    llm_config_path = os.path.join(config_dir, "llm_config.json")
    
    with open(llm_config_path, "r") as f:
        llm_config = json.load(f)
    
    llm_service = LLMService(llm_config)
    query_embedding = llm_service.generate_embedding(test_query)
    
    # Search
    search_result = vdb.search(query_embedding, top_k=3)
    
    print(f"\n   Top 3 results:")
    if search_result.get('ids') and search_result['ids'][0]:
        for i, doc_id in enumerate(search_result['ids'][0], 1):
            distance = search_result['distances'][0][i-1] if search_result.get('distances') else 0
            doc = search_result['documents'][0][i-1] if search_result.get('documents') else "N/A"
            metadata = search_result['metadatas'][0][i-1] if search_result.get('metadatas') else {}
            
            print(f"\n   [{i}] ID: {doc_id}")
            print(f"       Distance: {distance:.4f}")
            print(f"       Text: {doc[:100]}...")
            print(f"       Metadata: {json.dumps(metadata, indent=15)}")
    else:
        print("   No results found")
    
    print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    inspect_chromadb()
