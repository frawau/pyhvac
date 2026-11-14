# Native Daikin / Sharp generic: capabilities old -> new

Line numbers are in `pyhvac/plugins/daikin.py` / `pyhvac/plugins/sharp.py` of
the scratch copy (legacy class code, unchanged).

## DaikinNativeDevice (daikin:generic = Daikinth, daikin:smash 2 = Smash2)

One Device, no variant: the two legacy classes share every line of code;
they differ only in the capability table (Smash2 adds fan/swing/powerful),
and under full control both get what the shared code encodes.

| Control | Old: Daikinth (generic) | Old: Smash2 | New (both models) | Source |
|---|---|---|---|---|
| modes | off, cool, fan, dry | off, cool, fan, dry | power + cool, fan, dry, **heat, auto** | tables daikin.py:66, 263; code_mode daikin.py:207-217 encodes dry 0x84, fan 0x86, heat 0x82, auto 0x80, cool 0x8C |
| setpoint | 18-31, step 1 | 18-31, step 1 | 18-31 °C, step 1 | daikin.py:67, 264; code_temperature daikin.py:90 (`bit_reverse(temp*2)`) |
| fan | none (always sends auto 0x05) | auto, highest, high, medium, low, lowest | `FAN_5`: auto, 1 lowest, 2 low, 3 medium, 4 high, 5 highest (**new for generic**) | daikin.py:265; code_fan daikin.py:109-116 |
| swing_v | none (always off) | off, on | `SWING`: off, swing ("on") (**new for generic**) | daikin.py:266; code_swing daikin.py:136-139 |
| swing_h | none | none | none | - |
| powerful | none | off, on (never sent: bug) | `ON_OFF` feature, byte 13 0x80 (**now sent**; new for generic) | daikin.py:267; code_powerful daikin.py:161-162 |
| comfort | xtra only, never offered, code_comfort returns [] | same | absent (no encoding exists) | daikin.py:165-177 |

Rules kept from the legacy code: fan mode sends 25 °C on the wire
(daikin.py:86, 183), dry sends byte 6 = 0x03 (daikin.py:209), off clears the
power bit, keeps the mode nibble and sets byte 16 = 0x02 (daikin.py:193-205).

Removed no-ops: none (nothing offered was a no-op; powerful was a no-op by
bug and is now fixed, not removed).

Skipped golden records (1 of 157 daikin records):

| Record | Why |
|---|---|
| Smash2 `{mode: cool, temperature: 25, powerful: on}` | `code_powerful` compares the string "on" with `True` (daikin.py:161), so powerful was never sent; the intent (`mask[13] = 0x80`) is encoded instead. |

All other 156 records (12 Daikinth, 144 Smash2) are reproduced byte for byte
(pulses and Broadlink).

## sharp:generic (Sharp) - not ported

No Device written; see REPORT.md. The generic Sharp class is a broken base of
JTech. Its own table: modes off/auto/cool/dry, 18-37 °C (sharp.py:73-74), no
fan/swing/features. Proposal: register `sharp:generic` as `JTechDevice` (or
drop it); no golden records exist for it.
