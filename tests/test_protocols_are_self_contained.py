import ast
from pathlib import Path

LEGACY = {"Airspool", "Daikinth", "Smash2", "Panasonic", "PanaCassette"}
DEVICES = {
    "airspool.py": "AirspoolDevice",
    "daikin.py": "DaikinNativeDevice",
    "panasonic.py": "PanasonicNativeDevice",
}


def test_native_devices_do_not_read_legacy_classes():
    root = Path(__file__).resolve().parents[1] / "pyhvac" / "plugins"
    for name, device in DEVICES.items():
        tree = ast.parse((root / name).read_text())
        cls = next(
            n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == device
        )
        module_level = [
            n for n in tree.body if not isinstance(n, (ast.ClassDef, ast.FunctionDef))
        ]
        used = {
            n.id
            for part in [cls, *module_level]
            for n in ast.walk(part)
            if isinstance(n, ast.Name)
        }
        assert not used & LEGACY, (name, sorted(used & LEGACY))
