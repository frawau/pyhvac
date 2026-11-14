# Phase 4 capability audit: Hitachi and Haier

Sources: `ir_Hitachi.h` / `ir_Haier.h` (header), `ir_*.cpp` (setters), `test/ir_*_test.cpp` (captures).
Test files are `tests/test_<device>_device.py`. "=" means unchanged.

## HitachiAcDevice (HITACHI_AC, RAS-35THA6)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–32 | = | kHitachiAcMin/MaxTemp (ir_Hitachi.h:86-87) | test_capabilities, test_setpoint_is_clamped_to_16_32 |
| step | 1 °C | = | Temp is whole °C << 1 | — |
| modes | auto heat cool dry fan | = | kHitachiAc{Auto,Heat,Cool,Dry,Fan} | test_capabilities |
| fan | auto,1,2,3 (FAN_3) | **added "4" (label "highest") = kHitachiAcFanHigh (5)**; 1-3 keep low/medium/high | ir_Hitachi.h:85; convertFan kMax (ir_Hitachi.cpp:352); setFan fanmax | test_fan_levels_follow_convert_fan[4-5], test_fan_offers_the_four_speeds_set_fan_allows, test_dry_has_only_low_and_medium[4-2], test_fan_mode_has_no_auto[4-4], test_real_capture_with_fan_high_is_reproduced_but_for_the_reset_bytes (NormalRealExample2, issue #417) |
| swing_v | off, swing | = | SwingV bit (byte 14) | test_capabilities |
| swing_h | off, swing | = | SwingH bit (byte 15) | test_capabilities |
| features | none | = | — | test_capabilities |

## Hitachi1Device (HITACHI_AC1, variants A and B: same capabilities)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–32 | = | setTemp clamps to kHitachiAcMin/MaxTemp | test_capabilities_are_the_documented_controls |
| modes | auto heat cool dry fan | = | kHitachiAc1* | same |
| fan | FAN_3 | = | kHitachiAc1Fan{Auto,Low,Med,High} | same |
| swing_v / swing_h | off, swing | = | SwingV / SwingH bits | same |
| sleep | on/off (sent as Sleep2) | = (see REPORT: levels 1-4 not offered) | kHitachiAc1Sleep1..4 (ir_Hitachi.h:239-243) | same |

## Hitachi264Device (HITACHI_AC264)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–32 | = | kHitachiAc264Min/MaxTemp | test_capabilities_are_the_documented_controls |
| modes | auto cool fan dry heat | **removed no-op "auto"** (was sent as cool) → cool fan dry heat | kHitachiAc264{Cool,Fan,Dry,Heat} only (ir_Hitachi.h:289-292); convertMode default cool | test_no_op_controls_are_not_offered, test_auto_mode_is_sent_as_cool |
| fan | FAN_3 | = | kHitachiAc264Fan{Low,Medium,High,Auto} | test_capabilities_are_the_documented_controls |
| swing_v | off, swing | **removed (no-op)** | no SwingV field in HitachiAC264Protocol; IRac::hitachi264 "No Swing(V)" | test_no_op_controls_are_not_offered, test_swing_and_features_have_no_bits |
| purifier, powerful, quiet, economy, light | on/off | **all removed (no-ops)** | no bits in HitachiAC264Protocol | same |

## Hitachi296Device (HITACHI_AC296)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–25 | **16–31** | kHitachiAc296MinTemp/MaxTemp (ir_Hitachi.h:362-363) | test_setpoint_range_is_the_headers, test_setpoint_is_whole_degrees_clamped_to_16_31, test_frames_clamp_the_setpoint_to_the_header_maximum |
| step | 1 °C | = | 5-bit Temp | — |
| modes | auto cool dry heat | = (DryCool, AutoDehumidifying, QuickLaundry, CondensationControl have no HvacState mode) | kHitachiAc296* | test_mode_codes |
| fan | auto,1..5 (FAN_5, "5" sent as FanHigh like "4") | **removed duplicate "5"** → auto,1..4 (FAN_4, same labels for 1-4) | kHitachiAc296Fan{Silent,Low,Medium,High,Auto} (ir_Hitachi.h:355-359) | test_no_fan_level_duplicates_high, test_every_fan_level_uses_convert_fan, test_the_oracles_highest_records_match_as_high |
| swing / features | none | = | — | — |

## Hitachi344Device (HITACHI_AC344)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–32 | = | kHitachiAc344Min/MaxTemp | test_capabilities_are_the_documented_controls |
| modes | cool fan dry heat | = | kHitachiAc344* (no auto) | same |
| fan | FAN_5 | = | kHitachiAc344Fan{Auto,Min,Low,Medium,High,Max} | same |
| swing_v | off, swing (button) | = | kHitachiAc344ButtonSwingV | same |
| swing_h | auto,1..5 | = | kHitachiAc344SwingH{Auto,LeftMax..RightMax} | same |

## Hitachi424Device (HITACHI_AC424)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–32 | = | kHitachiAc424Min/MaxTemp | test_capabilities_are_the_documented_controls |
| modes | fan heat cool dry | = | kHitachiAc424* (no auto) | same |
| fan | FAN_5 | = | kHitachiAc424Fan* | same |
| swing_v | off, swing (button) | = | kHitachiAc424ButtonSwingV | same |
| swing_h | none | = (button only, deferred) | kHitachiAc424ButtonSwingH | same |

## HaierAcDevice (HAIER_AC, HSU07-HEA03)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–30 | = | kHaierAcMin/MaxTemp | test_capabilities |
| modes | auto cool dry heat fan | = | kHaierAc* | test_capabilities |
| fan | FAN_3 | = | kHaierAcFan{Auto,Low,Med,High} | test_capabilities |
| swing_v | off, 1 (auto high), 2 (auto low) | **added "auto" = kHaierAcSwingVChg (0b11)** | ir_Haier.h:94; convertSwingV default (ir_Haier.cpp:398); toCommonSwingV → kAuto | test_swing_v_offers_every_documented_value, test_every_swing_position[auto-3], test_swing_change_matches_the_libraries_message_construction (MessageConstuction, synthetic) |
| purifier, sleep | on/off | = | Health bit, kHaierAcSleepBit | test_capabilities |

## Haier176Device (HAIER_AC176, variants A/B, incl. mabe models) and HaierYrw02Device (HAIER_AC_YRW02, A/B)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–30 | = | kHaierAcYrw02Min/MaxTempC | test_capabilities_are_the_documented_controls (both files) |
| modes | auto cool dry heat fan | = | kHaierAcYrw02* | same |
| fan | FAN_3 | = | kHaierAcYrw02Fan{Auto,Low,Med,High} | same |
| swing_v | off,auto,1..4 | = (all six kHaierAcYrw02SwingV* values; Middle/Bottom by mode as setSwingV) | ir_Haier.h | same |
| swing_h | auto,1..5 | = (all kHaierAcYrw02SwingH*) | ir_Haier.h | same |
| purifier, sleep, powerful, quiet | on/off | = | Health, Sleep, Turbo, Quiet bits | same |

## Haier160Device (HAIER_AC160)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–30 | = | kHaierAcYrw02Min/MaxTempC | test_capabilities |
| modes | auto cool dry heat fan | = | kHaierAcYrw02* | test_capabilities |
| fan | FAN_3 | = | kHaierAcYrw02Fan* | test_capabilities |
| swing_v | off,auto,1 ceiling,2 90°,3 45°,4 30°,5 0° | **added kHaierAc160SwingVHighest as "2" (label "highest")**; renumbered: 3 90°, 4 45°, 5 30°, 6 0° (labels kept on the same codes) | ir_Haier.h:160; setSwingV accepts it (ir_Haier.cpp:1829) | test_swing_v_offers_every_documented_position, test_every_swing_value[2-2], test_legacy_swing_labels_keep_their_positions |
| swing_h | none | = (not added, see REPORT) | struct has SwingH but IRHaierAC160 has no setter | test_capabilities |
| purifier, sleep, powerful, quiet, cleaning, light | on/off | = | Health, Sleep, Turbo, Quiet, Clean/Clean2, kHaierAc160ButtonLight | test_capabilities |

## Deferred (documented, but needs new frame logic)

- Hitachi264: kHitachiAc264ButtonSwingV — a swing button press; needs a toggle rule against `previous` (as Hitachi424), which the C path never sends.
- Hitachi424: kHitachiAc424ButtonSwingH — a horizontal swing button with no state field; needs a toggle rule.
- Hitachi1: sleep levels kHitachiAc1Sleep1..4 — a documented field write, but it would need a non-boolean "sleep" feature, which the vocabulary does not have (every device uses on/off). Not added.
- Haier AC / 176 / 160: the Button/Command field naming the key actually pressed (the real remotes do; C and the port always send Power / On-Off).
- Not deferred, excluded by the spec: timers, clock, Fahrenheit, Lock (Haier), Humidity (Hitachi296), AuxHeating as a user control (Haier160, set by heat mode).
