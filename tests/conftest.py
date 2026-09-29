import sys
from pathlib import Path

# tools/ holds portkit, which tests/test_portkit.py imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
