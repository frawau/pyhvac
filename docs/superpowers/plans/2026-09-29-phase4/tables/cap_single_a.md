# Phase 4 capability audit, group single_a

Header paths are relative to `irremote/src`; test names are in
`tests/test_<device>_device.py`. "=" means unchanged. Every device lost its
`test_capabilities_match_the_legacy_entity` (C-only); devices whose
capabilities did not change got a `test_capabilities_are_the_headers` pin
instead.

## AIRTON (airton.py AirtonDevice)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-25 | **16-31** | ir_Airton.h:70-71 kAirtonMinTemp/MaxTemp; setTemp ir_Airton.cpp:205 | test_setpoint_range_is_the_headers, test_setpoints_up_to_31_are_sent |
| step | 1 | = | Temp:4 field, whole degrees | - |
| modes | auto cool fan dry heat | = | ir_Airton.h:57-61 | test_mode_bits_when_powered |
| fan | auto,1-5 | = | ir_Airton.h:63-68 | test_every_fan_level_uses_its_documented_code |
| swing_v | off, swing | = | SwingV ir_Airton.h:40 | test_swing_sets_swing_v |
| swing_h | none | = | - | - |
| purifier | on/off | = | Health | test_purifier_and_light_set_their_bits |
| powerful | on/off | = | Turbo (+ fan max) | test_powerful_sets_turbo_and_fan_max |
| economy | on/off | = | Econo, cool only | test_economy_is_sent_in_cool_only |
| light | on/off | = | Light | test_purifier_and_light_set_their_bits |
| quiet | on/off | **REMOVED (no-op)** | no bit; IRac "No Quiet setting available" | test_quiet_is_not_offered |
| sleep | - | **ADDED** | Sleep ir_Airton.h:44; setSleep ir_Airton.cpp:297 (not in auto/fan) | test_sleep_sets_its_bit_outside_auto_and_fan, test_off_clears_sleep, test_port_reproduces_the_real_sleep_capture (0xA00600000911D3) |

## AIRWELL (airwell.py AirwellDevice)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-30 | = | ir_Airwell.h:43-44 | test_temperature_is_offset_from_the_minimum |
| modes | auto cool fan dry heat | = | ir_Airwell.h:51-55 | test_off_carries_mode_auto_in_every_mode |
| fan | FAN_4 (auto, 1 lowest, 2 low, 3 medium, 4 high; 1 and 2 both kAirwellFanLow) | **FAN_3 (auto, 1 low, 2 medium, 3 high)**: duplicate level removed | ir_Airwell.h:46-49 kAirwellFanLow/Medium/High/Auto | test_fan_offers_the_headers_three_speeds_and_auto, test_every_fan_level_uses_its_documented_code, test_a_lowest_record_sends_what_a_low_record_sends |
| swing / features | none | = | header has none | - |

## AMCOR (amcor.py AmcorDevice)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 12-32 | = | ir_Amcor.h:73-74 | test_every_whole_setpoint |
| modes | auto cool fan dry heat | = | ir_Amcor.h:66-70 | test_mode_codes_and_vent_in_mode_fan_only |
| fan | auto, 1 lowest, 2 medium, 3 highest | = | ir_Amcor.h:61-64 | test_every_fan_level |
| powerful | - | **ADDED** (Max, cool at 12 / heat at 32, nothing in other modes or off) | Max ir_Amcor.h:50, kAmcorMax :81; setMax ir_Amcor.cpp:189 | test_powerful_is_offered, test_powerful_sets_max_and_its_setpoint, test_powerful_is_not_sent_outside_cool_and_heat, test_powerful_is_not_sent_with_power_off (no real Max capture exists) |

## BOSCH144 (bosch.py Bosch144Device): unchanged

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-30 | = | ir_Bosch.h:70-71 kBosch144CelsiusMin/Max | test_capabilities_are_the_headers |
| modes | auto cool fan dry heat | = | ir_Bosch.h:53-57 | idem |
| fan | auto,1-5 | = | ir_Bosch.h:61-66 Fan20..Fan100, FanAuto | idem |
| quiet | on/off | = | Quiet bit ir_Bosch.h:168 | test_quiet_sets_the_quiet_bit_and_fan_auto |

## CARRIER_AC64 (carrier.py CarrierAc64Device)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-30 | = | ir_Carrier.h:80-81 | test_setpoint_is_clamped_to_the_documented_range |
| modes | cool fan heat | = | ir_Carrier.h:73-75 | test_mode_uses_its_documented_value |
| fan | auto,1-3 | = | ir_Carrier.h:76-79 | test_every_fan_level_uses_its_documented_code |
| swing_v | none | **ADDED off, swing** | SwingV ir_Carrier.h:49; setSwingV ir_Carrier.cpp:420; IRac::carrier64 IRac.cpp:721 | test_swing_and_sleep_are_offered, test_swing_sets_swing_v, test_port_reproduces_the_real_capture_but_its_timer_hours (RealExample 0x404000102E5E5584, swing on; only the disabled timers' hours differ) |
| sleep | - | **ADDED** (Sleep + OffTimer 2 h, enables clear) | Sleep ir_Carrier.h:56; setSleep ir_Carrier.cpp:432 | test_sleep_sets_sleep_and_a_disabled_2h_off_timer, test_port_reproduces_the_reconstructed_sleep_state_but_its_on_timer (0x2030009020555584) |

## CORONA_AC (corona.py CoronaAcDevice): unchanged

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 17-30 | = | ir_Corona.h:89-90 | test_capabilities_are_the_headers |
| modes | heat dry cool fan | = | ir_Corona.h:91-94 | idem |
| fan | auto,1-3 | = | ir_Corona.h:80-83 | idem |
| swing_v | off, swing (toggle) | = | SwingVToggle | idem |
| economy | on/off | = | Econo | idem |

## DELONGHI_AC (delonghi.py DelonghiAcDevice)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-25 | **18-32** | ir_Delonghi.h:53-54 kDelonghiAcTempMinC/MaxC; setTemp ir_Delonghi.cpp:186 | test_setpoint_range_is_the_headers, test_setpoint_is_sent_in_every_mode_clamped_to_18_32 |
| modes | auto cool fan dry | = | ir_Delonghi.h:63-66 | test_mode_uses_its_documented_value |
| fan | none (high in fan mode, else auto) | **ADDED FAN_3 (auto, 1 low, 2 medium, 3 high)**; normalise: auto/dry -> auto, fan mode auto -> 3 | ir_Delonghi.h:59-62; setFan ir_Delonghi.cpp:217 | test_fan_offers_the_headers_speeds_and_auto, test_every_fan_speed_uses_its_documented_code, test_auto_and_dry_allow_fan_auto_only, test_fan_mode_turns_auto_into_high, test_off_sends_fan_auto |
| powerful | on/off | = | Boost | test_powerful_sets_the_boost_bit |
| quiet | on/off | **REMOVED (no-op)** | no bit in the header | test_quiet_is_not_offered |
| sleep | - | **ADDED** | Sleep ir_Delonghi.h:36; setSleep ir_Delonghi.cpp:353 | test_sleep_sets_the_sleep_bit (no real sleep capture) |

## ECOCLIM (ecoclim.py EcoclimDevice)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 5-31 | **5-36** | ir_Ecoclim.h:43-44 kEcoclimTempMin, kEcoclimTempMax = Min + 31 | test_setpoint_range_is_the_headers, test_setpoint_and_sensor_temperature_are_the_target (5..36) |
| modes | auto cool fan dry heat | = | ir_Ecoclim.h:27-32 | test_mode_uses_its_documented_value |
| fan | auto,1-3 | = | ir_Ecoclim.h:35-38 | test_every_fan_level_uses_its_documented_code |
| sleep | - | **ADDED** (mode kEcoclimSleep in place of the mode, as IRac::ecoclim) | ir_Ecoclim.h:33; IRac.cpp:1208-1212 | test_sleep_is_offered, test_sleep_sends_mode_sleep (no real sleep capture) |

## ELECTRA_AC (electra.py ElectraAcDevice): unchanged

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-32 | = | ir_Electra.h:82-83 | test_capabilities_are_the_headers |
| modes | auto cool fan dry heat | = | ir_Electra.h:93-97 | idem |
| fan | auto,1-3 | = | ir_Electra.h:88-91 | idem |
| swing_v / swing_h | off, swing | = | ir_Electra.h:85-86 | idem |
| light, cleaning, powerful, quiet | on/off | = | LightToggle, Clean, Turbo, Quiet | idem |

## EUROM (eurom.py EuromDevice): unchanged

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-32 | = | ir_Eurom.h:116-117 | test_capabilities_are_the_headers |
| modes | cool heat fan dry | = | ir_Eurom.h:105-108 | idem |
| fan | 1-3, no auto | = | ir_Eurom.h:145-147 | idem |
| swing_v | off, swing | = | kEuromSwingOn :129 | idem |
| sleep | on/off | = | kEuromSleepEnabled :133 | idem |

## GOODWEATHER (goodweather.py GoodweatherDevice)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-31 | = | ir_Goodweather.h:79-80 | test_setpoint_is_clamped_to_16_31 |
| modes | auto cool fan dry heat | = | ir_Goodweather.h:64-68 | test_on_always_names_the_power_button |
| fan | auto,1-3 | = | ir_Goodweather.h:74-77 | test_every_fan_level_uses_the_documented_codes |
| swing_v | off, 1 "auto low", 2 "auto high" (both Slow) | off, **1 -> Slow, 2 -> Fast** (labels kept) | ir_Goodweather.h:70-72 kGoodweatherSwingFast/Slow/Off | test_swing_offers_the_two_speeds_and_off, test_every_swing_value, test_the_port_reproduces_the_swing_fast_capture (0xD52462000000), test_undeclared_swing_fast_deviation_is_reported |
| powerful, light | on/off | = (sent every message, spec) | Turbo, Light | test_powerful_is_the_turbo_bit_and_light_the_light_bit |
| quiet | on/off | **REMOVED (no-op)** | no bit; IRac "No Quiet setting available" | test_quiet_is_not_offered |
| sleep | - | **ADDED** | Sleep ir_Goodweather.h:40; setSleep ir_Goodweather.cpp:186; IRac.cpp:1406 | test_sleep_sets_the_sleep_bit |

## NEOCLIMA (neoclima.py NeoclimaDevice, also the soleus models)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-32 | = | ir_Neoclima.h:108-109 | test_every_setpoint_in_every_mode |
| modes | auto cool dry heat | **+ fan** | kNeoclimaFan ir_Neoclima.h:115; setMode ir_Neoclima.cpp:184 | test_fan_mode_is_offered, test_every_mode_uses_its_documented_code (+ fan in the setpoint, fan and off tests) |
| fan | auto,1-3 (dry forces low) | = | ir_Neoclima.h:101-104 | test_every_fan_level_uses_its_documented_code |
| swing_v / swing_h | off, swing | = | ir_Neoclima.h:99-100, setSwingH | test_swing_v_uses_its_documented_code |
| sleep, powerful, purifier, economy, light | on/off | = | Sleep, Turbo, Ion, Econo, Light | test_each_feature_sets_its_bit_only |

## RHOSS (rhoss.py RhossDevice): unchanged

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-30 | = | ir_Rhoss.h:74-75 | test_capabilities_are_the_headers |
| modes | auto cool dry heat fan | = | ir_Rhoss.h:67-71 | idem |
| fan | auto, 1 lowest, 2 medium, 3 highest | = | ir_Rhoss.h:62-65 | idem |
| swing_v | off, swing | = | ir_Rhoss.h:82-83 | idem |

## TRANSCOLD (transcold.py TranscoldDevice)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 17-30 | **18-30** | ir_Transcold.h:103-104 kTranscoldTempMin/Max | test_setpoint_range_is_the_headers, test_setpoint_17_is_clamped_to_kTranscoldTempMin |
| modes | auto cool dry fan heat | = | ir_Transcold.h:87-91 | test_every_mode |
| fan | auto,1-3 | = | ir_Transcold.h:94-98 | (existing fan tests) |
| swing_v | off, swing (toggle word) | = | kTranscoldSwing :111 | (existing toggle tests) |

## TRUMA (truma.py TrumaDevice): unchanged

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-31 | = | ir_Truma.h:63-64 | test_capabilities_are_the_headers |
| modes | auto cool fan | = | ir_Truma.h:53-55 | idem |
| fan | 1-3, no auto | = | ir_Truma.h:58-60 | idem |
| quiet | on/off (kTrumaFanQuiet, cool only) | = | ir_Truma.h:57 | idem |

## VESTEL_AC (vestel.py VestelAcDevice)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-30, frames clamp 18 outside heat | 16-30 (union); **normalise clamps to 18 outside heat** | ir_Vestel.h:71-73 kVestelAcMinTempH/MinTempC/MaxTemp | test_normalise_clamps_to_18_outside_heat, test_heat_sends_setpoints_down_to_16 |
| modes | auto cool dry fan heat | = | ir_Vestel.h:75-79 | test_mode_uses_its_documented_value |
| fan | 1-3, no auto | **auto + 1-3** | kVestelAcFanAuto ir_Vestel.h:81 | test_fan_offers_auto_and_the_three_speeds, test_fan_auto_uses_its_documented_code, test_port_reproduces_the_real_heat_capture (RealNormalExample 0xF4410001FF1201, now byte for byte), test_fanless_records_are_fan_auto |
| swing_v | off, swing | = | kVestelAcSwing :92 | test_swing_uses_its_documented_code |
| sleep, powerful, purifier | on/off | = | kVestelAcSleep/Turbo, Ion | test_sleep_and_powerful_share_turbo_sleep, test_purifier_sets_ion |

## Deferred (documented, needs new frame logic)

- TRANSCOLD swing_h: kTranscoldSwingH (ir_Transcold.h:112) is a separate
  command word, marked "NA" in the header; offering it needs a new message.

## Documented but outside the model or the vocabulary (not offered)

- ECOCLIM mode kEcoclimRecycle (not in HvacState MODES).
- NEOCLIMA hold, eye, fresh, 8 C heat, follow-me (no vocabulary key).
- GOODWEATHER air flow (AirFlow bit), and the Command "button" field.
- TRANSCOLD fan kTranscoldFanZoneFollow / kTranscoldFanFixed (not speeds).
- VESTEL fan kVestelAcFanAutoCool/AutoHot (IRVestelAc::setAuto levels).
- Timers, clocks, sensor temperatures (Electra IFeel/SensorTemp, Ecoclim
  SensorTemp), Fahrenheit: excluded by the spec.
