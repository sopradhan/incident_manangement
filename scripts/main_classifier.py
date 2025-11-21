#!/usr/bin/env python
"""
Wrapper script to run main classifier from scripts folder.
Executes the actual classifier located in src/incident_iq/ml_model/scripts/
"""
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    # Get the path to the actual classifier script
    project_root = Path(__file__).resolve().parent.parent
    actual_classifier_script = project_root / "src" / "incident_iq" / "ml_model" / "scripts" / "main_classifier.py"
    
    print("=" * 80)
    print("INCIDENT CLASSIFIER")
    print(f"Script: {actual_classifier_script}")
    print("=" * 80)
    
    # Execute the actual classifier script
    result = subprocess.run(
        [sys.executable, str(actual_classifier_script)],
        cwd=str(project_root)
    )
    
    sys.exit(result.returncode)
