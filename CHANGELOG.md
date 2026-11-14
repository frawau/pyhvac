# Changelog

## 0.2.0

Breaking: new API, pure Python.

- No C extension: the IRremoteESP8266 protocols are ported to Python and
  verified against recordings of what 0.1.7 sent; wheels are py3-none-any.
- New API: `registry`, `HvacState`, `Device.encode(previous, target,
  actions)` -> `Command`; Broadlink, Pronto and raw output; decoding. The
  plugin API (`PluginObject`, `set_value`, `build_ircode`, `to_broadlink` on
  the device) is gone. See "Migrating from 0.1.x" in the README.
- One command, `pyhvac` (also `python -m pyhvac`), replaces the 0.1.x
  scripts `gaccode`, `gcpanasonic`, `gcdaikin`, `gclg` and `gcsharp`.
- Names: brands and models as the manufacturers write them; 0.1.x names
  still resolve for the former pure-Python devices (Daikin, LG and Panasonic
  "generic" and their variants, Airspool, Sharp "j-tech").
- Capabilities: full control of what each protocol documents (setpoint
  ranges and steps, fan levels, swing positions, features); controls that did
  nothing are removed.
- Output changes on purpose where 0.1.x sent wrong or undocumented codes,
  for example: swing "on" never reached the C library; Airwell never sent a
  valid state; Ecoclim always sent Sleep; Eurom always had sleep on; Daikin
  "smash 2" never sent powerful.
- Removed: Hitachi "PC-LH3B" and "generic 3" (HITACHI_AC3: 0.1.x sent
  nothing for them); Sharp "generic" (it never produced a valid command).
- More models: 121 brands and 689 models and remotes (82 brands and 404
  rows before the SmartIR import), mostly from the SmartIR community's
  learned climate codes. A SmartIR file becomes a pyhvac row only when a
  pyhvac protocol generates its codes; pyhvac ships and fetches no SmartIR
  data.
- AEG Chillflex Pro AXP26U558HW (verified on a unit by ha-aeg-infrared)
  and AXP34U338CW, both Electra like the AXP26U338CW.
- New protocol variants found in those captures: Coolix 16C and quiet;
  Electra aux (AUX-family remotes); Gree YAW1F-wifi, YAW1F-0 and YX1FSF-H;
  Kelon dry-grade and 16C; Midea RG57 and RG57-F (whole °F on the wire);
  Panasonic JKE-M13 and RKR-81; Mitsubishi A/C remote; TCL112 GZ055BE1-R,
  TAC09CHSD-R/-RH and TAC09CHSD-X03/X80/X83/XC0. Mitsubishi112 i-feel was
  learned from a unit.
- An unknown brand's error suggests the closest names.
- The sdist holds the package only (no tests, tools or docs).
