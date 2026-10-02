"""A SmartIR climate code file as keys and µs pulses.

The reading of stored codes is shared with pyhvac.protocols.table, which
serves such files at runtime.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple

from pyhvac.protocols.table import Key, UnsupportedFormat, to_pulses, walk

__all__ = ["Code", "Key", "SmartIRFile", "UnsupportedFormat", "parse", "to_pulses"]


@dataclass(frozen=True)
class Code:
    key: Key
    pulses: Tuple[int, ...]


@dataclass(frozen=True)
class SmartIRFile:
    number: int
    manufacturer: str
    models: Tuple[str, ...]
    controller: str
    encoding: str
    min_temperature: Optional[float]
    max_temperature: Optional[float]
    precision: Optional[float]
    modes: Tuple[str, ...]
    fans: Tuple[str, ...]
    swings: Tuple[str, ...]
    codes: Tuple[Code, ...] = field(repr=False)
    skipped: int  # codes that could not be turned into pulses
    unsupported: Optional[str] = None  # why no code could be read at all


def parse(number, data):
    controller = data.get("supportedController", "")
    encoding = data.get("commandsEncoding", "")
    codes, skipped, unsupported = [], 0, None
    for key, stored in walk(data.get("commands", {}), data.get("swingModes", ())):
        try:
            codes.append(Code(key, tuple(to_pulses(stored, controller, encoding))))
        except UnsupportedFormat as exc:
            unsupported = str(exc)
            skipped += 1
        except (ValueError, TypeError):
            skipped += 1
    return SmartIRFile(
        number=number,
        manufacturer=data.get("manufacturer", ""),
        models=tuple(data.get("supportedModels", ())),
        controller=controller,
        encoding=encoding,
        min_temperature=data.get("minTemperature"),
        max_temperature=data.get("maxTemperature"),
        precision=data.get("precision"),
        modes=tuple(data.get("operationModes", ())),
        fans=tuple(data.get("fanModes", ())),
        swings=tuple(data.get("swingModes", ())),
        codes=tuple(codes),
        skipped=skipped,
        unsupported=unsupported if not codes else None,
    )
