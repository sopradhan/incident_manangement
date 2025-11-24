#!/usr/bin/env python
"""Quick test of IngestionAgent - Test basic functionality"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test 1: Import check
print("Test 1: Checking imports...")
try:
    from incident_iq.rag.agents.ingestion_agent import IngestionAgent, TableIngestionConfig
    print("✓ IngestionAgent imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: TableIngestionConfig
print("\nTest 2: TableIngestionConfig methods...")
try:
    tables = TableIngestionConfig.load_sqlite_tables()
    print(f"✓ load_sqlite_tables(): {len(tables)} tables")
    
    chunking = TableIngestionConfig.get_chunking_config()
    print(f"✓ get_chunking_config(): {chunking}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: IngestionAgent initialization mock
print("\nTest 3: IngestionAgent class structure...")
try:
    methods = [m for m in dir(IngestionAgent) if not m.startswith('_') and callable(getattr(IngestionAgent, m))]
    print(f"✓ Public methods: {methods}")
    
    expected_methods = ['ingest_all_configured_tables', 'ingest_data', 'ingest_directory', 
                       'ingest_document', 'ingest_document_text', 'ingest_sqlite_table']
    missing = [m for m in expected_methods if m not in methods]
    if missing:
        print(f"⚠ Missing methods: {missing}")
    else:
        print("✓ All expected methods present")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Code syntax validation
print("\nTest 4: Code syntax check...")
try:
    import py_compile
    py_compile.compile(str(Path(__file__).parent.parent / "src/incident_iq/rag/agents/ingestion_agent.py"), doraise=True)
    print("✓ ingestion_agent.py syntax valid")
except Exception as e:
    print(f"✗ Syntax error: {e}")

print("\n" + "="*50)
print("QUICK TEST COMPLETED")
print("="*50)
