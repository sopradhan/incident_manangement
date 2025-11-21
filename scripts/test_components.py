#!/usr/bin/env python
"""
Wrapper script to run component tests from scripts folder.
Executes the actual test suite located in src/incident_iq/ml_model/scripts/
"""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    # Get the path to the actual test script
    project_root = Path(__file__).resolve().parent.parent
    actual_test_script = project_root / "src" / "incident_iq" / "ml_model" / "scripts" / "test_components.py"
    
    print("=" * 80)
    print("RUNNING COMPONENT VALIDATION TEST SUITE")
    print(f"Test Script: {actual_test_script}")
    print("=" * 80)
    
    # Execute the actual test script
    result = subprocess.run(
        [sys.executable, str(actual_test_script)],
        cwd=str(project_root)
    )
    
    sys.exit(result.returncode)
