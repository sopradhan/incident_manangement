"""
Test script to validate all components independently.
Run this before main_classifier.py to verify setup.
"""

import json
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path)

# Add src directory to Python path so incident_iq imports work
src_path = Path(__file__).resolve().parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Add scripts directory to path for local imports
scripts_path = Path(__file__).resolve().parent
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))

DB_NAME = os.getenv("DB_NAME", "incident_iq.db")

DB_PATH = Path(__file__).resolve().parent.parent.parent / "database" / "data" / DB_NAME
MODEL_DIR_PATH = Path(__file__).resolve().parent.parent / "bert" 

# Setup basic logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)


def test_database_operations():
    """Test database operations."""
    print("\n" + "=" * 80)
    print("TEST 1: Database Operations")
    print("=" * 80)
    
    try:
        from database_operations import DatabaseOperations
        

        print("→ Initializing database operations...")
        db_ops = DatabaseOperations(DB_PATH)
        print("  ✓ Database connection established")
        
        # Test loading rules
        print("→ Loading severity rules...")
        rules = db_ops.load_severity_rules()
        print(f"  ✓ Loaded {len(rules)} severity rules")
        
        if rules:
            pattern, severity, score, category, desc, env = rules[0]
            print(f"  Sample rule: '{pattern}' -> {severity} (score: {score})")
        
        # Test getting unprocessed incidents
        print("→ Fetching unprocessed incidents...")
        incidents = db_ops.get_unprocessed_incidents(limit=5)
        print(f"  ✓ Fetched {len(incidents)} unprocessed incidents (limit: 5)")
        
        # Test getting statistics
        print("→ Fetching severity statistics...")
        stats = db_ops.get_severity_statistics()
        print(f"  ✓ Severity statistics: {stats}")
        
        print("\n✓ Database operations test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Database operations test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_bert_embedder():
    """Test BERT embedder."""
    print("\n" + "=" * 80)
    print("TEST 2: BERT Embedder")
    print("=" * 80)
    
    try:
        from bert_embedder import BertEmbedder
        
        print("→ Initializing BERT embedder...")
        embedder = BertEmbedder(MODEL_DIR_PATH)
        print(f"  ✓ BERT embedder initialized")
        print(f"  Device: {embedder.device}")
        print(f"  Hidden size: {embedder.hidden_size}")
        
        # Test single encoding
        print("\n→ Testing single text encoding...")
        test_text = "database connection timeout error"
        embedding = embedder.encode(test_text)
        print(f"  ✓ Encoded: '{test_text}'")
        print(f"  Embedding shape: {embedding.shape}")
        print(f"  Embedding preview: [{embedding[0]:.4f}, {embedding[1]:.4f}, ..., {embedding[-1]:.4f}]")
        
        # Test multiple encodings
        print("\n→ Testing multiple text encodings...")
        texts = [
            "api call failed with status 500",
            "high cpu utilization detected",
            "network connectivity issues"
        ]
        
        for text in texts:
            emb = embedder.encode(text)
            print(f"  ✓ Encoded: '{text}' -> shape {emb.shape}")
        
        # Test batch encoding
        print("\n→ Testing batch encoding...")
        batch_embeddings = embedder.encode_batch(texts)
        print(f"  ✓ Batch encoded {len(texts)} texts")
        print(f"  Batch shape: {batch_embeddings.shape}")
        
        print("\n✓ BERT embedder test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ BERT embedder test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_resource_extractor():
    """Test resource ID extraction."""
    print("\n" + "=" * 80)
    print("TEST 3: Resource Extractor")
    print("=" * 80)
    
    test_cases = [
        "/subscriptions/12345-abcde/resourceGroups/prod-rg-eastus/providers/Microsoft.Storage/storageAccounts/prodstg001",
        "/subscriptions/67890-fghij/resourceGroups/uat-rg-westus/providers/Microsoft.Sql/servers/databases/uatdb001",
        "/subscriptions/abcdef-12345/resourceGroups/dev-rg/providers/Microsoft.Web/sites/devapp"
    ]
    
    try:
        from resource_extractor import ResourceExtractor
        
        print("→ Testing resource ID parsing...")
        
        for i, resource_id in enumerate(test_cases, 1):
            print(f"\nTest case {i}:")
            print(f"  Resource ID: {resource_id}")
            
            sub_id, rg, res_type, res_name = ResourceExtractor.extract_resource_fields(resource_id)
            
            print(f"  ✓ Subscription:    {sub_id}")
            print(f"  ✓ Resource Group:  {rg}")
            print(f"  ✓ Resource Type:   {res_type}")
            print(f"  ✓ Resource Name:   {res_name}")
            
            # Test display name
            display_name = ResourceExtractor.get_resource_display_name(sub_id, rg, res_type, res_name)
            print(f"  Display name:      {display_name}")
            
            # Test production check
            is_prod = ResourceExtractor.is_production_resource(resource_id, rg, sub_id)
            print(f"  Is production:     {is_prod}")
        
        print("\n✓ Resource extractor test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Resource extractor test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_severity_engine():
    """Test severity engine."""
    print("\n" + "=" * 80)
    print("TEST 4: Severity Engine")
    print("=" * 80)
    
  
    try:
        from database_operations import DatabaseOperations
        from bert_embedder import BertEmbedder
        from severity_engine import SeverityEngine
        
        print("→ Initializing components...")
        db_ops = DatabaseOperations(DB_PATH)
        embedder = BertEmbedder(MODEL_DIR_PATH)
        engine = SeverityEngine(db_ops, embedder)
        
        print(f"  ✓ Severity engine initialized with {len(engine.pattern_info)} patterns")
        print(f"  Similarity threshold: {engine.similarity_threshold}")
        
        # Test incident analysis with various scenarios
        test_incidents = [
            {
                "name": "Database Timeout (Production)",
                "data": {
                    "operationName": {"value": "DatabaseConnect"},
                    "status": {"value": "Failed"},
                    "properties": {
                        "error": {
                            "message": "database connection timeout",
                            "code": "CONN_TIMEOUT"
                        },
                        "environment": "prod"
                    },
                    "resourceId": "/subscriptions/12345/resourceGroups/prod-rg/providers/Microsoft.Sql/servers/databases/proddb"
                }
            },
            {
                "name": "API Error (UAT)",
                "data": {
                    "operationName": {"value": "ApiCall"},
                    "status": {"value": "Failed"},
                    "properties": {
                        "error": {
                            "message": "api call failed with status 500",
                            "code": "HTTP_500"
                        },
                        "environment": "uat"
                    }
                }
            },
            {
                "name": "High CPU (Dev)",
                "data": {
                    "metricName": "CpuPercentage",
                    "properties": {
                        "environment": "dev"
                    },
                    "category": "Metric",
                    "status": {"value": "Warning"}
                }
            }
        ]
        
        print("\n→ Testing incident analysis...")
        
        for test in test_incidents:
            print(f"\n  Test: {test['name']}")
            print(f"  " + "-" * 60)
            
            result = engine.analyze_incident(test['data'])
            
            print(f"    Severity:        {result['severity_level']}")
            print(f"    BERT Score:      {result['bert_score']:.4f}")
            print(f"    Rule Score:      {result['rule_score']:.2f}")
            print(f"    Combined Score:  {result['combined_score']:.2f}")
            print(f"    Matched Pattern: {result['matched_pattern']}")
            print(f"    Environment:     {result['environment']}")
            
            if result['all_matches']:
                print(f"    Top matches:")
                for i, match in enumerate(result['all_matches'][:3], 1):
                    print(f"      {i}. '{match['pattern']}' (similarity: {match['similarity']:.4f})")
        
        print("\n✓ Severity engine test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Severity engine test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_incident_processor():
    """Test incident processor initialization."""
    print("TEST Incident Processor")
    
    try:
        from incident_processor import IncidentProcessor
        
        print("→ Initializing incident processor...")
        processor = IncidentProcessor(db_path=DB_PATH, model_dir=MODEL_DIR_PATH)
        
        print("  ✓ Incident processor initialized")
        print(f"  ML models loaded: {processor.scaler is not None and processor.classifier is not None}")
        
        # Test statistics
        print("\n→ Getting current statistics...")
        stats = processor.get_statistics()
        
        print(f"  ✓ Total processed: {stats['total_processed']}")
        print("  Severity distribution:")
        for severity, count in sorted(stats['severity_distribution'].items()):
            pct = stats['percentages'].get(severity, 0)
            print(f"    {severity}: {count} ({pct:.1f}%)")
        
        print("\n✓ Incident processor test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Incident processor test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all component tests."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "COMPONENT TEST SUITE" + " " * 38 + "║")
    print("╚" + "=" * 78 + "╝")
    
    results = {
        "Database Operations": test_database_operations(),
        "BERT Embedder": test_bert_embedder(),
        "Resource Extractor": test_resource_extractor(),
        "Severity Engine": test_severity_engine(),
        "Incident Processor": test_incident_processor()
    }
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for component, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {component:<30} {status}")
    
    all_passed = all(results.values())
    
    print("=" * 80)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("\nYou can now run: python main_classifier.py")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nPlease fix the failing components before running main_classifier.py")
        print("Check the error messages above for details.")
    
    print("\n" + "=" * 80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)