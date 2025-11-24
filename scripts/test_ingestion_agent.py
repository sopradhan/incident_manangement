#!/usr/bin/env python
"""Test IngestionAgent functionality"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from incident_iq.rag.agents.ingestion_agent import IngestionAgent
from incident_iq.rag.config.env_config import EnvConfig
from incident_iq.rag.tools.services.llm_service import LLMService
from incident_iq.rag.tools.services.vectordb_service import VectorDBService
from incident_iq.rag.config.loader import ConfigLoader


def test_ingestion_agent():
    print("=" * 60)
    print("INGESTION AGENT TEST")
    print("=" * 60)
    
    # Initialize services
    print("\n1. Initializing services...")
    try:
        ConfigLoader.set_config_dir(EnvConfig.get_rag_config_path())
        llm_service = LLMService(ConfigLoader.get_llm_config())
        vectordb_service = VectorDBService(EnvConfig.get_chroma_db_path())
        
        services = {
            'llm': llm_service,
            'vectordb': vectordb_service
        }
        print("   ✓ Services initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize services: {e}")
        return
    
    # Create IngestionAgent
    print("\n2. Creating IngestionAgent...")
    try:
        config = {
            'chunk_size': 500,
            'chunk_overlap': 50
        }
        agent = IngestionAgent(services, config)
        print(f"   ✓ Agent created: {agent.name}")
    except Exception as e:
        print(f"   ✗ Failed to create agent: {e}")
        return
    
    # Test 1: Ingest text data
    print("\n3. Test: Ingest text data")
    try:
        text_data = "This is a technical document about Python programming and API development."
        result = agent.ingest_data(text_data)
        print(f"   Success: {result.get('success')}")
        print(f"   Domain: {result.get('domain')}")
        print(f"   Documents ingested: {result.get('documents_ingested')}")
        print(f"   Metadata: {json.dumps(result.get('metadata'), indent=4)}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Ingest dictionary data
    print("\n4. Test: Ingest dictionary data")
    try:
        dict_data = {
            "title": "Medical Report",
            "type": "clinical_assessment",
            "content": "Patient diagnosis and treatment plan for cardiac condition",
            "date": "2024-01-15"
        }
        result = agent.ingest_data(dict_data)
        print(f"   Success: {result.get('success')}")
        print(f"   Domain: {result.get('domain')}")
        print(f"   Metadata: {json.dumps(result.get('metadata'), indent=4)}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Ingest list of mixed data
    print("\n5. Test: Ingest list of mixed data")
    try:
        list_data = [
            "Financial quarterly report with revenue and profit metrics",
            {
                "type": "balance_sheet",
                "assets": 1000000,
                "liabilities": 500000
            },
            "Legal contract terms and conditions"
        ]
        result = agent.ingest_data(list_data)
        print(f"   Success: {result.get('success')}")
        print(f"   Domain: {result.get('domain')}")
        print(f"   Documents ingested: {result.get('documents_ingested')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: Domain detection for different domains
    print("\n6. Test: Domain detection for different domains")
    domains_to_test = [
        ("This is a travel itinerary for a European vacation with hotel and flight bookings", "travel"),
        ("Legal agreement outlining terms and conditions of service", "legal"),
        ("Medical prescription for diabetes management and patient care", "medical"),
        ("Financial investment portfolio analysis and market trends", "finance"),
    ]
    
    for text, expected_domain in domains_to_test:
        try:
            result = agent._detect_domain([text])
            status = "✓" if result == expected_domain else "⚠"
            print(f"   {status} Expected: {expected_domain:10} | Got: {result}")
        except Exception as e:
            print(f"   ✗ Error detecting domain: {e}")
    
    # Test 5: Metadata extraction
    print("\n7. Test: Metadata extraction")
    try:
        docs = [
            "Technical documentation for REST API endpoints",
            "Configuration and setup guide"
        ]
        metadata = agent._extract_metadata(docs, "technical")
        print(f"   Document count: {metadata.get('document_count')}")
        print(f"   Total characters: {metadata.get('total_characters')}")
        print(f"   Domain: {metadata.get('domain')}")
        print(f"   Has URLs: {metadata.get('has_urls')}")
        print(f"   Has emails: {metadata.get('has_emails')}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    test_ingestion_agent()
