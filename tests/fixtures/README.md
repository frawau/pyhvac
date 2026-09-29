# Test fixtures

- `oracle/<PROTOCOL>.json.gz`: what pyhvac 0.1.7's IRremoteESP8266 C path sent
  for a grid of old-vocabulary states (one record per state: plugin, model,
  class, variant, state, pulses). Generated with pyhvac 0.1.7's
  `tools/oracle_generate.py`; CARRIER_AC64, TROTEC, TROTEC_3550 and
  WHIRLPOOL_AC were regenerated from the fixed C path (protocol names and
  the missing-comma bug fixed) before the C extension was removed.
- `oracle_extra/<test module>.json.gz`: the C output the tests compared with
  beyond the grid (persistent-object sequences, extra states, the
  fixed-glue cases, direct IRac checks), recorded once by `tests/c_oracle.py`
  (PYHVAC_FREEZE=1) while the C extension still existed; replayed ever since.
- `golden/<module>.json.gz`: what the 0.1.x pure-Python classes sent.
- `airwell_c_raw.json`: the AIRWELL state words the C library built (its
  SWIG timing recorder mis-recorded Manchester pulses).
