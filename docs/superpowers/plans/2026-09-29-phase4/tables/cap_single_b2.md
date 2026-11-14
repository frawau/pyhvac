# Capability audit, group single_b2: old -> new

Sources: `irremote/src/ir_*.h` (header constants and union structs), `ir_*.cpp`
(setters), `IRac.cpp` (what IRac sends). Test names are in the device's
`tests/test_*_device.py`. Every device's `test_capabilities_match_the_legacy_entity`
is deleted; each device gets `test_capabilities_are_the_documented_ones`.

## TOSHIBA_AC — ToshibaAcDevice (unchanged)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 17–30 | 17–30 (same) | kToshibaAcMinTemp/MaxTemp, ir_Toshiba.h:101-102 | test_setpoint_is_sent_in_the_state_message |
| step | 1 | 1 | Temp :4 (whole degrees) | test_capabilities_are_the_documented_ones |
| modes | auto cool dry fan heat | same | kToshibaAc{Auto..Fan}, ir_Toshiba.h:104-108 | test_mode_uses_its_documented_value |
| fan | auto 1–5 | same | kToshibaAcFanAuto..FanMax, ir_Toshiba.h:110-113 | test_fan_is_the_speed_plus_one |
| swing_v | off swing | same | kToshibaAcSwingOn/Off, ir_Toshiba.h:97-98 | test_swing_message_is_the_documented_swing_state |
| swing_h | – | – | – | – |
| powerful | on/off | same | kToshibaAcTurboOn, ir_Toshiba.h:115 | test_powerful_and_economy_make_the_long_message |
| economy | on/off | same | kToshibaAcEconoOn, ir_Toshiba.h:116 | same |
| purifier | on/off | same | Filter, ir_Toshiba.h:79 | test_port_reproduces_the_captures (PURE_ON) |

## ARGO — ArgoDevice, WREM2

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–25 | **10–32** | kArgoMinTemp/kArgoMaxTemp, ir_Argo.h:171-172; setTemp clamps to them | test_every_setpoint, test_setpoint_is_clamped_to_the_header_range, test_new_values_match_the_c_path[WREM2] |
| step | 1 | 1 | Temp :5 | – |
| modes | auto cool fan dry heat | same | kArgo* / argoMode_t | test_every_mode |
| fan | auto 1–3 | same | kArgoFanAuto, kArgoFan1..3 (Fan :2), ir_Argo.h:226-229 | test_every_wrem2_fan_level |
| swing_v | auto 1–6 | same | FLAP_AUTO, FLAP_1..6 | test_every_swing_value |
| powerful | on/off | same | Max, ir_Argo.h:59 | test_powerful_sets_max_in_every_mode |
| quiet | on/off | **removed (no-op)** | IRac::argo "No Quiet setting available", IRac.cpp:527 | test_wrem2_offers_no_quiet |
| sleep | – | **added** | Night, ir_Argo.h:58; IRac::argo setNight(sleep >= 0), IRac.cpp:534 | test_wrem2_sleep_sets_night |

## ARGO — ArgoDevice, WREM3

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–25 | **10–32** | kArgoMinTemp/MaxTemp, ir_Argo.h:171-172 ("range: 10..32", :101) | test_every_setpoint, test_new_values_match_the_c_path[WREM3] |
| step | 1 | 1 | Temp :5 | – |
| modes | auto cool fan dry heat | same | argoMode_t | test_every_mode |
| fan | auto 1–3 (1=FAN_LOWER, 2=FAN_LOW, 3=FAN_HIGH) | **auto 1–6**: 1 FAN_LOWEST "lowest", 2 FAN_LOWER "low", 3 FAN_LOW "medium", 4 FAN_MEDIUM "midhigh", 5 FAN_HIGH "high", 6 FAN_HIGHEST "highest" | argoFan_t, ir_Argo.h:214-222; WREM3 setFan stores all | test_every_wrem3_fan_level, test_wrem3_med_high_fan_is_the_class_built_message, test_new_values_match_the_c_path[WREM3] |
| swing_v | auto 1–6 | same | FLAP_AUTO, FLAP_1..6 | test_every_swing_value |
| powerful | on/off | same | Max | test_powerful_sets_max_in_every_mode |
| quiet | on/off | same (Night) | Night, ir_Argo.h:107; IRac passes quiet as night, IRac.cpp:3186 | test_wrem3_features |
| economy | on/off | same | Eco, ir_Argo.h:108 | test_wrem3_features |
| purifier | on/off | same | Filter, ir_Argo.h:111 | test_wrem3_features |
| light | – | **added** | Light, ir_Argo.h:112; argoWrem3_ACCommand setLight | test_wrem3_features, test_all_features_together, test_wrem3_real_capture_except_what_the_entity_cannot_express (real capture, Light on), test_new_values_match_the_c_path[WREM3] |

## SHARP_AC — SharpAcDevice, A907

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 15–30 | same | kSharpAcMinTemp/MaxTemp, ir_Sharp.h:95-96 | test_setpoint_modes_send_degrees_above_15 |
| modes | auto cool dry heat | same | kSharpAcAuto/Heat "A907 only", ir_Sharp.h:106,110 | test_mode_uses_its_documented_value |
| fan | auto 1–3 | **auto 1–4** (4 = kSharpAcFanMax "FAN4", label "highest") | ir_Sharp.h:112-117 | test_every_fan_level_uses_its_documented_code_in_every_mode, test_a907_fan_levels_are_the_real_captures (KnownStates cool_fan1..4_28), test_a907_fan_4_is_the_legacy_highest, test_states_beyond_the_oracle_grid_match_the_c_path[A907] |
| swing_v | off 1 2 3 | same | kSharpAcSwingV{Ignore,High,Mid,Low} | test_swing_positions_use_their_documented_codes |
| cleaning / powerful / purifier | on/off | same | Clean / setTurbo / Ion | existing tests |
| economy | on/off | **removed (no-op)** | IRac.cpp:2492 "Econo deliberately not used" | test_economy_and_light_are_not_offered |

## SHARP_AC — SharpAcDevice, A903 and A705

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 15–30 | same | ir_Sharp.h:95-96 | test_setpoint_modes_send_degrees_above_15 |
| modes | A903 auto cool dry fan; A705 cool dry fan | same (see REPORT: A903 auto) | ir_Sharp.h:106-110 | test_mode_uses_its_documented_value |
| fan | auto 1–3 | same | kSharpAcFanA705Low/A705Med/FanMax, ir_Sharp.h:114-117 | test_every_fan_level_uses_its_documented_code_in_every_mode |
| swing_v | off 1 2 3 | same | – | – |
| cleaning / powerful / purifier | on/off | same | – | – |
| light | on/off | **removed (no-op)** | setLightToggle's Special overwritten by setMode/setPower, IRac.cpp:2497-2510 | test_economy_and_light_are_not_offered |

## GREE — GreeDevice (YAW1F, YBOFB, YX1FSF)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16–30 | same | kGreeMinTempC/MaxTempC, ir_Gree.h:104-105 | test_every_setpoint_in_every_mode |
| step | 1 | 1 (TempExtraDegreeF is Fahrenheit) | – | test_capabilities_are_the_documented_ones |
| modes | auto cool dry fan heat | same | kGree{Auto..Heat} | test_every_mode_uses_its_documented_code |
| fan | auto 1–3 | same | kGreeFan{Auto,Min,Med,Max} | test_every_fan_level |
| swing_v | auto 1–5 | **off auto 1–5** (off = kGreeSwingLastPos, SwingAuto clear; SWING_V_ANGLES) | ir_Gree.h:110; convertSwingV kOff -> LastPos | test_swing_v_uses_its_documented_code, test_records_without_swing_are_swing_off (29 C records), test_port_reproduces_the_energy_saver_capture_swing_off (real capture #1821), test_states_beyond_the_oracle_grid_match_the_c_path |
| swing_h | off auto 1–5 | same | kGreeSwingH* | test_every_swing_h_value |
| powerful / light / cleaning | on/off | same | Turbo / Light / Xfan | test_each_feature_sets_its_bit_only |
| economy | YBOFB, YX1FSF | same | Econo (+ kGreeEcono mode on YX1FSF) | test_yx1fsf_economy_is_mode_econo_in_every_mode |
| sleep | – | **added, all variants** | Sleep, ir_Gree.h:53; IRac::gree setSleep(sleep >= 0), IRac.cpp:1455 | test_sleep_sets_the_sleep_bit, test_each_feature_sets_its_bit_only |

## MIDEA — MideaDevice (unchanged)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 17–30 | same | kMideaACMinTempC/MaxTempC, ir_Midea.h:112-113 | test_capabilities_are_the_documented_ones |
| modes | auto cool fan dry heat | same | kMideaAC{Cool..Fan} | existing |
| fan | auto 1–3 | same | kMideaACFan{Low,Med,High} | existing |
| swing_v | off swing | same | kMideaACToggleSwingV | existing |
| powerful quiet economy light cleaning sleep | on/off | same | toggles / QuietOn/Off / Sleep bit | existing |

## COOLIX — CoolixDevice

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 17–30 | same | kCoolixTempMin/Max, ir_Coolix.h:63-64 | test_every_setpoint |
| modes | cool dry auto heat fan | same | kCoolix{Cool..Heat}, fan = Dry + kCoolixFanTempCode | test_every_mode |
| fan | auto 1–3 | same | kCoolixFan{Min,Med,Max} | test_every_fan_level |
| swing_v / swing_h | off swing | same (one kCoolixSwing word) | ir_Coolix.h:124 | existing |
| powerful / light / cleaning | on/off | same | kCoolixTurbo/Led/Clean | existing |
| quiet | on/off | **removed (no-op)** | IRac::coolix "No Quiet setting available"; no quiet word in ir_Coolix.h | test_quiet_is_not_offered |

## FUJITSU_AC — FujitsuAcDevice

| aspect | variant | old | new | source | test |
|---|---|---|---|---|---|
| setpoint | all | 16–30 | same | kFujitsuAcMinTemp/MaxTemp, ir_Fujitsu.h:137-138 | test_setpoint_encoding |
| step | ARREW4E | 1 | **0.5** | setTemp ARREW4E: Temp = (C - offset/2) * 2, ir_Fujitsu.cpp:476 | test_arrew4e_setpoint_has_half_degrees, test_arrew4e_half_degree_is_the_real_capture (arrew4e_25_5c), test_arrew4e_half_degrees_match_the_c_path |
| step | others | 1 | 1 | Temp = (C - 16) * 4, getTemp integer | test_other_variants_snap_to_whole_degrees |
| modes | all | auto cool dry fan heat | same | kFujitsuAcMode* | test_mode_uses_its_documented_value |
| fan | all | auto 1–4 | same | kFujitsuAcFan{Quiet,Low,Med,High} | test_fan_follows_convert_fan |
| swing_v | ARDB1, ARJW2 | off swing | **removed (no-op)** | checkSum forces kFujitsuAcSwingOff, ir_Fujitsu.cpp:209 | test_ardb1_and_arjw2_send_15_bytes_and_never_swing |
| swing_h | ARJW2 | off swing | **removed (no-op)** | same | same |
| swing_v | ARRAH2E ARREB1E ARRY4 ARREW4E | off swing | same | kFujitsuAcSwing* | test_swing_sends_the_documented_bits |
| swing_h | ARRAH2E ARREW4E | off swing | same | setSwing | same |
| quiet | all | on/off | same (fan kFujitsuAcFanQuiet) | IRac::fujitsu | test_quiet_sets_the_quiet_fan |
| powerful / economy | ARREB1E ARREW4E | on/off | same | kFujitsuAcCmdPowerful/Econo | test_commands_are_buttons_pressed_on_a_change |
| purifier / cleaning | ARRY4 | on/off | same | Filter / Clean | test_arry4_sends_filter_and_clean |

## Deferred (documented, need new frame logic)

- SHARP_AC A907 economy: setEconoToggle's special message (Special kSharpAcSpecialTempEcono, PowerSpecial SetSpecialOn/Off, ir_Sharp.h:145). IRac never sends it ("cycles through 3 modes uncontrollably", IRac.cpp:2492).
- SHARP_AC A903/A705 light: setLightToggle's special message (same Special code).
- COOLIX sleep: kCoolixSleep word 0xB2E003 (ir_Coolix.h:127), a separate toggle word IRac::coolix sends after the state.
- FUJITSU_AC ARDB1/ARJW2 (and others) swing: kFujitsuAcCmdToggleSwingVert/Horiz and StepVert/Horiz short codes (ir_Fujitsu.h:125-128).
- FUJITSU_AC 10C Heat (ARRAH2E, ARREW4E): set10CHeat rewrites mode/fan/swing and reuses the Clean bit; a mode-level message, and no vocabulary name.
- MIDEA 8C heat: kMideaACToggle8CHeat (ir_Midea.h:147); the special message exists in the port's table, but there is no feature name for it.
- TOSHIBA swing step/toggle (kToshibaAcSwingStep/Toggle): button presses, not states.
