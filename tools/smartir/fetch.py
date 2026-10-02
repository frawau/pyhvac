"""Upstream SmartIR climate code files into a local cache (never committed)."""

import io
import zipfile
from pathlib import Path

from pyhvac.protocols import table

ARCHIVE = "https://codeload.github.com/smartHomeHub/SmartIR/zip/refs/heads/master"
PREFIX = "codes/climate/"


def default_dir():
    return table.cache_dir() / "smartir-upstream" / "climate"


def fetch(dest=None, url=ARCHIVE, get=None):
    """Download upstream master and write its ``codes/climate/<n>.json``
    files to ``dest``; returns the directory. ``get(url) -> bytes`` defaults
    to pyhvac.protocols.table.fetch."""
    dest = Path(dest or default_dir())
    dest.mkdir(parents=True, exist_ok=True)
    archive = zipfile.ZipFile(io.BytesIO((get or table.fetch)(url)))
    for name in archive.namelist():
        _, _, path = name.partition("/")  # drop the "SmartIR-master/" root
        if path.startswith(PREFIX) and path.endswith(".json"):
            leaf = path[len(PREFIX) :]
            if "/" not in leaf:
                (dest / leaf).write_bytes(archive.read(name))
    return dest


def files(directory):
    """The cached files, by file number."""
    found = []
    for p in Path(directory).glob("*.json"):
        if p.stem.isdigit():
            found.append(p)
    return sorted(found, key=lambda p: int(p.stem))
