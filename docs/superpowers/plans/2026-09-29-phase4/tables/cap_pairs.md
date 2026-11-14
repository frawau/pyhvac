# Phase 4 capability audit: pairs group

Headers are in IRremoteESP8266 `src/` (h = header, cpp = implementation).
"=" means unchanged. **ADDED** / **REMOVED (no-op)** / **REMOVED (alias)** mark the changes.
An alias is a value with no code of its own that sent the same code as another offered value.
Every changed device has a `test_capabilities_are_the_documented_values` test that pins the whole capability set.
Each device's `test_capabilities_match_the_legacy_entity` test is deleted.

## MitsubishiAcDevice (mitsubishi_electric.py, MITSUBISHI_AC, 12 models)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-31 | = | kMitsubishiAcMinTemp/MaxTemp (ir_Mitsubishi.h:124-125) | test_setpoint_is_clamped_to_16_31 |
| step | 0.5 | = | HalfDegree bit (h:72) | test_setpoint_has_half_degrees |
| modes | auto cool fan dry heat | = | kMitsubishiAc{Auto..Fan} | test_mode_codes_and_the_byte_8_nibble_set_mode_writes |
| fan | auto, 1-5 | = | FanAuto bit, Fan 1-4 + Silent | test_every_fan_level_uses_set_fan |
| swing_v | off(VaneAuto) auto(VaneSwing) 1-5 | = | kMitsubishiAcVane* | test_every_swing_v_position_drives_both_vanes |
| swing_h | auto 1-6 | = | kMitsubishiAcWideVane* | test_every_swing_h_position |
| economy | - | **ADDED** (Ecocool bit, byte 14 bit 5) | struct `Ecocool` (h:94); toString reports it as kEconoStr (cpp:880) | test_economy_is_the_ecocool_bit |
| quiet | - | not added (it has no bit: IRac's quiet is fan kMitsubishiAcFanSilent, which fan "1" already sends) | kMitsubishiAcFanQuiet = FanSilent (h:123), IRac.cpp:2044 | test_capabilities_are_the_documented_values |

## Mitsubishi136Device (MITSUBISHI136, 4 models)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-25 | **17-30** | kMitsubishi136MinTemp/MaxTemp (h:172-173) | test_setpoint_is_whole_degrees_clamped_to_17_30 |
| step | 1 | = | Temp is whole °C | test_capabilities_are_the_documented_values |
| modes | 5 | = | kMitsubishi136{Fan,Cool,Heat,Auto,Dry} | test_mode_codes |
| fan | auto, 1-5 | **1-4** (lowest, low, medium, highest) | kMitsubishi136Fan{Min,Low,Med,Max} (h:184-187). **REMOVED (alias)**: auto (no auto code, C sent Med) and "5" (C sent Max, as "4") | test_every_fan_level, test_fans_without_a_code_are_not_offered |
| swing_v | off auto 1-4 | **auto 1-4** | kMitsubishi136SwingV* (h:179-183). **REMOVED (alias)**: off (no off code, C sent SwingVAuto) | test_every_swing_value, test_swing_off_is_not_offered |
| swing_h | - | = | none in the struct | - |
| quiet | on/off | = (kept: forces kMitsubishi136FanQuiet) | kMitsubishi136FanQuiet (h:188) | test_quiet_forces_the_quiet_fan |
| real capture | fan "5" | fan "4" | PEAD-RP71JAA DecodeRealExample | test_the_real_capture_is_reproduced |

## Mitsubishi112Device (MITSUBISHI112, 4 models)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-25 | **16-31** | kMitsubishi112MinTemp/MaxTemp (h:226-227) | test_setpoint_is_31_minus_whole_degrees_clamped_to_16_31, test_off_carries_mode_auto_and_the_setpoint |
| modes | auto cool dry heat | = (no fan-only mode) | kMitsubishi112{Cool,Heat,Auto,Dry} | test_mode_codes |
| fan | 1-4 | = (no auto code) | kMitsubishi112Fan{Min,Low,Med,Max} | test_every_fan_level_uses_the_documented_code |
| swing_v | off auto 1-5 | **auto 1-5** | kMitsubishi112SwingV* (h:234-239). **REMOVED (alias)**: off (C sent SwingVAuto) | test_every_vertical_swing_value, test_swing_v_off_is_not_offered |
| swing_h | auto 1-6 | = | kMitsubishi112SwingH* | test_every_horizontal_swing_value |
| quiet | on/off | = (kept) | kMitsubishi112FanQuiet | test_quiet_overrides_the_fan |

## MitsubishiHeavy152Device (mitsubishi_heavy_industries.py, MITSUBISHI_HEAVY_152, 5 models)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 17-31 | = | kMitsubishiHeavyMinTemp/MaxTemp | test_setpoint_is_clamped_to_17_31 |
| modes | 5 | = | kMitsubishiHeavy{Auto..Heat} | test_mode_codes_and_the_setpoint_in_every_mode |
| fan | auto 1-5 | = (1 = Econo, 5 = Max; Turbo through powerful) | kMitsubishiHeavy152Fan* | test_every_fan_level |
| swing_v | off auto 1-5 | = | kMitsubishiHeavy152SwingV* | test_every_swing_v_value |
| swing_h | auto 1-5, "6" labelled wide (which sent SwingHOff) | **off, auto, 1-5, 6 right-left, 7 left-right** | kMitsubishiHeavy152SwingH{Off,RightLeft,LeftRight} (h:115-117). **ADDED**: off (8), RightLeft (6), LeftRight (7). **REMOVED**: "wide" (not documented; it sent Off) | test_every_swing_h_value, test_the_legacy_wide_is_read_as_off, test_a_missing_hswing_is_the_off_default |
| quiet sleep purifier cleaning powerful economy | on/off | = | Silent, Night, Filter, Clean, FanTurbo, FanEcono | test_feature_bits, test_powerful_is_turbo_and_economy_is_econo_and_wins |
| 3D | - | not added ("3D" is not in the feature vocabulary) | Three/D bits (h:59,61) | - |

## MitsubishiHeavy88Device (MITSUBISHI_HEAVY_88, 3 models)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 17-31 | = | kMitsubishiHeavyMinTemp/MaxTemp | test_setpoint_is_whole_degrees_offset_from_17 |
| modes | auto cool dry heat | **+ fan** | kMitsubishiHeavyFan (h:87); IRMitsubishiHeavy88Ac::setMode accepts it (cpp:653) | test_mode_codes, test_off_carries_mode_auto |
| fan | 1 Econo, 2 Low, 3 Med, 4 Turbo | **auto, 1 Econo, 2 Low, 3 Med, 4 High, 5 Turbo** (FAN_5) | kMitsubishiHeavy88Fan{Auto,High} (h:163,166). **ADDED**: auto, High. Turbo moves from "4" to "5" (label "highest" kept) | test_every_fan_level_uses_its_documented_code |
| swing_v | off auto 1-5 | = | kMitsubishiHeavy88SwingV* | test_vertical_swing_counts_down_from_highest |
| swing_h | off auto 1-5 | **+ 6 right-left, 7 left-right, 8 3D** | kMitsubishiHeavy88SwingH{RightLeft,LeftRight,3D} (h:159-161) | test_horizontal_swing_runs_left_to_right |
| cleaning powerful economy | on/off | = | Clean, FanTurbo, FanEcono | test_cleaning_sets_the_clean_bit, test_powerful_and_economy_are_fan_codes |
| real capture | differed in fan auto and SwingH LeftRight | **reproduced exactly** | ZjsSyntheticExample | test_the_synthetic_capture_is_reproduced |

## PanasonicAcDevice (panasonic.py, PANASONIC_AC; variants NKE, DKE, JKE, CKP, RKR)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-30 | = | kPanasonicAcMinTemp/MaxTemp | test_temperatures_clamp_to_the_documented_range |
| modes / fan / swing_v | 5 / auto 1-5 / auto 1-5 | = | kPanasonicAc* | test_capabilities_are_the_documented_values |
| swing_h NKE | off/swing | **REMOVED (no-op)** | setSwingHorizontal forces Middle on NKE (ir_Panasonic.cpp:455-457) | test_nke_offers_no_swing_h, test_nke_swing_h_is_always_middle |
| swing_h DKE, RKR | auto 1-5 | = | kPanasonicAcSwingH* | test_swing_h_positions |
| swing_h JKE, CKP | - | = | never written | test_jke_and_ckp_have_no_swing_h |
| quiet, powerful | all variants | = | kPanasonicAcQuiet/PowerfulOffset (+Ckp) | test_quiet_and_powerful |
| purifier | DKE only | = | kPanasonicAcIonFilterByte (setIon: DKE only) | test_only_dke_has_a_purifier |

## PanasonicAc32Device (PANASONIC_AC32, 3 models): no change

| aspect | old | new | source | test |
|---|---|---|---|---|
| all | 16-30; 5 modes; auto 1-5; auto 1-5; off/swing | = | PanasonicAc32Protocol, kPanasonicAc32* | test_capabilities_are_the_documented_values |

## SanyoAcDevice (sanyo.py, SANYO_AC, 5 models)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-30 | = | kSanyoAcTempMin/Max | test_setpoint_is_clamped_to_16_30 |
| modes | auto cool dry heat | = (no fan code) | kSanyoAc{Heat,Cool,Dry,Auto} | test_mode_codes_and_the_setpoint_in_every_mode |
| fan | auto 1-3 | = | kSanyoAcFan* | test_every_fan_level |
| swing_v | auto + 5 angles (90° 60° 45° 30° 0°) | **auto + 6 positions, header-named labels: highest, high, upper middle, lower middle, low, lowest** | kSanyoAcSwingV* (h:101-107). **ADDED**: LowerMiddle ("4") | test_every_swing_v_value, test_legacy_angles_are_read_as_what_c_sent |
| sleep | on/off | = | Sleep bit | test_sleep_bit |

## SanyoAc88Device (SANYO_AC88, 1 model)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 10-30 | = | kSanyoAc88TempMin/Max | test_setpoint_is_whole_degrees_clamped_to_10_30 |
| modes | auto cool heat fan | = (FeelCool/FeelHeat have no HvacState mode) | kSanyoAc88* | test_mode_codes |
| fan | auto, 1 lowest, 2 medium, 3 high, 4 highest | **FAN_3: auto, 1 low, 2 medium, 3 high** | kSanyoAc88Fan{Auto,Low,Medium,High} (h:184-187). **REMOVED (alias)**: "highest" (it sent FanHigh, as "high") | test_fan_codes, test_legacy_extra_fans_are_read_as_what_c_sent |
| swing_v | off/swing | = | SwingV bit | test_swing_sends_the_documented_bit |
| powerful purifier sleep | on/off | = | Turbo, Filter, Sleep | test_each_feature_sets_its_bit_only |

## LgAcDevice (lg.py, LG; variants LG6711A20083V, GE6711AR2853M)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-25 | **16-30** | kLgAcMinTemp/MaxTemp (ir_LG.h:63-64) | test_every_setpoint, test_setpoint_is_clamped_to_16_30, test_real_captures_except_the_unnamed_bit_15 (0x880CF50, heat 30 °C) |
| modes / fan | 5 / auto 1-4 | = | kLgAc*; setFan stores kLgAcFanHigh as Max off AKB74955603 | test_every_fan_level |
| swing_v LG6711A20083V | off/swing | = | kLgAcSwingVToggle | test_swing_with_previous_toggles_on_change |
| swing_v GE6711AR2853M | off auto 1-5 | **REMOVED (no-op)** | IRLgAc::send has no GE swing word (cpp:254) | test_ge_offers_no_swing, test_ge_sends_no_swing_word |
| swing_h (both) | off/swing | **REMOVED (no-op)** | SwingH words are AKB73757604-only (cpp:254) | test_capabilities_are_the_documented_values, test_light_and_swing_h_send_nothing |
| light (both) | on/off | **REMOVED (no-op)** | the light toggle is AKB74955603-only (cpp:254) | same |

## Lg2Device (LG2; variants AKB75215403 = V1, AKB74955603 = V2, AKB73757604 = V3)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint (all) | 16-25 | **16-30** | kLgAcMinTemp/MaxTemp (h:63-64) | test_setpoint_is_clamped_to_16_30, test_swing_off_after_auto_capture (26 °C now reproduced) |
| fan V1 | auto 1-5 ("4" and "5" both Max) | **auto 1-4** | **REMOVED (alias)**: "5" (setFan stores High as Max) | test_every_fan_level |
| fan V2 | auto 1-4 | **auto 1-5** | **ADDED**: "5" = kLgAcFanMax (h:56), kept apart from kLgAcFanHigh (h:59) on AKB74955603 | test_every_fan_level |
| fan V3 | auto 1-4 | = | as V1 | test_every_fan_level |
| swing_v V1 | off auto 1-5 | **REMOVED (no-op)** | no swing word for AKB75215403 | test_akb75215403_sends_the_state_word_only |
| swing_v V2 | off auto + 5 angles | **off, auto + 6 positions (header names)** | kLgAcSwingV* (h:78-87). **ADDED**: UpperMiddle ("3") | test_akb74955603_swing_word_without_previous |
| swing_v V3 | off auto + 5 angles (off/auto sent Highest) | **6 positions** | kLgAcVaneSwingV* (h:103-108). **ADDED**: UpperMiddle ("3"). **REMOVED (alias)**: off, auto (convertVaneSwingV's default is Highest) | test_akb73757604_sends_every_vane_then_swing_h, test_akb73757604_offers_no_swing_off_or_auto, test_vane_upper_middle_capture |
| swing_h V1, V2 | off/swing | **REMOVED (no-op)** | SwingH words are AKB73757604-only | test_akb74955603_sends_no_swing_h, test_akb75215403_sends_the_state_word_only |
| swing_h V3 | off/swing | = | kLgAcSwingHAuto/Off | test_akb73757604_swing_h_with_previous_only_on_change |
| light V1, V3 | on/off | **REMOVED (no-op)** | the light toggle is AKB74955603-only | test_akb73757604_swing_h_and_no_light, test_akb75215403_sends_the_state_word_only |
| light V2 | on/off | = | kLgAcLightToggle | test_akb74955603_light_toggle_whenever_light_is_off |

## KelonDevice (kelon.py, KELON, 1 model)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 18-32 | = (auto/dry/fan forced to 26/25 in frames, as setMode) | kKelonMinTemp/MaxTemp | test_setpoint_is_sent_in_cool_and_heat |
| modes / fan | 5 / auto 1-3 | = | kKelonMode*, kKelonFan* | test_mode_uses_its_documented_value |
| swing_v | - | **ADDED off/swing** (SwingVToggle, same rule as PowerToggle) | struct `SwingVToggle` (ir_Kelon.h:54); IRac::handleToggles KELON case (IRac.cpp:3028), sendAc passes `swingv != kOff` (IRac.cpp:3489) | test_swing_toggle_without_previous_is_the_target_swing, test_swing_toggle_with_previous_toggles_on_change, test_port_reproduces_the_swing_toggle_capture_but_for_its_dry_setpoint |
| sleep | on/off | = | SleepEnabled | test_sleep_sets_the_sleep_bit |
| powerful | - | **ADDED** (Super Cool: both SuperCoolEnabled bits, cool, 18 °C, fan max) | SuperCoolEnabled1/2 (h:62,64); IRKelonAc::setSupercool (cpp:278); IRac passes turbo as superCool (IRac.cpp:3489) | test_powerful_is_super_cool, test_port_reproduces_the_super_cool_capture (real 0x900002010683) |

## TrotecDevice (trotech.py, TROTEC, 3 models)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-30 (16, 17 sent as 18) | **18-32** | kTrotecMinTemp/MaxTemp (ir_Trotec.h:73,75) | test_setpoint_is_clamped_to_18_32 |
| modes / fan / sleep | auto cool dry fan / 1-3 / on-off | = | kTrotec* | test_capabilities_are_the_documented_values |

## Trotec3550Device (TROTEC_3550, 2 models): no change

| aspect | old | new | source | test |
|---|---|---|---|---|
| all | 16-30; 4 modes; 1-3; off/swing | = | kTrotec3550MinTempC/MaxTempC, SwingV bit | test_capabilities_are_the_documented_values |

## Deferred / not offered

No feature in these protocols needs new frame logic, so nothing is deferred in the spec's sense. Documented fields that are left out:
- Out of the feature vocabulary: MitsubishiAc ISee, AbsenseDetect, DirectIndirect, NaturalFlow ("Fresh"), iSave10C (10 °C heat); MitsubishiHeavy152 3D (Three/D bits); Sanyo Beep; Kelon DehumidifierGrade; SanyoAc88 FeelCool/FeelHeat modes (no HvacState mode).
- Excluded by the spec: timers and clocks (Mitsubishi, Panasonic, Sanyo, Sanyo88, Kelon, Trotec, Trotec3550), sensor temperature (Sanyo), Fahrenheit (Trotec3550).
