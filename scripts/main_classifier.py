import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    actual_classifier_script = project_root / "src" / "incident_iq" / "ml_model" / "scripts" / "main_classifier.py"


    # Execute the actual classifier script
    result = subprocess.run(
        [sys.executable, str(actual_classifier_script)],
        cwd=str(project_root)
    )

    sys.exit(result.returncode)
