#!/usr/bin/env python
"""
Simple test to verify classifier outputs processor works correctly.
"""

import sys
from pathlib import Path

# Setup path
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

print("=" * 80)
print("Testing Corrective Action Processor")
print("=" * 80)

try:
    # Test imports
    print("\n✓ Testing imports...")
    from incident_iq.database.models.classifier_output import ClassifierOutputsModel
    from incident_iq.rag.agents.master_orchestrator import MasterOrchestrator
    print("  ✓ All imports successful")
    
    # Test processor initialization
    print("\n✓ Initializing processor...")
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from process_classifier_outputs import CorrectiveActionProcessor
    
    processor = CorrectiveActionProcessor()
    print("  ✓ Processor initialized successfully")
    
    # Test fetching records
    print("\n✓ Fetching sample records...")
    records = processor.fetch_unprocessed_records(limit=2)
    print(f"  ✓ Found {len(records)} unprocessed records")
    
    if records:
        print("\n  Sample records:")
        for i, rec in enumerate(records, 1):
            print(f"    {i}. ID={rec.get('id')}, Payload={rec.get('payload_id')}, Severity={rec.get('severity_id')}")
    
    processor.close()
    
    print("\n" + "=" * 80)
    print("✅ All tests passed! Processor is ready to use.")
    print("=" * 80)
    print("\nRun the full processor with:")
    print("  python scripts/process_classifier_outputs.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
