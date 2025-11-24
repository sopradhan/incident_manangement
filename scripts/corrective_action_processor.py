#!/usr/bin/env python
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    script_path = Path(__file__).resolve()
    
    # Run the actual processor
    result = subprocess.run(
        [sys.executable, str(script_path.parent / "process_classifier_outputs.py")],
        cwd=str(project_root)
    )
    
    sys.exit(result.returncode)
