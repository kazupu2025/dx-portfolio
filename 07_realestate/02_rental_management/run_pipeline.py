"""
B-14 パイプライン実行スクリプト
cleanse -> validate -> analyze -> validate_report -> visualize
"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "output"
PYTHON = "C:/Users/realp/miniconda3/python.exe"

steps = [
    ("cleanse",          OUT / "cleanse.py"),
    ("validate",         OUT / "validate.py"),
    ("analyze",          OUT / "analyze.py"),
    ("validate_report",  OUT / "validate_report.py"),
    ("visualize",        OUT / "visualize.py"),
]

def run(label, script):
    print(f"\n{'='*50}")
    print(f"STEP: {label}")
    print(f"{'='*50}")
    result = subprocess.run(
        [PYTHON, str(script)],
        cwd=str(BASE / "output"),
    )
    if result.returncode != 0:
        print(f"ERROR: {label} failed with code {result.returncode}")
        sys.exit(result.returncode)
    print(f"OK: {label}")

if __name__ == "__main__":
    for label, script in steps:
        run(label, script)
    print("\nPipeline complete!")
