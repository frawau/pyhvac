# Capabilities: legacy entity -> Device (LG and Panasonic native)

Line numbers are in the patched `pyhvac/plugins/lg.py` / `panasonic.py`
(the legacy code itself is unchanged; lg.py gained one import line).

## LgNativeDevice (lg.py), one class, variant = model

### variant "generic" (legacy `LG`, model `generic`)

| capability | legacy (old) | new | source |
|---|---|---|---|
| modes | off, cool, fan, dry | power + (cool, fan, dry) | lg.py:78 `LG.__init__` |
| temperature | 18..29 step 1 | TemperatureRange(18, 29) | lg.py:79 |
| fan | none (code_fan sends auto 0x05) | None | lg.py:146 `code_fan` (no "fan" capability -> auto) |
| swing_v / swing_h | none | None | `xtra_capabilities = {}` |
| features / actions | none | none | |

### variant "inverter v" (legacy `InverterV`)

| capability | legacy (old) | new | source |
|---|---|---|---|
| modes | off, auto, cool, fan, dry | power + (auto, cool, fan, dry) | lg.py:422 |
| temperature | 16..29 | TemperatureRange(16, 29) | lg.py:423 |
| fan | auto, highest, high, medium, low, lowest | `choices.FAN_5` (auto, "1"=lowest .. "5"=highest); forced auto in auto mode | lg.py:425, code_fan lg.py:146 |
| swing_v | off, swing, 90°, 0° | off, swing, "1"=90°, "2"=0° | lg.py:428, code_swing lg.py:185 |
| auto_bias | -2, -1, default, +1, +2 | feature `auto_bias`, Choice(default, -2, -1, +1, +2) (default first = the feature default) | lg.py:424, code_temperature lg.py:96 |
| powerful | off, on | feature `powerful` ON_OFF | lg.py:429, code_powerful lg.py:249 |
| cleaning | off, on | feature `cleaning` ON_OFF | lg.py:430, code_cleaning lg.py:316 |
| economy | off, 80, 60, 40 | feature `economy`, Choice(off, 80, 60, 40) | lg.py:431, code_economy lg.py:293 |

### variant "dual inverter" (legacy `DualInverter`)

| capability | legacy (old) | new | source |
|---|---|---|---|
| modes | off, auto, cool, fan, dry | power + (auto, cool, fan, dry) | lg.py:450 |
| temperature | 16..29 | TemperatureRange(16, 29) | lg.py:451 |
| fan | auto, highest .. lowest | `choices.FAN_5`, forced auto in auto mode | lg.py:453 |
| swing_v | off, swing, ceiling, 90°, 60°, 45°, 30°, 0° | off, swing, "1"=ceiling, "2"=90°, "3"=60°, "4"=45°, "5"=30°, "6"=0° | lg.py:456 |
| swing_h | off, swing, left, centre left, centre, centre right, right, swing left, swing right | off, swing, "1"=left, "2"=centre left, "3"=centre, "4"=centre right, "5"=right, "6"=swing left, "7"=swing right | lg.py:457, code_hswing lg.py:216 |
| auto_bias | -2 .. +2 | feature `auto_bias` | lg.py:452 |
| powerful, purifier, cleaning | off, on | features ON_OFF | lg.py:468-470 |
| economy | off, 80, 60, 40 | feature `economy`, Choice(off, 80, 60, 40) | lg.py:471 |
| diagnostic | off, on (a state value) | **action** `diagnostic` (code_diagnostic: "It is a request, not a toggle") | lg.py:472, code_diagnostic lg.py:335 |

Behaviour change: swing_h now does something. The legacy DualInverter
never sent it (status lacks "hswing", see skipped records).

Not offered (encoded by the shared LG code, absent from every class
table; kept in LG_NATIVE_COMMANDS/LAYOUT, re-adding is a table entry):
heat (no code at all in code_mode, so not encodable), swing_v positions
ceiling/60°/45°/30° for "inverter v", swing_h for "inverter v".

Removed no-ops: none. Every value each class table offers changes the frames.

## PanasonicNativeDevice (panasonic.py), one class, variant = model

### variant "generic" (legacy `Panasonic`)

| capability | legacy (old) | new | source |
|---|---|---|---|
| modes | off, auto, cool, fan, dry | power + (auto, cool, fan, dry) | panasonic.py:90 |
| temperature | 16..31 | TemperatureRange(16, 31); fan mode sends 27 | panasonic.py:91, set_mode/code_temperature panasonic.py:107-124 |
| fan / swing | none (code_fan/code_swing send 0) | None | panasonic.py:153, 187 |
| features | none | none | |

### variant "4 way cassette" (legacy `PanaCassette`)

| capability | legacy (old) | new | source |
|---|---|---|---|
| modes | off, auto, cool, fan, dry | power + (auto, cool, fan, dry) | panasonic.py:334 |
| temperature | 16..31 | TemperatureRange(16, 31) | panasonic.py:335 |
| fan | auto, highest, medium, lowest | auto, "1"=lowest, "2"=medium, "3"=highest | panasonic.py:336, code_fan panasonic.py:153 |
| swing_v | auto, auto high, auto low, 90°, 60°, 45°, 30° | auto, "1"=90°, "2"=60°, "3"=45°, "4"=30°, "5"=auto high, "6"=auto low | panasonic.py:337, code_swing panasonic.py:187 |
| purifier | off, on | feature `purifier` ON_OFF | panasonic.py:338, code_purifier panasonic.py:247 |
| economy | off, on (toggle) | feature `economy` ON_OFF (toggle frame on change) | panasonic.py:341, code_economy panasonic.py:287 |
| cleaning | off, on (toggle) | feature `cleaning` ON_OFF (toggle frame on change) | panasonic.py:341, code_cleaning panasonic.py:271 |

Not offered (encoded by the shared Panasonic code, absent from both class
tables; kept in the PANASONIC_NATIVE_* tables): heat (code_mode 0x92),
fan high/low (0x06/0x02), swing ceiling (0x80), profile normal/boost/quiet
(code_profile 0x08/0x88/0x0c). Neither legacy class ever sent them.

Removed no-ops: none.

## Skipped golden records

| records | why |
|---|---|
| lg.json.gz DualInverter 397-404 (hswing swing, left, centre left, centre, centre right, right, swing left, swing right) | Evident legacy bug: `DualInverter.status` (lg.py:474-485) has no "hswing" key, so `set_hswing` (lg.py:213 `self.status["hswing"] != mode`) raised KeyError, which `HVAC.set_value` (hvaclib.py:81) swallowed: hswing was offered (lg.py:457) and has an encoder (code_hswing lg.py:216) but was never sent. The port sends the state frame plus the code_hswing frame (test_hswing_is_sent). |

No Panasonic record is skipped (215/215 reproduced).
