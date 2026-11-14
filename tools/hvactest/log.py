"""The optional session log: one JSON object per line, UTC timestamps."""

import datetime as dt
import json
from pathlib import Path


class SessionLog:
    """Appends events to ``path``; with ``path=None`` it writes nothing."""

    def __init__(self, path=None):
        self.path = Path(path).expanduser() if path else None

    @property
    def enabled(self):
        return self.path is not None

    def write(self, event, **data):
        if self.path is None:
            return None
        record = {
            "time": dt.datetime.now(dt.timezone.utc).isoformat(),
            "event": event,
            **data,
        }
        with self.path.open("a") as out:
            out.write(json.dumps(record, default=str) + "\n")
        return record
