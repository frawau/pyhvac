import sys
from pathlib import Path

# tools/ holds portkit and the hvacir importer, which tests import.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
