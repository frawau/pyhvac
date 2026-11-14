# Daikin capability audit (phase 4, section 2)

Sources: `irremote/src/ir_Daikin.h` (h:N), `ir_Daikin.cpp` (cpp:N), `IRac.cpp`
(IRac:N). Tests are in `tests/test_<device>_device.py`. "=" means unchanged.

Shared fan ladder (DaikinArc, Daikin2, Daikin152, Daikin312), `DAIKIN_FAN_CHOICE`:
`auto`=0xA (kDaikinFanAuto h:151), `1` quiet=0xB (kDaikinFanQuiet h:152),
`2` low=3, `3` medium-low=4, `4` medium=5, `5` high=6, `6` highest=7
(kDaikinFanMin..Max h:148-150, setFan cpp:240 "speed + 2"). Old labels low/medium/high
stay on the bytes IRac sent for kLow/kMedium/kHigh (convertFan cpp:494), so every
oracle record maps to the same frame.

## DaikinArcDevice (DAIKIN, ARC433 etc.)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 10-32 | = | kDaikinMin/MaxTemp h:146-147 | (existing) |
| step | 0.5 | = | Temp = °C×2, h:104 | test_half_degree_setpoints_are_sent |
| modes | auto dry cool heat fan | = | kDaikinAuto..Fan h:141-145 | - |
| fan | auto 1-3 (low/medium/high) | **auto + 1-6** (quiet, 5 speeds) | h:148-152, cpp:240 | test_every_fan_step_uses_its_documented_value, test_old_fan_labels_are_the_speeds_the_c_path_sent |
| swing_v | off/swing | = | kDaikinSwingOn/Off h:153-154 | test_swing_sends_the_documented_value |
| swing_h | off/swing | = | h:112 | same |
| economy, powerful, quiet, cleaning | on/off | = | Powerful/Quiet/Econo/Mold h:118-133 | (existing) |

Real capture: none has a new value (RealExample is fan auto).

## Daikin2Device (DAIKIN2, ARC477A1, FTXZ*)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 10-32 | = (union); **normalise raises cool to 18 when on** | kDaikin2MinCoolTemp h:326, setTemp cpp:828 | test_normalise_reports_the_cool_minimum |
| step | 1 | = | Temp:6 whole °C | - |
| modes | 5 | = | - | - |
| fan | auto 1-3 | **auto + 1-6** | as shared ladder | test_every_fan_step_uses_its_documented_value, test_old_fan_labels_are_the_speeds_the_c_path_sent, test_real_capture_with_quiet_fan_light_and_swing_h_auto, test_real_capture_with_fan_speed_3 |
| swing_v | off auto 1-6 | = | kDaikin2SwingV* h:290-299 (as ported) | - |
| swing_h | off 1-6 | **+ auto (0xBE)** | kDaikin2SwingHAuto h:309 | test_swing_h_auto_is_kdaikin2swinghauto, real capture Issue1035 |
| economy, powerful, quiet, cleaning, purifier | on/off | = | Mold h:206, Powerful/Quiet h:255, Econo/Purify h:266 | (existing) |
| light | - | **added** (1 bright / 3 off, as IRac) | Light:2 byte 7 h:201, kDaikinLightBright/Off h:168-170, IRac daikin2 `setLight(light ? 1 : 3)` | test_light_as_irac_sends_it, real capture Issue1035 (Light: 1) |

Defect updated: swing_h off -> C value now reads as "auto" (was raw 0xBE).

## Daikin152Device (DAIKIN152, ARC480A5)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 10-32 | = (union); **normalise: 18 floor outside heat when on** | setTemp cpp:3170 (kDaikinMinTemp heat, kDaikin2MinCoolTemp else) | test_normalise_reports_the_per_mode_floor, test_normalise_keeps_the_setpoint_of_an_off_state |
| step | 1 | = | Temp:7 whole °C | - |
| modes | 5 | = | - | - |
| fan | auto 1-3 | **auto + 1-6** | setFan (ESP's), convertFan -> IRDaikinESP cpp:3212 | test_every_fan_step_uses_its_documented_value, test_old_fan_labels..., **test_real_capture_with_fan_speed_2** (RealExample, Fan: 2, byte for byte) |
| swing_v | off/swing | = | SwingV:4 h:598, kDaikinSwingOn h:153 | - |
| economy, powerful, quiet | on/off | = | Powerful/Quiet h:603-605, Econo h:612 | - |

## Daikin160Device (DAIKIN160, ARC423A5)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 10-32 | = | setTemp cpp:1877 | - |
| modes | 5 | = | - | - |
| fan | auto 1-3 (4,5,6) | **auto + 1-5 (3..7), FAN_5 labels** | setFan cpp:1890, convertFan cpp:1912 (kMin..kMax -> speeds 1..5) | test_every_fan_speed_uses_its_documented_value, test_old_fan_labels_are_the_speeds_the_c_path_sent |
| swing_v | off auto 1-5 | **removed "off"** (it was sent as auto) | only kDaikin160SwingVLowest..Highest + Auto h:427-432; setSwingVertical cpp:1926 | test_swing_off_is_not_offered |

Oracle: records with old swing "off" are read as "auto" by the test's `c_record()`
(C sent kDaikin160SwingVAuto for them: convertSwingV default).

## Daikin176Device (DAIKIN176, BRC4C153 etc.)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 10-32 | = (dry/fan send kDaikin176DryFanTemp in frames, as C: not a clamp, the setpoint is kept) | h:504, setTemp cpp:2263 | (existing) |
| modes | 5 | = | kDaikin176Fan..Dry h:498-502 | - |
| fan | 1 (low), 2 (high), no auto | = | setFan cpp:2282 accepts kDaikinFanMin, kDaikin176FanMax only | (existing) |
| swing_h | off/swing | = | kDaikin176SwingHAuto/Off h:506-507 | (existing) |

No change; capability test deleted.

## Daikin216Device (DAIKIN216, ARC433B69 etc.)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 10-32 | = | setTemp cpp:1535 | - |
| modes | 5 | = | - | - |
| fan | auto 1-3 | **auto + 1-5** (low, medium-low, medium, high, highest) | setFan cpp:1548 | test_every_fan_speed_uses_its_documented_value, test_old_fan_labels_are_the_speeds_the_c_path_sent |
| fan quiet (0xB) | via quiet feature | = (kept as the feature, not a fan step) | setQuiet cpp:1598 | test_quiet_is_not_a_fan_step, test_quiet_is_a_fan_speed |
| swing_v, swing_h | off/swing | = | kDaikin216SwingOn/Off h:379-380 | - |
| powerful, quiet | on/off | = | - | - |

## Daikin312Device (DAIKIN312, ARC466A67, FTXM20R5V1B)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 10-32 | = (union); **normalise raises cool to 18 when on** | kDaikin312MinCoolTemp h:862, setTemp cpp:3975 | test_normalise_reports_the_cool_minimum |
| step | 0.5 | = | Temp:7 half degrees | test_half_degree_setpoint |
| modes | 5 | = | - | - |
| fan | auto 1-3 | **auto + 1-6** | convertFan -> IRDaikinESP cpp:4316, setFan cpp:3993 | test_every_fan_step_uses_its_documented_value, test_old_fan_labels... |
| swing_v | off/swing | **off, swing, 1-6** (Daikin2's labels) | kDaikin312SwingV* h:824-833 | test_every_swing_v_position_uses_its_documented_value |
| swing_h | off/swing | = (positions not offered) | h:775 SwingH:4 vs kDaikin312SwingH* 0xA3..0xAC h:836-841 | test_swing_h_has_no_positions |
| quiet, powerful, light, economy, purifier, cleaning | on/off | = | - | (existing) |

## Daikin64Device (DAIKIN64, DGS01 etc.)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-30 | = | kDaikin64Min/MaxTemp h:681-682 | - |
| modes | dry cool heat fan | = (no auto in header) | kDaikin64Dry..Heat h:671-674 | - |
| fan | auto 1-5 (quiet..turbo) | = | kDaikin64Fan* h:675-680 | (existing) |
| swing_v | off/swing | = | SwingV:1 | - |
| sleep | - | **added** | Sleep:1 byte 7 bit 1 h:651, setSleep cpp:3624 | test_sleep_sets_the_documented_bit |

## Daikin128Device (DAIKIN128, BRC52B63, 17 Series)

| aspect | old | new | source | test |
|---|---|---|---|---|
| setpoint | 16-30 | = | kDaikin128Min/MaxTemp h:576-577 | - |
| modes | 5 | = | kDaikin128Dry..Auto h:565-569 | - |
| fan | auto 1-5 (quiet..powerful) | = | kDaikin128Fan* h:570-575 | (existing) |
| swing_v | off/swing | = | SwingV:1 | - |
| economy | on/off | = | - | - |
| sleep | - | **added** | Sleep:1 byte 7 bit 1 h:534, setSleep cpp:2714 | test_sleep_sets_the_documented_bit |
| light | - | **added, toggle on the Wall bit** (set when it changes; without previous: when on) | Wall bit h:544, kDaikin128BitWall h:578, setLightToggle cpp:2826, IRac daikin128 `setLightToggle(light ? kDaikin128BitWall : 0)`, IRac::handleToggles DAIKIN128 `light ^ prev->light` | test_light_without_previous_follows_the_c_path, test_light_toggles_only_when_it_changes |

## Removed no-ops

- Daikin160 swing_v "off" (sent the same frame as "auto"; not in the header).
- No feature was a no-op: every offered feature writes a field in every message.

## Deferred / not offered

- Daikin2, Daikin312: swing_v Breeze (0xC) and Circulate (0xD) (kDaikin2SwingVBreeze/Circulate h:296-297, kDaikin312SwingVBreeze/Circulate h:830-831): documented values, but no canonical HvacState name (they are airflow modes, not positions). Encodable by a field write once a name is agreed.
- Daikin312: swing_h positions (kDaikin312SwingH*, h:836-841): 8-bit constants for a 4-bit field; the header is self-contradictory. Needs a capture before offering.
- Daikin128: Ceiling light bit (kDaikin128BitCeiling) for ceiling units: would need a per-model variant; IRac only sends Wall.
- Outside the feature vocabulary (not offered, not deferred): Comfort (ESP, 152), Sensor/Eye/EyeAuto (ESP, 152, Daikin2, 312), FreshAir/FreshAirHigh, Beep, Humidity (Daikin2, 312), light dim level (kDaikinLightDim), 176 unit Id.
- Excluded by the spec: timers (On/Off/Sleep timers, WeeklyTimer), clock, current day.
