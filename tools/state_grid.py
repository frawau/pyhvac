"""Deterministic grids of device states for golden and oracle fixtures."""

import itertools

# Pure-Python classes covered by golden fixtures: module -> class names.
# The generic Sharp class is left out: its build_ircode() raises KeyError.
NATIVE = {
    "airspool": ["Airspool"],
    "sharp": ["JTech"],
    "daikin": ["Daikinth", "Smash2"],
    "panasonic": ["Panasonic", "PanaCassette"],
    "lg": ["LG", "InverterV", "DualInverter"],
}


def _temperatures(values):
    """min, middle, max of a temperature capability.

    Pure-Python plugins list every value; C-backed ones give [min, max].
    """
    values = list(values)
    lo, hi = values[0], values[-1]
    mid = values[len(values) // 2] if len(values) > 2 else (lo + hi) // 2
    return sorted({lo, mid, hi})


def state_grid(capabilities, extra=None, limit=200):
    """States covering mode x temperature x fan x swing, plus each other
    capability set once to each non-default value, at most ``limit`` in all."""
    caps = dict(capabilities)
    caps.update(extra or {})
    temps = _temperatures(caps["temperature"])
    axes = [("mode", list(caps["mode"])), ("temperature", temps)]
    for key in ("fan", "swing"):
        if key in caps:
            axes.append((key, list(caps[key])))
    names = [name for name, _ in axes]

    active = next((m for m in caps["mode"] if m != "off"), caps["mode"][0])
    base = {"mode": active, "temperature": temps[len(temps) // 2]}
    extras = []
    for key, values in caps.items():
        if key in names:
            continue
        for value in list(values)[1:]:
            extras.append({**base, key: value})

    main = [
        dict(zip(names, combo)) for combo in itertools.product(*(v for _, v in axes))
    ]
    room = max(limit - len(extras), 1)
    if len(main) > room:
        step = len(main) / room
        main = [main[int(i * step)] for i in range(room)]
    return (main + extras)[:limit]


def build_native(cls, state):
    """Fresh device with ``state`` applied (mode last) and its frames."""
    dev = cls()
    for key, value in state.items():
        if key != "mode":
            dev.set_value(key, value)
    dev.set_value("mode", state["mode"])
    return dev, dev.build_ircode()
