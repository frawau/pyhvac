"""Names for Broadlink devices, kept in ~/.pyhvacrc.

The file is a JSON object; the names live under "broadlink_names", a map
from MAC address (lower case, colon separated) to name. Other keys are kept
as they are.
"""

import json
import os
from pathlib import Path

DEFAULT_PATH = Path("~/.pyhvacrc").expanduser()
KEY = "broadlink_names"


def _mac(mac):
    return mac.strip().lower().replace("-", ":")


def load(path=DEFAULT_PATH):
    """(names, error): the MAC -> name map and None, or ({}, a message) when
    the file cannot be read or is not a JSON object."""
    path = Path(path)
    if not path.exists():
        return {}, None
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        return {}, f"cannot read {path}: {exc}"
    if not isinstance(data, dict) or not isinstance(data.get(KEY, {}), dict):
        return {}, f"{path} is not a JSON object with a {KEY!r} map"
    return {_mac(m): str(n) for m, n in data.get(KEY, {}).items()}, None


def rename(mac, name, path=DEFAULT_PATH):
    """Name the device ``mac`` (an empty name removes it) and write the file
    atomically, keeping its other keys (a file that cannot be read is
    replaced)."""
    path = Path(path)
    try:
        data = json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError):
        data = {}
    names = data.get(KEY) if isinstance(data.get(KEY), dict) else {}
    names = {_mac(m): n for m, n in names.items()}
    if name.strip():
        names[_mac(mac)] = name.strip()
    else:
        names.pop(_mac(mac), None)
    data[KEY] = names
    partial = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    partial.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    partial.replace(path)
    return names
