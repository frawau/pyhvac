import base64
import subprocess
import sys

from pyhvac import registry
from pyhvac.ir.formats import to_broadlink
from pyhvac.state import HvacState


def run(*args):
    return subprocess.run(
        [sys.executable, "-m", "pyhvac", *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def test_lists_brands_and_models():
    assert "Daikin" in run("--list").splitlines()
    brand = "Daikin"
    assert run("--list-models", brand).splitlines() == registry.models(brand)


def test_broadlink_output_is_the_devices_command():
    brand = "Daikin"
    model = registry.models(brand)[0]
    dev = registry.get_device(brand, model)
    expected = to_broadlink(dev.encode(None, HvacState(True, "cool", 24.0)).signal)
    out = run(brand, model, "--mode", "cool", "--temperature", "24")
    assert base64.b64decode(out.strip()) == expected
