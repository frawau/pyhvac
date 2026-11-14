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


def test_a_pyhvac_console_script_is_declared():
    # 0.1.x installed gaccode, gcpanasonic, gcdaikin, gclg and gcsharp; 0.2.0
    # has one command, pyhvac, running pyhvac.__main__:main.
    from pathlib import Path
    import re

    text = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()
    scripts = re.search(r"\[project\.scripts\]\n(.*?)(?:\n\[|\Z)", text, re.S)
    assert scripts and re.search(
        r'^pyhvac\s*=\s*"pyhvac\.__main__:main"', scripts.group(1), re.M
    )


def run_raw(*args):
    return subprocess.run(
        [sys.executable, "-m", "pyhvac", *args], capture_output=True, text=True
    )


def test_bad_names_and_values_are_usage_errors_not_tracebacks():
    for args in (
        ("--list-models", "Nope"),
        ("Nope", "X"),
        ("Daikin",),  # several models, none given
        ("Daikin", "nope"),
        ("Daikin", "ARC433**", "--mode", "blah"),
    ):
        result = run_raw(*args)
        assert result.returncode == 2, args
        assert "Traceback" not in result.stderr and "error:" in result.stderr, args


def test_a_state_the_device_changes_is_reported():
    result = run_raw("Daikin", "ARC433**", "--temperature", "99", "--fan", "9")
    assert result.returncode == 0
    assert "sent" in result.stderr and "temperature" in result.stderr
    assert "fan" in result.stderr


def test_a_bare_feature_means_on():
    brand, model = "Daikin", "ARC433**"
    on = run("Daikin", model, "--feature", "powerful=on")
    assert run(brand, model, "--feature", "powerful") == on
