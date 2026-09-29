import sys
from pathlib import Path

# tools/ holds helpers shared by the fixture generators and the tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))


def pytest_sessionfinish(session, exitstatus):
    # c_oracle record mode (PYHVAC_FREEZE=1): write what the C path sent.
    import c_oracle

    if c_oracle.RECORDING:
        c_oracle.write_fixtures()
