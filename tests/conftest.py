import sys
from pathlib import Path

import pytest

# tools/ holds portkit and the smartir importer, which tests import.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))


def pytest_addoption(parser):
    parser.addoption(
        "--network",
        action="store_true",
        help="run the tests that fetch from the internet",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--network"):
        return
    skip = pytest.mark.skip(reason="needs --network")
    for item in items:
        if "network" in item.keywords:
            item.add_marker(skip)
