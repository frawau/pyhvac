# Capability audit, group single_b1

Header references are to IRremoteESP8266 `src/` in the scratchpad copy
(`irremote/src`). Test names are in `tests/test_<device>_device.py`. "=" means
unchanged. In every device, the C-only `test_capabilities_match_the_legacy_entity`
is deleted.

## Kelvinator: `KelvinatorDevice` (kelvinator, gree YAPOF3/YAP0F8, sharp YB1FA/A5VEY)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-30 | = | kKelvinatorMinTemp/MaxTemp, ir_Kelvinator.h:102-103 | test_every_setpoint_in_every_mode, test_setpoint_is_clamped |
| step | 1 | = | Temp:4 whole degrees, ir_Kelvinator.h:46 | same |
| modes | auto cool fan dry heat | = | kKelvinator{Auto..Heat}, ir_Kelvinator.h:93-97 | test_every_mode_uses_its_documented_code |
| fan | auto, 1-3 (FAN_3: sent as Fan 2/3/4) | **auto, 1-5 (FAN_5: Fan 1..5)**. Added: Fan 1 and Fan 5. The legacy low/medium/high stay Fan 2/3/4 (FAN_5's "2"/"3"/"4") | kKelvinatorFanAuto/Min/Max, ir_Kelvinator.h:99-101; setFan "0 is auto, 1-5 is the speed", ir_Kelvinator.cpp:229-242 | test_fan_offers_the_five_documented_speeds, test_every_fan_level, test_fan_5_is_kelvinator_fan_max, test_port_reproduces_the_fan_1_message_construction (reproduces TestKelvinatorClass.MessageConstuction's wire and SendDataOnly's typical state, both fan 1; library test states, not captures) |
| swing_v | off auto 1-5 | = | kKelvinatorSwingV{Off,Auto,Highest..Lowest}, ir_Kelvinator.h:106-112 | test_swing_v_uses_its_documented_code |
| swing_h | off swing | = | SwingH:1, ir_Kelvinator.h:61 | test_swing_h_sets_swing_h_and_swing_auto |
| powerful | on/off | = | Turbo, ir_Kelvinator.h:50 | test_each_feature_sets_its_bit_only |
| quiet | on/off | = | Quiet, ir_Kelvinator.h:80 | same |
| light | on/off | = | Light, ir_Kelvinator.h:51 | same |
| purifier | on/off | = | IonFilter, ir_Kelvinator.h:52 | same |
| cleaning | on/off | = | XFan, ir_Kelvinator.h:53 | same, test_cleaning_only_in_cool_and_dry |

Not offered: sleep (see Deferred); swing range codes LowAuto/MiddleAuto/HighAuto
(kKelvinatorSwingV*Auto, ir_Kelvinator.h:113-115) have no HvacState name.

## Mirage: `MirageDevice`

### KKG9AC1 (VLU series, generic, Maxell)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-32 | = | kMirageAcMinTemp/MaxTemp, ir_Mirage.h | test_temperature_is_offset_by_0x5c |
| modes | cool fan dry heat | = (recycle has no HvacState mode) | kMirageAc{Heat..Fan}, ir_Mirage.h | test_mode_uses_its_documented_value |
| fan | auto 1-3 | = | kMirageAcFan{Auto,Low,Med,High} | test_every_fan_level_uses_its_documented_code |
| swing_v | off auto 1-5 | = | kMirageAcSwingV*, SwingAndPower | test_kkg9ac1_swing_and_power_share_a_field, test_kkg29ac1_offers_no_swing_v_position |
| swing_h | none | = (setSwingH is a no-op on KKG9AC1) | ir_Mirage.cpp setSwingH | (none) |
| powerful / sleep / light | on/off | = | Turbo_Kkg9ac1, Sleep_Kkg9ac1, Light_Kkg9ac1 | test_powerful_sets_turbo_in_cool_only, test_sleep_sets_the_documented_bit, test_kkg9ac1_light_is_a_state |

### KKG29AC1 (generic 2, Tronitechnik)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint, modes, fan | as KKG9AC1 | = | as above (kMirageAcKKG29AC1Fan*) | as above |
| swing_v | off auto 1-5 | **off auto. Removed no-op: positions 1-5** (each sent the same one bit as auto) | SwingV:1, ir_Mirage.h:123; setSwingV `_.SwingV = (position != kMirageAcSwingVOff)`, ir_Mirage.cpp:416; getSwingV returns kMirageAcSwingVAuto | test_kkg29ac1_swing_v_is_one_bit, test_kkg29ac1_offers_no_swing_v_position, test_a_legacy_kkg29ac1_angle_is_sent_as_c_sends_it |
| swing_h | off swing | = | SwingH:1 | test_kkg29ac1_swing_h_sets_the_documented_bit |
| powerful sleep light quiet cleaning purifier | on/off | = | Turbo_Kkg29ac1, Sleep_Kkg29ac1, LightToggle, Quiet, CleanToggle, Filter | test_kkg29ac1_state_features, test_kkg29ac1_toggle_* |

## TCL: `Tcl112AcDevice` (both variants, same capabilities)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-31 | = | kTcl112AcTempMin/Max, ir_Tcl.h:110-111 | test_setpoint_is_clamped_to_16_31, test_capabilities_offer_auto_and_half_degrees |
| step | 1 | **0.5. Added: half degrees** (HalfDegree bit; 31.5 is not possible, setTemp clamps to 31.0) | HalfDegree:1, ir_Tcl.h:77; setTemp, ir_Tcl.cpp:221-230 | test_every_half_degree_setpoint, test_port_reproduces_real_captures_but_timer_indicator (TestTcl112AcClass.Temperature's 16.5 C / 19.5 C states, library test states) |
| modes | cool dry fan heat | **auto cool dry fan heat. Added: auto** | kTcl112AcAuto = 8, ir_Tcl.h:100 | test_mode_uses_its_documented_value, test_auto_mode_is_sent, test_port_reproduces_the_auto_mode_state_but_its_sum |
| fan | auto 1-4 | = | kTcl112AcFan{Auto,Min,Low,Med,High} | test_every_fan_level_uses_its_documented_code |
| swing_v | off auto 1-5 | = | kTcl112AcSwingV* | test_every_swing_position_uses_its_documented_code |
| swing_h | off swing | = | SwingH | test_swing_h_sets_the_swing_h_bit |
| quiet | on/off | = (special message, already sent) | kTcl112AcSpecial | test_quiet_sends_the_special_message_first |
| purifier / light / powerful / economy | on/off | = | Health, Light, Turbo, Econo | test_feature_bits, test_powerful_forces_fan_high_and_swing |

## Technibel: `TechnibelAcDevice` (technibel, teco, alaska)

The "teco" variant is removed: every model has the Technibel capabilities.
Registrations in teco.py/alaska.py are unchanged.

| aspect | old technibel | old teco/alaska | new (all) | source | test |
|---|---|---|---|---|---|
| setpoint | 16-31 | 16-30 | 16-31 (teco/alaska gain 31) | kTechnibelAcTempMinC/MaxC, ir_Technibel.h:53-54 | test_teco_and_alaska_reach_31, test_every_setpoint_is_sent_in_celsius |
| modes | cool dry fan heat | auto + 4 | cool dry fan heat. **teco/alaska: auto removed** (no auto code; C sent it as cool) | kTechnibelAc{Cool,Dry,Fan,Heat}, ir_Technibel.h:63-66 | test_auto_is_sent_as_cool, test_every_model_has_the_full_technibel_capabilities |
| fan | 1-3 (no auto) | auto 1-3 | 1-3. **teco/alaska: fan auto removed** (no auto code; convertFan's default Low) | kTechnibelAcFan{Low,Medium,High}, ir_Technibel.h:59-61 | test_fan_auto_is_sent_as_low, test_legacy_teco_fan_auto_is_c_s_fan_low |
| swing_v | off swing | off swing | = | Swing:1 | test_swing_sets_the_documented_bit |
| sleep | on/off | on/off | = | Sleep:1 | test_sleep_sets_the_documented_bit |
| light | none | on/off | **teco/alaska: removed no-op** (the protocol has no light) | TechnibelProtocol has no light field | test_light_is_not_offered |

## Voltas: `VoltasDevice` (Unknown and 122LZF)

No change. Test: test_capabilities_are_what_the_protocol_documents.

| aspect | old = new | source |
|---|---|---|
| setpoint | 16-30, step 1 | kVoltasMinTemp/MaxTemp, ir_Voltas.h:79,81 |
| modes | cool dry fan heat (no auto) | kVoltas{Fan,Heat,Dry,Cool} |
| fan | auto 1-3 | kVoltasFan{Auto,Low,Med,High} |
| swing_v | off swing | setSwingV: 0b111 / 0b000 only |
| swing_h | off swing (Unknown); none (122LZF: setSwingH ignored) | setSwingH, setModel |
| economy, powerful, sleep | on/off (sent in cool only) | Econo, Turbo, Sleep |
| light | on/off | Light |

## Whirlpool: `WhirlpoolAcDevice` (capabilities per remote variant)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint DG11J13A | 18-32 | = | kWhirlpoolAcMinTemp/MaxTemp, ir_Whirlpool.h:114-115 | test_capabilities_offer_the_variants_setpoint_range, test_setpoint_counts_from_the_models_minimum |
| setpoint DG11J191 | 18-32 (31-32 sent as 30) | **16-30. Added: 16, 17. Removed: 31, 32** (they sent 30) | getTempOffset -2, ir_Whirlpool.cpp:189-194; _setTemp, ir_Whirlpool.cpp:202-205 | same, test_dg11j191_normalises_31_and_32_to_30_as_c_clamps, test_every_model_gets_its_variants_capabilities |
| modes | auto cool dry fan heat | = | kWhirlpoolAc{Heat,Auto,Cool,Dry,Fan} | test_mode_uses_its_documented_value |
| fan | auto 1-3 | = | kWhirlpoolAcFan{Auto,High,Medium,Low} | test_every_fan_level_uses_its_documented_code |
| swing_v | off swing | = | Swing1/Swing2 | test_swing_sets_swing1_and_swing2 |
| light / sleep / powerful | on/off | = | LightOff, Sleep, Super1/Super2 | test_light_clears_light_off, test_sleep_sets_fan_low, test_powerful_* |

## Samsung: `SamsungAcDevice`

No change. Test: test_capabilities_are_what_the_protocol_documents.

| aspect | old = new | source |
|---|---|---|
| setpoint | 16-30, step 1 | kSamsungAcMinTemp/MaxTemp |
| modes | auto cool dry heat fan | kSamsungAc{Auto..Heat} |
| fan | auto 1-3 | kSamsungAcFan{Auto,Low,Med,High} (Turbo is powerful) |
| swing_v / swing_h | off swing each | kSamsungAcSwingV/H/Both/Off |
| quiet, powerful, economy, light, purifier, cleaning | on/off | Quiet, FanSpecial Powerful/Econo, Display, Ion, CleanToggle10/11 |

## Deferred (documented, but not added)

- Samsung sleep: Sleep5/Sleep12 are a sleep timer. `_setSleepTimer`
  (ir_Samsung.cpp:752-756) sets them only with the off timer enabled, and the
  sleep time is the off-timer value. That makes it timer logic, which is excluded.
- Samsung Breeze/WindFree (FanSpecial kSamsungAcBreezeOn, ir_Samsung.cpp:73):
  one field write, but the feature vocabulary has no name for it.
- Kelvinator sleep: the header has only unnamed, commented bits ("Sleep Modes
  1 & 3" byte 0 bit 7, "Sleep mode 2" byte 12 bit 0, and mode 3's "related"
  bytes 12-14; ir_Kelvinator.h:44,78-84). There is no constant and no setter,
  and the semantics of the three modes are not documented.
- Mirage KKG29AC1 RecycleHeat and mode kMirageAcRecycle: no HvacState mode or
  feature name for them.
- Out of scope by rule: timers, clocks, IFeel/sensor temperature, Fahrenheit
  (Technibel UseFah), Voltas Wifi, Whirlpool 6th Sense/IFeel commands, Samsung
  beep.
