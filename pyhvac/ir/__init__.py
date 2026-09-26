"""Pure-Python IR physical layer: timings, bit encodings, encode/decode."""

from .model import (  # noqa: F401
    BitEncoding,
    Frame,
    Manchester,
    Protocol,
    PulseDistance,
    PulseWidth,
    Section,
    Signal,
)

from .codec import encode  # noqa: F401
