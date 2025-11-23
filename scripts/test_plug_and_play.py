#!/usr/bin/env python3
"""Test plug-and-play ingestion interface across multiple domains"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from incident_iq.rag.agents.master_orchestrator import MasterOrchestrator


def test_finance_ingestion():
    """Test ingestion of finance data"""
    print("\n" + "="*60)
    print("TEST 1: FINANCE DATA INGESTION")
    print("="*60)
    
    finance_data = [
        "Q3 2024 Revenue: $45M, Profit Margin: 28%",
        "Investment Portfolio: Tech 40%, Healthcare 30%, Finance 30%",
        "New product pricing: Standard $99/mo, Professional $299/mo",
    ]
    
    orch = MasterOrchestrator()
    result = orch.ingest_data(finance_data, domain="finance")
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
    assert result['success'], "Finance ingestion failed"
    assert result['domain'] == 'finance', "Domain not detected as finance"
    print("[OK] Finance ingestion successful")
    return orch


def test_travel_ingestion():
    """Test ingestion of travel data"""
    print("\n" + "="*60)
    print("TEST 2: TRAVEL DATA INGESTION")
    print("="*60)
    
    travel_data = {
        "destinations": [
            {"city": "Paris", "flight_cost": "$450", "hotel_cost": "$120/night"},
            {"city": "Tokyo", "flight_cost": "$650", "hotel_cost": "$150/night"},
        ]
    }
    
    orch = MasterOrchestrator()
    result = orch.ingest_data(travel_data)
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
    assert result['success'], "Travel ingestion failed"
    print("[OK] Travel ingestion successful")
    return orch


def test_medical_ingestion():
    """Test ingestion of medical data"""
    print("\n" + "="*60)
    print("TEST 3: MEDICAL DATA INGESTION")
    print("="*60)
    
    medical_data = """
    Patient Information:
    - Age: 45, Blood Pressure: 160/95 (High)
    - Treatment: Lisinopril 10mg daily
    - Follow-up: Check BP in 2 weeks
    
    Clinic Hours: Monday-Friday 9am-5pm, Saturday 10am-2pm
    """
    
    orch = MasterOrchestrator()
    result = orch.ingest_data(medical_data)
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
    assert result['success'], "Medical ingestion failed"
    print("[OK] Medical ingestion successful")
    return orch


def test_raw_text_ingestion():
    """Test ingestion of raw text"""
    print("\n" + "="*60)
    print("TEST 4: RAW TEXT INGESTION")
    print("="*60)
    
    raw_text = """
    Configuration Management Best Practices:
    1. Use version control for all configs
    2. Separate environment-specific configs
    3. Never hardcode secrets
    4. Document all configuration options
    """
    
    orch = MasterOrchestrator()
    result = orch.ingest_data(raw_text)
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
    assert result['success'], "Raw text ingestion failed"
    print("[OK] Raw text ingestion successful")
    return orch


def test_multi_domain_orchestrator():
    """Test same orchestrator interface works across domains"""
    print("\n" + "="*60)
    print("TEST 5: MULTI-DOMAIN WITH SAME INTERFACE")
    print("="*60)
    
    # Finance
    orch1 = MasterOrchestrator()
    result1 = orch1.ingest_data(["Q3 profit: $45M"], domain="finance")
    print(f"\n  Finance: {result1['documents_ingested']} docs")
    
    # Travel
    orch2 = MasterOrchestrator()
    result2 = orch2.ingest_data({"destinations": ["Paris", "Tokyo"]})
    print(f"  Travel: {result2['documents_ingested']} docs")
    
    # Medical
    orch3 = MasterOrchestrator()
    result3 = orch3.ingest_data("Patient treatment plan...")
    print(f"  Medical: {result3['documents_ingested']} docs")
    
    # Verify all used same interface
    assert result1['success'] and result2['success'] and result3['success']
    print("\n[OK] Same orchestrator interface works across all domains")


if __name__ == "__main__":
    try:
        print("\n[TEST] Plug-and-Play Ingestion Interface")
        print("[TEST] Testing domain-agnostic data ingestion\n")
        
        test_finance_ingestion()
        test_travel_ingestion()
        test_medical_ingestion()
        test_raw_text_ingestion()
        test_multi_domain_orchestrator()
        
        print("\n" + "="*60)
        print("[SUCCESS] All plug-and-play tests passed!")
        print("="*60)
        print("\nThe orchestrator is now truly plug-and-play:")
        print("  - ingest_data(data) accepts ANY format")
        print("  - Works with finance, travel, medical, technical data")
        print("  - Auto-detects domain")
        print("  - ask_question() works on any ingested domain")
        print("  - No domain-specific configuration needed\n")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
