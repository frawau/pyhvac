"""A released model never goes away: every brand/model pair pyhvac has
served keeps resolving and encoding (consumers such as the IR HVAC Home
Assistant integration store these names).

A rename keeps the old name in ``brands.ALIASES``. At each release, add the
new pairs to the fixture:

    python -c "import json; from pyhvac import registry; \
print(json.dumps(sorted([b, m] for b in registry.brands() \
for m in registry.models(b)), indent=1))" > tests/fixtures/released_models.json

(only ever adding pairs: never remove one from the fixture).
"""

import json
from pathlib import Path

import pytest

from pyhvac import registry
from pyhvac.state import HvacState

RELEASED = json.loads(
    (Path(__file__).parent / "fixtures" / "released_models.json").read_text()
)


def test_fixture_holds_the_0_2_0_catalogue():
    assert len(RELEASED) >= 689
    assert ["AEG", "Chillflex Pro AXP26U558HW"] in RELEASED


@pytest.mark.parametrize("brand,model", RELEASED)
def test_released_model_still_works(brand, model):
    device = registry.get_device(brand, model)
    caps = device.capabilities
    device.encode(None, HvacState(True, caps.modes[0], caps.temperature.min))
