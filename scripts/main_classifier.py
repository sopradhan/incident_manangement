import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent

    print("=" * 80)
    print("INCIDENT CLASSIFIER")
    print("=" * 80)

    # Execute the actual classifier script
    result = subprocess.run(
        [sys.executable, str(actual_classifier_script)],
        cwd=str(project_root)
    )

    sys.exit(result.returncode)
