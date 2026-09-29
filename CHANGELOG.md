# Changelog

## 0.2.0

Breaking: new API, pure Python.

- No C extension: the IRremoteESP8266 protocols are ported to Python and
  verified against recordings of what 0.1.7 sent; wheels are py3-none-any.
- New API: `registry`, `HvacState`, `Device.encode(previous, target,
  actions)` -> `Command`; Broadlink, Pronto and raw output; decoding. The
  plugin API (`PluginObject`, `set_value`, `build_ircode`, `to_broadlink` on
  the device) is gone. See "Migrating from 0.1.x" in the README.
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
