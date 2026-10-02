# SmartIR climate import

- covered: 4
- near: 196
- unknown: 143
- unsupported: 13

## Files

Skipped: codes that could not be read; flagged (!) when they are over 10% of the file.

| file | brand | verdict | candidate | units | verified | skipped | gaps |
|---|---|---|---|---|---|---|---|
| 1000 | Toyotomi | near | GreeDevice/YX1FSF | C | 118/181 | 0 | swing_v (60), temp (4), mode (1) |
| 1001 | Toyotomi | unknown |  |  | 0/241 | 0 |  |
| 1020 | Panasonic | near | PanasonicAcDevice/JKE | C | 0/121 | 0 | model_13 (118), mode (1) |
| 1021 | Panasonic | near | PanasonicAcDevice/DKE | C | 0/121 | 0 | byte 20 bit 7 (121), swing_h (121), byte 19 bit 3 (121), model_23 (121), mode (1) |
| 1022 | Panasonic | near | PanasonicAcDevice/RKR | C | 167/349 | 0 | byte 14 bit 0 (154), mode (1) |
| 1023 | Panasonic | near | PanasonicAcDevice/JKE | C | 0/361 | 0 | swing_h (361), model_13 (361), temperature (84), power (2) |
| 1024 | Panasonic | near | PanasonicAcDevice/JKE | C | 0/241 | 0 | model_13 (239), fan (1), mode (1), power (1) |
| 1025 | Panasonic | near | PanasonicAcDevice/NKE | C | 0/25 | 0 | model_13 (25), clock (25), mode (16) |
| 1026 | Panasonic | near | PanasonicAcDevice/JKE | C | 0/181 | 0 | model_13 (179), fan (74), mode (1) |
| 1027 | Panasonic | unknown |  |  | 0/181 | 0 |  |
| 1028 | Panasonic | near | PanasonicAcDevice/JKE | C | 0/271 | 0 | swing_h (271), model_13 (271), temperature (84), power (2) |
| 1029 | Panasonic | near | PanasonicAcDevice/DKE | C | 0/361 | 0 | swing_h (326), clock (2), model_23 (2), mode (1) |
| 1030 | Panasonic | near | PanasonicAcDevice/JKE | C | 0/2160 | 0 | model_13 (2055), temperature (486), swing_h (1), swing_v (1), fan (1) |
| 1031 | Panasonic | near | MitsubishiHeavy88Device | C | 157/209 | 0 | temperature (48), mode (14), fan (13) |
| 1032 | Panasonic | near | PanasonicAcDevice/NKE | C | 0/301 | 0 | model_23 (295), temperature (70), fan (60), powerful (45), mode (1) |
| 1040 | Ggeneral Electric | near | ElectraAcDevice | C | 0/205 | 0 | swing_h (205), light_toggle (205), byte 2 bit 1 (187), byte 2 bit 0 (154), byte 3 bit 3 (154), byte 3 bit 4 (154), byte 2 bit 3 (136), byte 3 bit 2 (119), byte 3 bit 0 (94), byte 2 bit 4 (69), byte 2 bit 2 (68), temperature (68), byte 3 bit 1 (58), fan (17), mode (1) |
| 1041 | Ggeneral Electric | unknown |  |  | 0/301 | 0 |  |
| 1042 | Ggeneral Electric | near | FujitsuAcDevice/ARRAH2E | C | 223/336 | 0 | byte 15 bit 7 (40), byte 15 bit 6 (40), byte 15 bit 2 (39), byte 8 bit 6 (35), byte 8 bit 7 (35), byte 15 bit 4 (30), byte 8 bit 4 (30), byte 15 bit 5 (30), byte 8 bit 5 (30), byte 15 bit 0 (26), byte 15 bit 1 (26), byte 10 bit 0 (26), byte 10 bit 1 (26), byte 10 bit 2 (13) |
| 1043 | General Electric | unknown |  |  | 0/336 | 0 |  |
| 1044 | General Electric | near | HaierYrw02Device/A | F | 0/365 | 0 | swing_h (357), use_fahrenheit (357), button (356), extra_degree_f (121), temperature (119), quiet (78), mode (1) |
| 1060 | LG | near | LgAcDevice/GE6711AR2853M | C | 209/261 | 0 | temp (52) |
| 1061 | LG | near | Lg2Device/AKB74955603 | C | 1/361 | 0 | unnamed (246), temperature (168), frames (90), fan (85) |
| 1062 | LG | near | LgAcDevice/GE6711AR2853M | C | 152/261 | 0 | temp (84), unused (39) |
| 1063 | LG | near | Lg2Device/AKB74955603 | C | 244/391 | 0 | temperature (144) |
| 1064 | LG | near | LgAcDevice/GE6711AR2853M | C | 53/79 | 0 | fan (26) |
| 1065 | LG | near | LgNativeDevice/generic | C | 1/181 | 0 | fan (175), change (174), temp (101), mode (43) |
| 1066 | LG | near | Lg2Device/AKB74955603 | C | 234/391 | 0 | temperature (132), fan (11) |
| 1067 | LG | covered | LgAcDevice/GE6711AR2853M | C | 79/79 | 0 |  |
| 1068 | LG | near | Lg2Device/AKB74955603 | C | 85/313 | 0 | temperature (150), frames (78), fan (6), power (6) |
| 1069 | LG | near | Lg2Device/AKB74955603 | C | 104/209 | 0 | temperature (96) |
| 1070 | LG | near | Lg2Device/AKB74955603 | C | 162/261 | 0 | temperature (84) |
| 1080 | Hitachi | near | Hitachi264Device | C | 0/136 | 0 | button (135), mode (1), temperature (1) |
| 1081 | Hitachi | near | Hitachi296Device | C | 8/137 | 0 | byte 11 bit 1 (121), byte 11 bit 0 (121), byte 11 bit 2 (121), byte 9 bit 3 (34), byte 9 bit 1 (34), temperature (9), unset_high (8), byte 11 bit 6 (1), byte 11 bit 4 (1), mode (1) |
| 1082 | Hitachi | unknown |  |  | 0/341 | 0 |  |
| 1083 | LG | near | Hitachi264Device | C | 0/205 | 0 | button (203), fan (50), byte 13 bit 0 (1), temperature (1), mode (1) |
| 1084 | Hitachi | unknown |  |  | 0/358 | 0 |  |
| 1085 | Hitachi | near | Mitsubishi112Device | C | 0/38 | 0 | swing_h (35), swing_v (35), byte 11 bit 7 (35), temperature (5), mode (1) |
| 1086 | Hitachi | unknown |  |  | 0/144 | 0 |  |
| 1087 | Hitachi | unknown |  |  | 0/426 | 0 |  |
| 1088 | Hitachi | unknown |  |  | 0/426 | 0 |  |
| 1089 | Hitachi | unknown |  |  | 0/358 | 0 |  |
| 1090 | Hitachi | near | HitachiAcDevice | C | 0/1701 | 0 | byte 23 bit 0 (1701), swing_h (850), temperature (340), fan (204), min_temp (20) |
| 1091 | Hitachi | near | KelonDevice | C | 0/452 | 0 | power_toggle (444), temperature (253), fan (233), smart (90), frames (1), swing_toggle (1) |
| 1092 | Hitachi | unknown |  |  | 0/205 | 0 |  |
| 1100 | Daikin | near | PanasonicAcDevice/JKE | C | 0/261 | 0 | byte 2 bit 7 (255), byte 3 bit 6 (255), byte 2 bit 0 (255), byte 2 bit 2 (255), byte 8 bit 0 (255), byte 0 bit 0 (255), byte 1 bit 7 (255), byte 3 bit 7 (255), byte 3 bit 2 (255), byte 9 bit 4 (255), byte 1 bit 6 (255), byte 9 bit 6 (255), byte 1 bit 1 (255), byte 10 bit 6 (255), byte 15 bit 7 (255), swing_v (255), byte 9 bit 5 (255), byte 7 bit 2 (255), byte 11 bit 2 (255), byte 8 bit 1 (255), byte 3 bit 5 (255), byte 9 bit 1 (255), byte 0 bit 1 (255), on_timer (255), byte 10 bit 2 (255), off_timer (255), byte 20 bit 7 (255), byte 9 bit 3 (255), byte 9 bit 7 (255), byte 1 bit 4 (255), byte 2 bit 6 (255), model_23 (255), byte 10 bit 7 (255), byte 10 bit 1 (255), byte 2 bit 1 (255), byte 8 bit 4 (255), byte 0 bit 4 (255), byte 1 bit 3 (255), byte 3 bit 4 (255), byte 19 bit 3 (255), byte 1 bit 5 (255), byte 10 bit 0 (255), fan (89), temperature (53), byte 14 bit 6 (52), byte 14 bit 7 (52), mode (13) |
| 1101 | Daikin | unknown |  |  | 0/521 | 0 |  |
| 1102 | Daikin | near | Daikin64Device | C | 0/271 | 0 | byte 4 bit 1 (271), byte 5 bit 5 (271), power (271), byte 5 bit 4 (271), byte 5 bit 2 (271), byte 3 bit 4 (271), byte 5 bit 0 (271), byte 4 bit 6 (271), byte 2 bit 5 (233), byte 3 bit 2 (181), byte 2 bit 0 (154), byte 2 bit 4 (129), byte 3 bit 0 (121), byte 2 bit 6 (120), fan (120), byte 2 bit 1 (109), byte 3 bit 1 (91), temperature (84), byte 2 bit 3 (30), byte 2 bit 2 (22), byte 3 bit 3 (1) |
| 1103 | Daikin | unknown |  |  | 0/65 | 0 |  |
| 1104 | Daikin | unknown |  |  | 0/316 | 0 |  |
| 1105 | Dalkin | unknown |  |  | 0/1036 | 0 |  |
| 1106 | Daikin | unknown |  |  | 0/456 | 0 |  |
| 1107 | Daikin | unknown |  |  | 0/313 | 0 |  |
| 1108 | Daikin | unknown |  |  | 0/601 | 0 |  |
| 1109 | Daikin | near | Daikin176Device | C | 0/193 | 0 | alt_mode (186), fan (94), mode_button (49), mode (1), temperature (1) |
| 1110 | Daikin | near | Daikin152Device | C | 0/181 | 0 | byte 18 bit 3 (178), temperature (116), fan (45), mode (15) |
| 1111 | Daikin | near | Daikin160Device | C | 66/67 | 0 | mode (1) |
| 1112 | Daikin | unknown |  |  | 0/361 | 0 |  |
| 1113 | Daikin | unknown |  |  | 0/598 | 0 |  |
| 1114 | Daikin | unknown |  |  | 0/520 | 0 |  |
| 1115 | Daikin | near | Daikin128Device | C | 0/1801 | 0 | power (1696), off_hours (1696), on_half_hour (1696), on_hours (1696), clock_hours (1696), clock_mins (1693), fan (541), temperature (420), mode (282), byte 15 bit 2 (281), swing_v (4) |
| 1116 | Daikin | unknown |  |  | 0/205 | 0 |  |
| 1117 | Daikin | unknown |  |  | 0/553 | 0 |  |
| 1118 | Daikin | unknown |  |  | 0/85 | 0 |  |
| 1119 | Daikin | unknown |  |  | 0/43 | 0 |  |
| 1120 | Mitsubishi Electric | unknown |  |  | 0/180 | 1 |  |
| 1121 | Mitsubishi Electric | unknown |  |  | 0/65 | 0 |  |
| 1122 | Mitsubishi | unknown |  |  | 0/265 | 0 |  |
| 1123 | Mitsubishi Electric | unknown |  |  | 0/91 | 0 |  |
| 1124 | Mitsubishi | unknown |  |  | 0/481 | 0 |  |
| 1125 | Mitsubishi Electric | unknown |  |  | 0/257 | 0 |  |
| 1126 | Mitsubishi Electric | unknown |  |  | 0/257 | 0 |  |
| 1127 | Mitsubishi Electric | unknown |  |  | 0/161 | 0 |  |
| 1128 | Mitsubishi Electric | near | MitsubishiAcDevice | C | 0/321 | 0 | swing_h (302), clock (302), temperature (145), mode_aux (77), vane_bit (49), fan_auto (40), fan (1), mode (1) |
| 1129 | Mitsubishi Electric  | near | MitsubishiAcDevice | C | 0/2689 | 0 | swing_h (2584), clock (2584), swing_v (2278), fan_auto (925), temperature (661), mode_aux (642), fan (450), vane_bit (237) |
| 1130 | Mitsubishi Electric | near | MitsubishiAcDevice | C | 0/193 | 0 | swing_h (176), swing_v (176), clock (176), temperature (105), mode_aux (49), vane_bit (32), fan_auto (17), mode (1) |
| 1131 | Mitsubishi Electric | near | Mitsubishi136Device | C | 87/145 | 0 | temperature (44), mode (1) |
| 1132 | Mitsubishi Electric | near | Mitsubishi112Device | C | 0/193 | 0 | swing_h (193), byte 5 bit 7 (193), temperature (120), mode (1) |
| 1133 | Mitsubishi Electric Starmex | near | MitsubishiAcDevice | C | 0/2129 | 0 | swing_h (2011), clock (2011), swing_v (1722), temperature (1260), mode_aux (673), fan_auto (322), frames (112), vane_bit (99), fan (16), mode (1) |
| 1134 | Mitsubishi Electric | near | MitsubishiAcDevice | C | 0/241 | 0 | swing_h (237), swing_v (237), clock (237), temperature (150), mode_aux (81), fan_auto (54), vane_bit (10), mode (1) |
| 1135 | Mitsubishi | near | MitsubishiAcDevice | C | 0/481 | 0 | swing_h (474), clock (474), mode_aux (189), temperature (180), fan_auto (100), swing_v (64), vane_bit (34), mode (1) |
| 1136 | Mitsubishi Electric | unknown |  |  | 0/289 | 0 |  |
| 1137 | Mitsubishi Electric | unknown |  |  | 0/2241 | 0 |  |
| 1138 | Mitsubishi Electric | near | MitsubishiAcDevice | C | 0/321 | 0 | isee (309), swing_h (309), byte 14 bit 4 (309), byte 32 bit 4 (309), clock (309), mode_aux (77), mode (77), temperature (75), fan_auto (62), ecocool (17), fan (1) |
| 1139 | Mitsubishi | unknown |  |  | 0/58 | 0 |  |
| 1140 | Actron | covered | CoolixDevice | C | 113/113 | 0 |  |
| 1160 | Carrier | near | CoolixDevice | C | 181/281 | 0 | fan (97), temp (2) |
| 1161 | Carrier | unknown |  |  | 0/181 | 0 |  |
| 1162 | Carrier | unknown |  |  | 0/57 | 0 |  |
| 1163 | Carrier | near | MideaDevice | F | 0/501 | 0 | fahrenheit (465), temperature (448), fan (135), unknown (70) |
| 1164 | Carrier | near | CoolixDevice | C | 191/238 | 1 | fan (39), temp (1) |
| 1165 | Carrier | near | LgAcDevice/GE6711AR2853M | C | 0/321 | 0 | unused (319), mode (319), byte 3 bit 1 (319), sign (319), fan (303), temp (299), byte 3 bit 0 (65), byte 3 bit 3 (65), byte 3 bit 2 (65), power (1) |
| 1166 | Carrier | near | LgAcDevice/GE6711AR2853M | C | 0/130 | 0 | unused (129), mode (129), byte 3 bit 1 (129), sign (129), fan (124), temp (121), frames (1), byte 3 bit 0 (1), power (1) |
| 1180 | Gree | unknown |  |  | 0/301 | 0 |  |
| 1181 | Gree | unknown |  |  | 0/79 | 0 |  |
| 1182 | Gree | unknown |  |  | 0/301 | 0 |  |
| 1183 | Gree | unknown |  |  | 0/961 | 0 |  |
| 1184 | Gree | unknown |  |  | 0/301 | 0 |  |
| 1185 | Gree | near | GreeDevice/YX1FSF | C | 225/301 | 0 | byte 7 bit 3 (60), light (14), mode (1), temp (1) |
| 1186 | Gree | unknown |  |  | 0/60 | 0 |  |
| 1187 | Gree | unknown |  |  | 0/61 | 0 |  |
| 1188 | Gree | unknown |  |  | 0/521 | 0 |  |
| 1200 | Tosot | near | GreeDevice/YAW1F | C | 0/301 | 0 | swing_v (180), swing_auto (180), display_temp (121), xfan (120), model_a (1), mode (1), temp (1) |
| 1220 | Sungold | near | MideaDevice | F | 0/201 | 0 | fahrenheit (201), temperature (192), unknown (61), fan (11) |
| 1240 | Consul | unknown |  |  | 0/118 | 0 |  |
| 1241 | Consul | near | KelonDevice | C | 0/241 | 0 | power_toggle (219), fan (60), dry_grade (45) |
| 1260 | Toshiba | unknown |  |  | 0/281 | 0 |  |
| 1261 |  Toshiba | unknown |  |  | 0/421 | 0 |  |
| 1262 | Toshiba | unknown |  |  | 0/354 | 0 |  |
| 1263 | Toshiba | unknown |  |  | 0/421 | 0 |  |
| 1264 | Toshiba | unknown |  |  | 0/421 | 0 |  |
| 1265 | Toshiba | unknown |  |  | 0/316 | 0 |  |
| 1280 | Fujitsu | near | FujitsuAcDevice/ARRAH2E | C | 1/144 | 52 (!) | byte 8 bit 0 (134), byte 15 bit 0 (86), byte 10 bit 0 (48), byte 15 bit 1 (48), byte 15 bit 2 (23), byte 15 bit 3 (12) |
| 1281 | Fujitsu | near | FujitsuAcDevice/ARRAH2E | C | 1/700 | 1 | byte 8 bit 5 (409), byte 15 bit 5 (405), byte 15 bit 0 (346), byte 8 bit 0 (346), byte 15 bit 6 (238), byte 15 bit 1 (207), byte 8 bit 6 (190), byte 15 bit 2 (167), byte 15 bit 7 (142), byte 8 bit 7 (90), byte 15 bit 4 (61), byte 10 bit 0 (56), byte 10 bit 1 (56), byte 8 bit 4 (50), byte 10 bit 2 (28), byte 15 bit 3 (27) |
| 1282 | Fujitsu | near | FujitsuAcDevice/ARDB1 | C | 218/375 | 1 | frames (135), byte 8 bit 5 (22), byte 14 bit 5 (11), byte 14 bit 6 (11), byte 8 bit 4 (11), byte 14 bit 4 (11) |
| 1283 | Fujitsu | near | DelonghiAcDevice | C | 0/157 | 0 | byte 2 bit 7 (145), byte 0 bit 6 (145), power (145), on_mins (145), byte 0 bit 2 (145), byte 0 bit 0 (145), fahrenheit (145), mode (145), byte 0 bit 1 (145), on_timer (145), temperature (133), on_hours (113), byte 3 bit 7 (82), byte 3 bit 6 (79), fan (44), frames (1) |
| 1284 | Fujitsu | unknown |  |  | 0/326 | 0 |  |
| 1285 | Fujitsu | unknown |  |  | 0/376 | 0 |  |
| 1286 | Fujitsu | near | FujitsuAcDevice/ARDB1 | C | 200/326 | 0 | byte 9 bit 1 (65), byte 9 bit 0 (65), byte 14 bit 7 (40), byte 14 bit 1 (39), byte 14 bit 0 (39), byte 14 bit 2 (39), byte 14 bit 6 (35), byte 8 bit 7 (30), byte 8 bit 6 (30), byte 8 bit 4 (30), byte 14 bit 5 (30), byte 14 bit 4 (30), byte 8 bit 5 (30), byte 10 bit 0 (26), byte 10 bit 1 (26), byte 10 bit 2 (13) |
| 1287 | Fujitsu | near | FujitsuAcDevice/ARRAH2E | C | 224/336 | 0 | byte 15 bit 7 (40), byte 15 bit 6 (40), byte 15 bit 2 (39), byte 8 bit 6 (35), byte 8 bit 7 (35), byte 15 bit 4 (30), byte 8 bit 4 (30), byte 15 bit 5 (30), byte 8 bit 5 (30), byte 10 bit 0 (26), byte 15 bit 0 (26), byte 10 bit 1 (26), byte 15 bit 1 (26), byte 10 bit 2 (13) |
| 1288 | Fujitsu | near | CarrierAc64Device | C | 0/209 | 0 | byte 0 bit 7 (192), byte 0 bit 4 (192), temperature (192), byte 1 bit 3 (192), byte 1 bit 7 (192), byte 1 bit 2 (192), byte 1 bit 4 (192), byte 1 bit 5 (192), on_timer (192), byte 1 bit 1 (192), off_timer (192), mode (142), byte 3 bit 6 (121), byte 3 bit 7 (121), power (115), byte 4 bit 1 (102), byte 4 bit 2 (101), byte 4 bit 0 (89), off_timer_enable (76), byte 3 bit 4 (71), swing_v (70), frames (1) |
| 1289 | Fujitsu | near | FujitsuAcDevice/ARREW4E | C | 1/209 | 52 (!) | byte 14 bit 5 (192), byte 14 bit 0 (192), byte 12 bit 2 (192), byte 11 bit 3 (192), byte 15 bit 7 (164), byte 11 bit 4 (128), byte 13 bit 0 (116), byte 15 bit 0 (107), byte 15 bit 1 (106), byte 13 bit 6 (101), byte 15 bit 2 (100), byte 15 bit 4 (95), byte 11 bit 0 (89), byte 15 bit 6 (87), byte 15 bit 5 (83), byte 13 bit 3 (72), byte 15 bit 3 (67), byte 13 bit 5 (65), byte 12 bit 0 (64), byte 13 bit 2 (63), byte 13 bit 1 (59), byte 13 bit 4 (42), byte 8 bit 4 (28), byte 8 bit 3 (28), byte 8 bit 7 (24), byte 8 bit 5 (24), byte 8 bit 6 (24) |
| 1290 | Fujitsu | unknown |  |  | 0/376 | 0 |  |
| 1291 | Fujitsu | unknown |  |  | 0/210 | 52 (!) |  |
| 1292 | Fujitsu | near | FujitsuAcDevice/ARRAH2E | C | 426/1301 | 0 | byte 10 bit 5 (648), byte 15 bit 5 (503), byte 15 bit 4 (385), byte 10 bit 4 (325), byte 15 bit 6 (324), byte 15 bit 7 (219), byte 15 bit 2 (156), byte 8 bit 7 (120), byte 8 bit 6 (120), byte 8 bit 4 (120), byte 8 bit 5 (120), byte 10 bit 0 (104), byte 15 bit 0 (104), byte 10 bit 1 (104), byte 15 bit 1 (104), byte 10 bit 2 (52) |
| 1293 | Fujitsu | near | FujitsuAcDevice/ARRAH2E | C | 426/651 | 0 | byte 15 bit 7 (80), byte 15 bit 2 (78), byte 15 bit 6 (65), byte 8 bit 7 (60), byte 8 bit 6 (60), byte 15 bit 4 (60), byte 8 bit 4 (60), byte 15 bit 5 (60), byte 8 bit 5 (60), byte 10 bit 0 (52), byte 15 bit 0 (52), byte 10 bit 1 (52), byte 15 bit 1 (52), byte 10 bit 2 (26) |
| 1294 | Fujitsu | unknown |  |  | 0/548 | 0 |  |
| 1300 | Sharp | near | SharpAcDevice/A907 | C | 0/301 | 0 | byte 9 bit 4 (223), swing (149), temp_flags (148), temperature (139), frames (75), fan (74), mode (1), byte 9 bit 5 (1) |
| 1301 | Sharp | near | SharpAcDevice/A903 | C | 15/241 | 0 | mode (121), temperature (117), temp_flags (60), fan (60) |
| 1320 | Haier | near | HaierYrw02Device/A | C | 0/301 | 0 | byte 2 bit 1 (301), byte 2 bit 4 (301) |
| 1321 | Haier | near | HaierYrw02Device/A | C | 0/181 | 0 | button (179), swing_v (120), swing_h (89), fan (10), mode (1), temperature (1) |
| 1322 | Haier | near | Haier176Device/A | C | 0/241 | 0 | swing_h (223), button (198), temperature (56), swing_v (54), fan (15), fan2 (15), frames (1) |
| 1340 | Tadiran | near | AmcorDevice | C | 57/136 | 0 | vent (76), temp (45), mode (1) |
| 1341 | Tadiran | unknown |  |  | 0/91 | 0 |  |
| 1342 | Tadiran | unknown |  |  | 0/121 | 0 |  |
| 1343 | Tadiran | unknown |  |  | 0/181 | 0 |  |
| 1344 | Tadiran | near | GreeDevice/YAW1F | C | 1059/1321 | 60 | swing_v (116), turbo (115), model_a (1), mode (1), xfan (1) |
| 1345 | Tadiran | unknown |  |  | 0/301 | 0 |  |
| 1346 | Tadiran | unknown |  |  | 0/137 | 0 |  |
| 1360 | Springer | near | CoolixDevice | C | 209/273 | 8 | temp (56), mode (52), fan (52) |
| 1380 | Midea | near | CoolixDevice | C | 114/157 | 0 | fan (37) |
| 1381 | Midea | near | CoolixDevice | C | 66/67 | 0 |  |
| 1382 | Midea | near | CoolixDevice | C | 205/281 | 0 | fan (70) |
| 1383 | Midea | near | CoolixDevice | C | 120/225 | 0 | fan (82), temp (40) |
| 1384 | Midea | near | CoolixDevice | C | 62/65 | 0 |  |
| 1385 | Midea | unknown |  |  | 0/281 | 0 |  |
| 1386 | Midea | unknown |  |  | 0/141 | 0 |  |
| 1387 | Midea | near | CoolixDevice | C | 153/281 | 0 | fan (105) |
| 1388 | Midea | unknown |  |  | 0/57 | 0 |  |
| 1389 | Midea | near | CoolixDevice | F | 194/289 | 0 | fan (72), temp (24) |
| 1390 | Midea | near | CoolixDevice | C | 154/281 | 0 | fan (105) |
| 1391 | Midea | near | CoolixDevice | C | 170/281 | 0 | fan (94), sensor_temp (3), temp (3), mode (1) |
| 1392 | Midea | near | MideaDevice | C | 49/127 | 0 | temperature (56), unknown (24) |
| 1393 | Midea | near | MideaDevice | C | 97/131 | 0 | unknown (30), temperature (4), mode (1) |
| 1394 | Midea | near | CoolixDevice | C | 194/281 | 0 | fan (84) |
| 1395 | Midea | near | MideaDevice | C | 112/284 | 0 | fan (122), temperature (57), unknown (42), frames (2), mode (1) |
| 1400 | Samsung | unknown |  |  | 0/449 | 2 |  |
| 1401 | Samsung | unknown |  |  | 0/240 | 1 |  |
| 1402 | Samsung | near | GreeDevice/YAW1F | C | 0/751 | 0 | byte 5 bit 5 (726), wifi (726), byte 5 bit 7 (726), xfan (298), turbo (58), temp (2), display_temp (1), mode (1) |
| 1403 | Samsung | unknown |  |  | 0/417 | 0 |  |
| 1404 | Samsung | unknown |  |  | 0/841 | 0 |  |
| 1405 | Samsung | near | CoolixDevice | C | 187/197 | 0 |  |
| 1406 | Samsung | unsupported |  |  | 0/0 | 195 (!) |  |
| 1407 | Samsung | unknown |  |  | 0/367 | 0 |  |
| 1408 | Samsung | unknown |  |  | 0/901 | 0 |  |
| 1420 | Sintech | unknown |  |  | 0/257 | 0 |  |
| 1440 | Akai | near | GoodweatherDevice | C | 193/341 | 0 | temperature (140), fan (51), air_flow (17), byte 8 bit 4 (12) |
| 1441 | Akai | near | Tcl112AcDevice/GZ055BE1 | C | 0/257 | 0 | timer_indicator (254), temperature (121), fan (64), mode (1) |
| 1460 | Alliance | near | CoolixDevice | C | 127/211 | 0 | fan (84) |
| 1480 | Junkers | near | GreeDevice/YAW1F | C | 45/181 | 0 | fan (76), model_a (60), byte 5 bit 5 (60), swing_v (60), swing_auto (60), display_temp (60), wifi (60), mode (1) |
| 1481 | Junkers | near | GreeDevice/YAW1F | C | 0/361 | 0 | display_temp (299), byte 5 bit 5 (60), wifi (60), model_a (60), swing_v (60), swing_auto (60), temp (11), mode (1) |
| 1500 | Sanyo | unknown |  |  | 0/157 | 0 |  |
| 1501 | Sanyo | near | DaikinNativeDevice | F | 0/286 | 0 | byte 2 bit 7 (284), byte 0 bit 7 (284), fan (284), power (284), byte 15 bit 1 (284), byte 2 bit 2 (284), byte 4 bit 2 (284), byte 12 bit 7 (284), byte 1 bit 6 (284), byte 7 bit 0 (284), byte 1 bit 1 (284), byte 12 bit 6 (284), byte 15 bit 7 (284), byte 1 bit 0 (284), swing_v (284), byte 15 bit 5 (284), byte 0 bit 3 (284), byte 7 bit 2 (284), byte 9 bit 1 (284), byte 0 bit 1 (284), byte 4 bit 5 (284), byte 7 bit 1 (284), byte 4 bit 1 (284), byte 10 bit 5 (284), byte 17 bit 4 (284), byte 15 bit 0 (284), byte 1 bit 4 (284), byte 2 bit 6 (284), byte 2 bit 3 (284), byte 10 bit 4 (284), byte 10 bit 1 (284), byte 4 bit 4 (284), byte 3 bit 0 (284), byte 9 bit 2 (284), byte 1 bit 3 (284), byte 4 bit 6 (284), temperature (276), byte 7 bit 5 (255), byte 7 bit 6 (254), byte 7 bit 7 (231), byte 11 bit 0 (223), byte 11 bit 3 (183), mode (164), byte 11 bit 5 (161), byte 11 bit 4 (160), byte 5 bit 5 (149), byte 5 bit 4 (148), byte 11 bit 7 (128), byte 11 bit 6 (108), byte 11 bit 2 (61), byte 11 bit 1 (61), powerful (30), byte 7 bit 4 (29), byte 5 bit 6 (15), off (1) |
| 1520 | Hisense | unknown |  |  | 0/261 | 0 |  |
| 1521 | Hisense | near | KelonDevice | C | 0/121 | 0 | power_toggle (59), frames (55) |
| 1522 | Hisense | near | KelonDevice | C | 2/361 | 0 | power_toggle (357), temperature (168), fan (105), dry_grade (84) |
| 1540 | Whirlpool | near | KelonDevice | C | 0/105 | 0 | power_toggle (96), mode (1) |
| 1560 | Tadiran | near | AmcorDevice | C | 57/136 | 0 | vent (76), temp (45), mode (1) |
| 1580 | Chigo | near | GoodweatherDevice | C | 1/118 | 0 | command (111), mode (36) |
| 1581 | Chigo | near | GoodweatherDevice | C | 0/290 | 0 | air_flow (286), command (285), mode (135), temperature (113), byte 8 bit 4 (14) |
| 1582 | Chigo | near | NeoclimaDevice | C | 0/222 | 0 | follow (222), byte 3 bit 5 (222), button (179), temp (80), mode (1) |
| 1600 | Beko | near | ElectraAcDevice | C | 0/154 | 0 | light_toggle (151), byte 9 bit 4 (51), swing_v (48), swing_h (2), temperature (1) |
| 1601 | Beko | unknown |  |  | 0/301 | 5 |  |
| 1602 | Beko | unknown |  |  | 0/321 | 0 |  |
| 1603 | Beko | near | HaierYrw02Device/A | C | 0/361 | 0 | swing_h (343), button (342), swing_v (15), mode (1) |
| 1604 | Beko | near | CoolixDevice | C | 192/229 | 2 | fan (26), temp (14) |
| 1620 | Tornado | near | CoolixDevice | C | 88/118 | 0 | fan (24) |
| 1621 | Tornado | near | KelonDevice | C | 0/121 | 0 | power_toggle (117), temperature (109) |
| 1622 | Tornado | near | ElectraAcDevice | C | 0/545 | 0 | light_toggle (530), byte 9 bit 4 (261), swing_h (261), mode (2), power (2), byte 6 bit 4 (1) |
| 1623 | Tornado | near | GoodweatherDevice | C | 0/91 | 0 | air_flow (89), command (88), swing_v (30), mode (1) |
| 1624 | Tornado | near | KelonDevice | C | 0/121 | 0 | power_toggle (117), temperature (109) |
| 1625 | Tornado | near | NeoclimaDevice | C | 0/91 | 0 | swing_h (88), follow (88), byte 3 bit 5 (88), button (86) |
| 1626 | Tornado | near | ElectraAcDevice | C | 0/121 | 0 | light_toggle (120), byte 9 bit 4 (60), mode (2), byte 4 bit 4 (1), fan (1), byte 6 bit 4 (1), power (1), byte 10 bit 7 (1) |
| 1627 | Tornado | near | KelonDevice | C | 119/241 | 0 | dry_grade (111), temperature (62), fan (44), power_toggle (1) |
| 1640 | FUJIKO | unknown |  |  | 0/301 | 0 |  |
| 1660 | ROYAL | unknown |  |  | 0/281 | 0 |  |
| 1661 | ROYAL | unknown |  |  | 0/385 | 0 |  |
| 1680 | Mitsubishi Heavy | unknown |  |  | 0/157 | 0 |  |
| 1681 | Mitsubishi Heavy | near | MitsubishiHeavy88Device | C | 51/196 | 0 | byte 5 bit 4 (122), swing_h (122), byte 5 bit 0 (122), fan (85) |
| 1682 | Mitsubishi Heavy | near | TranscoldDevice | C | 0/157 | 0 | byte 0 bit 4 (152), fan (152), mode (99), temp (1) |
| 1683 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 0/196 | 0 | swing_h (177), byte 13 bit 7 (177), temp (51), mode (1) |
| 1684 | Mitsubishi Heavy Industries | unknown |  |  | 0/121 | 0 |  |
| 1685 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 0/325 | 0 | swing_h (320), byte 13 bit 6 (320), byte 13 bit 5 (320), temp (60), fan (52), mode (1) |
| 1686 | Mitsubishi Heavy | unknown |  |  | 0/326 | 0 |  |
| 1687 | Mitsubishi Heavy | unknown |  |  | 0/157 | 0 |  |
| 1688 | Mitsubishi Heavy | unknown |  |  | 0/261 | 0 |  |
| 1689 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 0/326 | 4 | byte 13 bit 7 (296), swing_h (177), swing_v (177), byte 13 bit 6 (119), temp (51), fan (48), mode (1) |
| 1690 | Mitsubishi Heavy | unknown |  |  | 0/326 | 0 |  |
| 1691 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 0/976 | 0 | swing_h (905), byte 13 bit 6 (463), three (180), d (180), temp (170), fan (144), swing_v (137), byte 13 bit 5 (124), mode (1), power (1) |
| 1692 | Mitsubishi Heavy | unknown |  |  | 0/157 | 13 |  |
| 1700 | Electrolux | covered | CoolixDevice | C | 57/57 | 0 |  |
| 1701 | Electrolux | near | GreeDevice/YAW1F | C | 177/181 | 0 | mode (4), fan (3), temp (1) |
| 1702 | Electrolux | unknown |  |  | 0/362 | 14 |  |
| 1703 | Electrolux | near | ElectraAcDevice | C | 0/273 | 0 | light_toggle (273), temperature (138), fan (34), mode (1) |
| 1704 | Electrolux | near | CoolixDevice | C | 179/182 | 1 | temp (1) |
| 1705 | Electrolux | near | ElectraAcDevice | C | 0/545 | 0 | light_toggle (541), byte 9 bit 4 (138), temperature (136), fan (36), mode (3), power (2), byte 3 bit 7 (1), swing_h (1), byte 2 bit 4 (1), byte 10 bit 7 (1) |
| 1720 | Erisson | unknown |  |  | 0/321 | 0 |  |
| 1740 | Kelvinator | near | CoolixDevice | C | 248/351 | 0 | fan (98), byte 0 bit 2 (14), zone_follow1 (14), byte 0 bit 0 (14), byte 6 bit 2 (14), temp (14), byte 0 bit 1 (14), byte 6 bit 1 (14), byte 6 bit 0 (14), sensor_temp (14) |
| 1741 | Kelvinator | unknown |  |  | 0/451 | 0 |  |
| 1760 | Daitsu | near | CoolixDevice | C | 192/281 | 0 | fan (81) |
| 1761 | Daitsu | unknown |  |  | 0/321 | 0 |  |
| 1762 | Daitsu | near | Tcl112AcDevice/GZ055BE1 | C | 0/257 | 0 | quiet (195), msg_type (195), timer_indicator (195), mode (195), power (194), temperature (180), frames (40), byte 11 bit 1 (1), model (1) |
| 1763 | Daitsu | unknown |  |  | 0/301 | 0 |  |
| 1764 | Daitsu | near | GreeDevice/YAW1F | C | 0/301 | 0 | byte 5 bit 5 (271), byte 5 bit 7 (271), swing_v (44), mode (1), temp (1) |
| 1780 | Trotec | near | GreeDevice/YAW1F | C | 0/121 | 0 | byte 5 bit 5 (120), xfan (16), mode (1), temp (1) |
| 1781 | Trotec | near | GreeDevice/YAW1F | C | 203/226 | 0 | turbo (15), mode (1), temp (1) |
| 1782 | Trotec | near | MideaDevice | C | 59/169 | 0 | temperature (82), fan (57), unknown (14), mode (1) |
| 1800 | Ballu | near | ElectraAcDevice | C | 0/137 | 0 | light_toggle (135), byte 9 bit 4 (67), temperature (1) |
| 1801 | Ballu | near | CoolixDevice | C | 86/168 | 1 | fan (56), temp (36), sensor_temp (14) |
| 1820 | Riello | near | Hitachi264Device | C | 0/273 | 0 | byte 29 bit 2 (254), byte 31 bit 0 (254), byte 29 bit 1 (254), byte 31 bit 2 (254), byte 29 bit 5 (254), button (253), fan (65), temperature (64), frames (1) |
| 1840 | Hualing | near | Mitsubishi112Device | C | 0/257 | 0 | swing_h (250), temperature (118), mode (65), byte 6 bit 3 (64) |
| 1860 | Simbio | unknown |  |  | 0/129 | 0 |  |
| 1880 | Saunier Duval | near | GreeDevice/YAW1F | C | 120/121 | 0 | model_a (1), mode (1), temp (1) |
| 1900 | TCL | unknown |  |  | 0/33 | 0 |  |
| 1901 | TCL | near | Tcl112AcDevice/TAC09CHSD | C | 0/129 | 0 | quiet (110), fan (110), byte 8 bit 7 (110), timer_indicator (110), turbo (80), swing_v (56), swing_h (54), temperature (54), byte 7 bit 4 (54), byte 7 bit 7 (54), byte 6 bit 6 (30), frames (13) |
| 1920 | Aokesi | near | ElectraAcDevice | C | 0/118 | 0 | fan (118), light_toggle (118), byte 9 bit 4 (54), mode (40), temperature (1) |
| 1940 | Electra | near | AirwellDevice | C | 0/181 | 0 | power_toggle (179), mode (1), temperature (1) |
| 1941 | Electra | near | CoolixDevice | C | 173/181 | 0 | temp (8), mode (4) |
| 1942 | Electra | unknown |  |  | 0/203 | 2 |  |
| 1943 | Electra | near | CoolixDevice | C | 173/181 | 0 | temp (8), mode (4) |
| 1944 | Electra | near | CoolixDevice | C | 108/113 | 0 | temp (2) |
| 1945 | Electra | unknown |  |  | 0/56 | 11 (!) |  |
| 1946 | Electra | unknown |  |  | 0/181 | 0 |  |
| 1947 | Electra | unknown |  |  | 0/127 | 0 |  |
| 1948 | Electra | unknown |  |  | 0/241 | 0 |  |
| 1960 | AUX | near | ElectraAcDevice | C | 0/118 | 0 | fan (118), light_toggle (118), byte 9 bit 4 (54), mode (40), temperature (1) |
| 1961 | AUX | near | ElectraAcDevice | C | 0/991 | 0 | light_toggle (881), temperature (404), byte 3 bit 7 (284), fan (197), byte 9 bit 4 (195), quiet (165), turbo (66), frames (1), mode (1) |
| 1962 | AUX | near | ElectraAcDevice | C | 0/427 | 0 | light_toggle (405), temperature (171), byte 9 bit 4 (76), turbo (30), fan (17) |
| 1963 | AUX | near | ElectraAcDevice | C | 0/512 | 0 | light_toggle (453), temperature (204), fan (102), byte 9 bit 4 (100), quiet (85), turbo (34), byte 3 bit 7 (8), frames (1), mode (1) |
| 1980 | Fuji | covered | FujitsuAcDevice/ARDB1 | C | 79/79 | 0 |  |
| 2000 | Aeronik | near | GreeDevice/YAW1F | C | 0/301 | 0 | byte 5 bit 5 (299), display_temp (299), wifi (299), ifeel (298), swing_v (179), swing_auto (119), mode (1), temp (1) |
| 2020 | Ariston | near | CoolixDevice | C | 175/281 | 0 | fan (94), temp (5) |
| 2040 | Pioneer | near | MideaDevice | C | 0/501 | 0 | fahrenheit (488), temperature (472), fan (147), unknown (76), mode (1) |
| 2041 | Pioneer | unknown |  |  | 0/1121 | 0 |  |
| 2060 | Dimplex | near | Tcl112AcDevice/GZ055BE1 | C | 0/321 | 0 | timer_indicator (312), temperature (240), fan (139), byte 11 bit 0 (28), mode (1) |
| 2080 | Sendo | near | ElectraAcDevice | C | 0/205 | 0 | light_toggle (201), byte 9 bit 4 (68), mode (1) |
| 2100 | Mirage | unknown |  |  | 0/57 | 0 |  |
| 2120 | Technibel | unknown |  |  | 0/392 | 0 |  |
| 2140 | Unionaire | unknown |  |  | 0/91 | 0 |  |
| 2160 | Lennox | unknown |  |  | 0/227 | 1 |  |
| 2161 | Lennox | near | CoolixDevice | C | 124/281 | 0 | fan (140), mode (56), sensor_temp (56) |
| 2162 | Lennox | unknown |  |  | 0/331 | 0 |  |
| 2180 | Hokkaido | unknown |  |  | 0/122 | 0 |  |
| 2200 | IGC | near | KelonDevice | C | 0/241 | 0 | power_toggle (230), temperature (106), fan (57), dry_grade (52) |
| 2220 | Blueridge | near | MideaDevice | C | 0/526 | 0 | fahrenheit (496), temperature (476), fan (206), unknown (99), mode (22), byte 2 bit 7 (21), power (21), type (21) |
| 2240 | DeLonghi | near | LgAcDevice/GE6711AR2853M | F | 0/154 | 0 | sign (154), unused (120), byte 3 bit 3 (105), mode (102), power (52), fan (1), temp (1) |
| 2241 | DeLonghi | near | ElectraAcDevice | C | 0/181 | 0 | light_toggle (177), temperature (121), fan (60), mode (1) |
| 2242 | DeLonghi | unknown |  |  | 0/501 | 0 |  |
| 2243 | DeLonghi | near | Mitsubishi112Device | C | 0/321 | 0 | swing_h (311), swing_v (311), temperature (184), mode (65), fan (64), byte 6 bit 3 (64) |
| 2260 | Profio | unknown |  |  | 0/321 | 0 |  |
| 2280 | Hantech | unknown |  |  | 0/91 | 0 |  |
| 2281 | Hantech | unknown |  |  | 0/97 | 0 |  |
| 2300 | Zanussi | near | GoodweatherDevice | C | 0/242 | 0 | air_flow (237), command (236), temperature (56), mode (1) |
| 2301 | Zanussi | near | KelvinatorDevice | C | 0/151 | 0 | timer (143), turbo (30), fan (29), xfan (1), mode (1), ion_filter (1) |
| 2320 | Whynter | unknown |  |  | 0/225 | 3 |  |
| 2321 | Whynter | unknown |  |  | 0/205 | 2 |  |
| 2340 | Vortex | unknown |  |  | 0/241 | 0 |  |
| 2360 | Flouu | near | GreeDevice/YX1FSF | C | 0/196 | 0 | display_temp (191), mode (61), byte 7 bit 3 (59), temp (57), byte 5 bit 5 (1) |
| 2380 | BAXI | near | ElectraAcDevice | C | 0/627 | 34 | light_toggle (602), temperature (232), byte 3 bit 7 (183), byte 9 bit 4 (129), mode (1) |
| 2400 | Yamatsu | unknown |  |  | 0/257 | 0 |  |
| 2420 | VS | near | ElectraAcDevice | C | 0/340 | 1 | swing_h (323), light_toggle (323), byte 3 bit 4 (248), byte 3 bit 3 (196), byte 3 bit 0 (143), temperature (136), byte 3 bit 1 (93), byte 3 bit 2 (90), byte 2 bit 2 (44), byte 2 bit 4 (44), byte 2 bit 1 (34), byte 2 bit 0 (34), fan (17), byte 3 bit 5 (11) |
| 2440 | Vaillant | unknown |  |  | 0/196 | 0 |  |
| 2460 | FanWorld | near | ElectraAcDevice | C | 0/273 | 0 | light_toggle (263), temperature (70), byte 9 bit 4 (63), fan (17), power (3), mode (1) |
| 2480 | Rotenso | near | CoolixDevice | C | 197/281 | 0 | fan (84) |
| 2500 | Endesa | near | KelonDevice | C | 3/361 | 0 | power_toggle (357), fan (105), dry_grade (84) |
| 2520 | Galanz | unknown |  |  | 0/257 | 0 |  |
| 2540 | Audinac | near | MirageDevice/KKG9AC1 | C | 0/301 | 0 | seconds (241), mode (241), minutes (241), frames (60), swing_power (1), hours (1) |
| 2560 | Mistral | near | Trotec3550Device | C | 59/271 | 0 | temp_f (181), temperature (154), fan (60), mode (1) |
| 2580 | KOREL | unknown |  |  | 0/793 | 33 |  |
| 2600 | Equation | unknown |  |  | 0/301 | 0 |  |
| 2620 | Komeco | near | CoolixDevice | C | 196/281 | 0 | fan (84) |
| 2640 | Fisher | unknown |  |  | 0/169 | 0 |  |
| 2641 | Fisher | near | CoolixDevice | C | 171/281 | 0 | fan (84) |
| 2660 | Hyundai | unknown |  |  | 0/269 | 0 |  |
| 2661 | Hyundai | unknown |  |  | 0/482 | 0 |  |
| 2662 | Hyndai | unknown |  |  | 0/341 | 0 |  |
| 2700 | Kolin | unknown |  |  | 0/64 | 0 |  |
| 2720 | AEG | unknown |  |  | 0/273 | 1 |  |
| 2740 | Bosch | unknown |  |  | 0/376 | 0 |  |
| 2760 | Tristar | near | GoodweatherDevice | C | 5/137 | 0 | command (106), temperature (55), byte 8 bit 4 (5), mode (1), air_flow (1) |
| 2780 | Xiaomi | unknown |  |  | 0/993 | 0 |  |
| 2800 | ELGIN | near | ElectraAcDevice | C | 0/35 | 0 | light_toggle (35), mode (18) |
| 2801 | ELGIN | unknown |  |  | 0/29 | 0 |  |
| 2820 | Pearl | unknown |  |  | 0/181 | 0 |  |
| 2840 | HTW | unknown |  |  | 0/281 | 0 |  |
| 2860 | Senville | near | CoolixDevice | C | 0/211 | 0 | byte 6 bit 6 (205), fan (205), byte 4 bit 0 (205), byte 0 bit 4 (205), zone_follow1 (205), zone_follow2 (205), byte 0 bit 0 (205), byte 6 bit 2 (205), mode (205), temp (205), byte 0 bit 1 (205), byte 6 bit 5 (205), sensor_temp (205), byte 6 bit 7 (205) |
| 2880 | Bora | unknown |  |  | 0/312 | 0 |  |
| 2900 | Goodman | near | MideaDevice | C | 82/169 | 0 | temperature (56), unknown (40), mode (1) |
| 2920 | Best | near | Tcl112AcDevice/GZ055BE1 | C | 0/241 | 0 | quiet (154), msg_type (154), temperature (154), timer_indicator (154), mode (154), power (153), frames (87) |
| 2940 | SAGA | near | GoodweatherDevice | C | 0/545 | 0 | command (543), air_flow (271), byte 8 bit 4 (32), temperature (32), swing_v (14), mode (1) |
| 2960 | EcoAir | near | MideaDevice | C | 0/281 | 0 | temperature (278), fahrenheit (278), fan (98), unknown (41), mode (1) |
| 2980 | Agratto | unknown |  |  | 0/94 | 0 |  |
| 3000 | Philco | near | MirageDevice/KKG29AC1 | C | 0/273 | 0 | pad5 (248), mode (130) |
| 3020 | Klasse | near | Mitsubishi112Device | C | 0/241 | 0 | byte 5 bit 5 (238), byte 3 bit 0 (238), swing_h (238), swing_v (238), byte 3 bit 4 (238), mode (238), byte 3 bit 1 (238), power (237), temperature (222) |
| 3040 | Viessmann | near | GreeDevice/YAW1F | C | 0/241 | 0 | byte 5 bit 5 (230), wifi (230), byte 5 bit 7 (230), mode (1) |
| 3060 | HappyTree | near | Tcl112AcDevice/GZ055BE1 | C | 0/241 | 0 | quiet (236), byte 8 bit 7 (236), msg_type (236), timer_indicator (236), mode (236), power (235), byte 7 bit 4 (234), byte 7 bit 7 (234), temperature (220), byte 6 bit 6 (174), byte 6 bit 7 (95), turbo (32) |
| 3080 | Voltas | near | VoltasDevice/122LZF | C | 0/722 | 0 | wifi (638), temperature (424), fan (223), swing_v (144), swing_h_change (134), byte 6 bit 6 (43), on_timer_mins (43), power (43), on_timer_hrs (43), off_timer_mins (43), byte 6 bit 3 (43), mode (43), byte 5 bit 6 (43), byte 2 bit 4 (43), byte 6 bit 2 (43), byte 3 bit 5 (43), off_timer_hrs (43), byte 4 bit 6 (43), byte 6 bit 0 (43), swing_h (39), byte 8 bit 0 (18), byte 1 bit 4 (13), byte 3 bit 4 (6), frames (2) |
| 3100 | Cecotec | near | Tcl112AcDevice/GZ055BE1 | C | 0/321 | 0 | quiet (312), byte 8 bit 7 (312), msg_type (312), timer_indicator (312), mode (312), power (311), temperature (292), byte 6 bit 6 (234), byte 6 bit 7 (137), turbo (48) |
| 3120 | Cooper & Hunter | near | GreeDevice/YAW1F | C | 0/601 | 0 | byte 5 bit 5 (546), wifi (544), byte 5 bit 7 (544), temp (5), mode (3), model_a (2), byte 3 bit 6 (2), fan (2), power (2), swing_v (2), swing_auto (2), byte 3 bit 4 (2), byte 3 bit 5 (2), light (2), byte 3 bit 7 (2) |
| 3140 | Argo | unknown |  |  | 0/181 | 0 |  |
| 3160 | AquaThermal | near | AirtonDevice | C | 0/321 | 0 | byte 4 bit 4 (318), fan (64), turbo (48), mode (1), temperature (1) |
| 3180 | Devanti | unknown |  |  | 0/257 | 0 |  |
| 3200 | Friedrich | near | Lg2Device/AKB74955603 | F | 136/325 | 0 | power (108), frames (81), temperature (36) |
| 3220 | Mundoclima | near | ElectraAcDevice | C | 0/341 | 0 | light_toggle (324), swing_h (187), temperature (122), swing_v (69), byte 9 bit 4 (68), fan (17), mode (1) |
| 3240 | Casper | unknown |  |  | 0/749 | 0 |  |
| 3300 | PARKAIR | near | ElectraAcDevice | C | 0/121 | 0 | swing_h (120), light_toggle (120), temperature (60), fan (15), mode (1) |
| 3320 | Chunlan | unknown |  |  | 0/256 | 0 |  |
| 3340 | Wide | near | MirageDevice/KKG29AC1 | C | 0/273 | 0 | pad5 (247), recycle_heat (66), swing_v (64), fan (48), temperature (48), frames (16) |
| 3360 | Kaden | near | CoolixDevice | C | 163/281 | 0 | fan (110) |
| 3380 | Zephir | near | ElectraAcDevice | C | 0/141 | 0 | light_toggle (136), byte 9 bit 4 (66), temperature (19), turbo (16), mode (1) |
| 4060 | LG | unsupported |  |  | 0/0 | 157 (!) |  |
| 4100 | Daikin | unsupported |  |  | 0/0 | 157 (!) |  |
| 4124 | Mitsubishi Electric | unsupported |  |  | 0/0 | 170 (!) |  |
| 4129 | Mitsubishi Electric | unsupported |  |  | 0/0 | 170 (!) |  |
| 4180 | Gree | unsupported |  |  | 0/0 | 301 (!) |  |
| 4181 | Gree | unsupported |  |  | 0/0 | 301 (!) |  |
| 4285 | Fujitsu | unsupported |  |  | 0/0 | 376 (!) |  |
| 4380 | Midea | unsupported |  |  | 0/0 | 281 (!) |  |
| 4381 | Midea | unsupported |  |  | 0/0 | 58 (!) |  |
| 4580 | Chigo | unsupported |  |  | 0/0 | 118 (!) |  |
| 4581 | Chigo | unsupported |  |  | 0/0 | 157 (!) |  |
| 4800 | TechnoLux | unsupported |  |  | 0/0 | 241 (!) |  |
| 5120 | Daikin | near | PanasonicAcDevice/JKE | C | 0/703 | 0 | byte 2 bit 7 (679), byte 3 bit 6 (679), byte 2 bit 0 (679), byte 2 bit 2 (679), byte 8 bit 0 (679), byte 0 bit 0 (679), byte 1 bit 7 (679), byte 3 bit 7 (679), byte 3 bit 2 (679), byte 9 bit 4 (679), byte 1 bit 6 (679), byte 9 bit 6 (679), byte 1 bit 1 (679), byte 10 bit 6 (679), byte 15 bit 7 (679), byte 9 bit 5 (679), byte 7 bit 2 (679), byte 11 bit 2 (679), byte 8 bit 1 (679), byte 3 bit 5 (679), byte 9 bit 1 (679), byte 0 bit 1 (679), on_timer (679), byte 10 bit 2 (679), off_timer (679), byte 20 bit 7 (679), byte 9 bit 3 (679), byte 9 bit 7 (679), byte 1 bit 4 (679), byte 2 bit 6 (679), model_23 (679), byte 10 bit 7 (679), byte 10 bit 1 (679), byte 2 bit 1 (679), byte 8 bit 4 (679), byte 0 bit 4 (679), byte 1 bit 3 (679), byte 3 bit 4 (679), byte 19 bit 3 (679), byte 1 bit 5 (679), byte 10 bit 0 (679), swing_v (343), temperature (121), fan (99), byte 14 bit 0 (30), byte 14 bit 6 (14), mode (2), byte 14 bit 7 (1) |
| 5140 | Mitsubishi Electric | near | Mitsubishi112Device | C | 0/1345 | 0 | swing_h (1308), temperature (428), swing_v (184), fan (1), mode (1) |
| 5520 | Hisense | near | KelonDevice | C | 0/241 | 0 | power_toggle (223), temperature (96), fan (60), dry_grade (56) |
| 7062 | LG | near | LgAcDevice/GE6711AR2853M | C | 53/105 | 0 | temp (48) |
| 7065 | LG | near | LgNativeDevice/generic | C | 1/181 | 0 | fan (175), change (174), temp (101), mode (43) |
| 7124 | Mitsubishi | unknown |  |  | 0/481 | 0 |  |
| 7260 | Toshiba | unknown |  |  | 0/449 | 112 (!) |  |
| 7285 | Fujitsu | unknown |  |  | 0/376 | 0 |  |
| 7300 | SHARP | near | SharpAcDevice/A903 | C | 0/179 | 1 | byte 11 bit 1 (179), temp_flags (59), temperature (56), fan (45), mode (1) |
| 7386 | Midea | near | Bosch144Device | C | 43/351 | 0 | fan_s1 (154), checksum (154) |
| 7740 | Kelvinator | unknown |  |  | 0/351 | 0 |  |
| 7741 | Family | unknown |  |  | 0/401 | 0 |  |
| 8700 | Kolin | unknown |  |  | 0/256 | 0 |  |
| 8720 | Viomi | unknown |  |  | 0/161 | 0 |  |
| 8800 | Sigma | unknown |  |  | 0/242 | 0 |  |

## Clusters of unknown files

### 6 files, 2499 codes, 1132 keys

files: 1101, 1104, 1106, 1108, 1114, 1118

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(426, 457, 1310), header=(396, 426), footer=(426,), gap=25337),
        "s1": Section(PulseDistance(426, 457, 1310), header=(3441, 1736), footer=(426,), gap=34808),
        "s2": Section(PulseDistance(426, 457, 1310), header=(3441, 1736), footer=(426,), gap=34808),
        "s3": Section(PulseDistance(426, 457, 1310), header=(3441, 1736), footer=(426,), gap=101502),
    },
)
```

### 6 files, 1828 codes, 858 keys

files: 1162, 1260, 1261, 1263, 1264, 2160

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 548, 579), header=(4355, 4385), footer=(518,), gap=7461),
        "s1": Section(PulseDistance(518, 548, 579), header=(4355, 4385), footer=(518,), gap=101502),
    },
)
```

### 6 files, 930 codes, 561 keys

files: 1388, 1660, 2100, 2320, 2801, 2840

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(548, 518, 1614), header=(4385, 4416), footer=(518,), gap=5208),
        "s1": Section(PulseDistance(548, 518, 1614), header=(4385, 4416), footer=(518,), gap=101502),
    },
)
```

### 5 files, 1619 codes, 991 keys

files: 1661, 2661, 2980, 3180, 7741

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(487, 305, 365), header=(3045, 1614), footer=(487,), gap=70134),
        "s1": Section(PulseDistance(487, 305, 365), header=(3045, 1614), footer=(487,), gap=101502),
    },
)
```

### 4 files, 2660 codes, 2529 keys

files: 1103, 1121, 1136, 1137

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 396, 457), header=(3441, 1705), footer=(457,), gap=12973),
        "s1": Section(PulseDistance(457, 396, 457), header=(3441, 1705), footer=(457,), gap=101502),
    },
)
```

### 4 files, 1835 codes, 1442 keys

files: 1183, 1184, 2162, 8800

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(640, 579, 1675), header=(8892, 4507), footer=(640,), gap=19947),
        "s1": Section(PulseDistance(640, 579, 1675), header=(640, 579), footer=(640,), gap=101502),
    },
)
```

### 4 files, 1586 codes, 1057 keys

files: 1043, 1284, 1285, 1294

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 365, 426), header=(3198, 1584), footer=(457,), gap=101502),
    },
)
```

### 3 files, 575 codes, 300 keys

files: 1680, 1688, 1692

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(396, 365, 1188), header=(3167, 1553), footer=(396,), gap=101502),
    },
)
```

### 2 files, 1350 codes, 1349 keys

files: 1400, 1408

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(548,), gap=17846),
        "s1": Section(None, header=(3015,), gap=8892),
        "s2": Section(PulseDistance(518, 487, 1462), header=(518, 487), footer=(3015,), gap=8892),
        "s3": Section(PulseDistance(518, 487, 1462), header=(518, 1462), footer=(518,), gap=101502),
    },
)
```

### 2 files, 1154 codes, 1153 keys

files: 1900, 2041

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(548, 274, 1035), header=(3076, 1553), footer=(548,), gap=69830),
        "s1": Section(PulseDistance(548, 274, 1035), header=(3076, 1553), footer=(548,), gap=101502),
    },
)
```

### 2 files, 996 codes, 810 keys

files: 1942, 2580

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 640, 1736), header=(8984, 4568), footer=(548,), gap=101502),
    },
)
```

### 2 files, 642 codes, 641 keys

files: 1188, 1342

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(609, 579, 1644), header=(8740, 4385), footer=(609,), gap=19521),
        "s1": Section(PulseDistance(609, 579, 1644), header=(609, 579), footer=(609,), gap=101502),
    },
)
```

### 2 files, 633 codes, 632 keys

files: 1602, 2880

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(548, 518, 1249), header=(3441, 1614), footer=(518,), gap=101502),
    },
)
```

### 2 files, 632 codes, 451 keys

files: 1343, 1741

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(609, 609, 1705), header=(8862, 4507), footer=(609,), gap=20008),
        "s1": Section(PulseDistance(609, 609, 1705), header=(609, 609), footer=(609,), gap=39955),
        "s2": Section(PulseDistance(609, 609, 1705), header=(8862, 4507), footer=(609,), gap=20008),
        "s3": Section(PulseDistance(609, 609, 1705), header=(609, 609), footer=(609,), gap=101502),
    },
)
```

### 2 files, 614 codes, 341 keys

files: 2662, 2720

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 548, 1675), header=(8771, 4416), footer=(518,), gap=101502),
    },
)
```

### 2 files, 573 codes, 437 keys

files: 2120, 3140

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(487, 792, 2071), header=(6426, 3137), footer=(487,), gap=101502),
    },
)
```

### 2 files, 557 codes, 361 keys

files: 1180, 8700

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(615, 609, 1625), header=(9014, 4455), footer=(615,), gap=19978),
        "s1": Section(PulseDistance(615, 609, 1625), header=(615, 614), footer=(615,), gap=19978),
    },
)
```

### 2 files, 542 codes, 361 keys

files: 1182, 2340

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(640, 548, 579), header=(8953, 4477), footer=(640,), gap=101502),
    },
)
```

### 2 files, 497 codes, 301 keys

files: 1763, 2440

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(640, 579, 1675), header=(8984, 4507), footer=(640,), gap=20038),
        "s1": Section(PulseDistance(640, 579, 1675), header=(640, 609), footer=(640,), gap=101502),
    },
)
```

### 2 files, 437 codes, 257 keys

files: 1120, 1125

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(426, 396, 457), header=(3350, 1675), footer=(396,), gap=11359),
        "s1": Section(PulseDistance(426, 396, 457), header=(3350, 1675), footer=(396,), gap=101502),
    },
)
```

### 2 files, 386 codes, 257 keys

files: 1420, 1860

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 426, 548), header=(3594, 1644), footer=(457,), gap=101502),
    },
)
```

### 2 files, 188 codes, 127 keys

files: 2280, 2281

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 609, 1675), header=(8771, 4416), footer=(579,), gap=101502),
    },
)
```

### 1 files, 1036 codes, 1036 keys

files: 1105

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(426, 426, 1310), header=(426, 426), footer=(426,), gap=25002),
        "s1": Section(PulseDistance(426, 426, 1310), header=(3502, 1705), footer=(426,), gap=101502),
    },
)
```

### 1 files, 993 codes, 993 keys

files: 2780

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(548, 426, 2254), header=(944, 609), footer=(548,), gap=101502),
    },
)
```

### 1 files, 841 codes, 841 keys

files: 1404

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(426,), gap=17907),
        "s1": Section(None, header=(2984,), gap=8984),
        "s2": Section(PulseDistance(487, 487, 1492), header=(518, 487), footer=(2984,), gap=8984),
        "s3": Section(PulseDistance(487, 487, 1492), header=(518, 1462), footer=(518,), gap=101502),
    },
)
```

### 1 files, 749 codes, 749 keys

files: 3240

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 579, 1705), header=(8862, 4507), footer=(518,), gap=101502),
    },
)
```

### 1 files, 598 codes, 598 keys

files: 1113

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(579, 609, 1675), header=(8679, 4446), footer=(579,), gap=19551),
        "s1": Section(PulseDistance(579, 609, 1675), header=(579, 609), footer=(579,), gap=101502),
    },
)
```

### 1 files, 553 codes, 553 keys

files: 1117

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(396, 457, 1340), header=(305, 487), footer=(396,), gap=25429),
        "s1": Section(PulseDistance(396, 457, 1340), header=(3411, 1797), footer=(426,), gap=101502),
    },
)
```

### 1 files, 501 codes, 501 keys

files: 2242

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 609, 1675), header=(8953, 4477), footer=(487,), gap=101502),
    },
)
```

### 1 files, 481 codes, 481 keys

files: 1124

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(365, 426, 457), header=(3259, 1736), footer=(335,), gap=11359),
        "s1": Section(PulseDistance(365, 426, 457), header=(3259, 1736), footer=(335,), gap=101502),
    },
)
```

### 1 files, 481 codes, 481 keys

files: 7124

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(450, 390, 1250), header=(3500, 1700), footer=(450,), gap=9000),
        "s1": Section(PulseDistance(450, 390, 1250), header=(3500, 1700), footer=(450,), gap=0),
    },
)
```

### 1 files, 449 codes, 449 keys

files: 7260

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(598, 489, 1574), header=(4477, 4309), footer=(598,), gap=7427),
        "s1": Section(PulseDistance(598, 489, 1574), header=(4477, 4309), footer=(598,), gap=0),
    },
)
```

### 1 files, 426 codes, 426 keys

files: 1087

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(29844,), gap=50187),
        "s1": Section(PulseDistance(365, 457, 1310), header=(3319, 1736), footer=(365,), gap=101502),
    },
)
```

### 1 files, 426 codes, 426 keys

files: 1088

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(365, 487, 29205), gap=48908),
        "s1": Section(PulseDistance(335, 579, 1310), header=(3198, 1736), footer=(426,), gap=30149),
        "s2": Section(PulseDistance(335, 579, 1310), header=(365, 487), footer=(426,), gap=101502),
    },
)
```

### 1 files, 417 codes, 417 keys

files: 1403

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(579,), gap=17937),
        "s1": Section(None, header=(2954,), gap=8984),
        "s2": Section(PulseDistance(487, 518, 1523), header=(487, 518), footer=(2954,), gap=8984),
        "s3": Section(PulseDistance(487, 518, 1523), header=(487, 1523), footer=(487,), gap=101502),
    },
)
```

### 1 files, 376 codes, 376 keys

files: 1290

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(487, 305, 365), header=(3289, 1614), footer=(426,), gap=101502),
    },
)
```

### 1 files, 376 codes, 376 keys

files: 2740

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(548, 518, 1584), header=(4416, 4385), footer=(548,), gap=5177),
        "s1": Section(PulseDistance(548, 518, 1584), header=(4416, 4385), footer=(548,), gap=5177),
        "s2": Section(PulseDistance(548, 518, 1584), header=(4416, 4385), footer=(548,), gap=101502),
    },
)
```

### 1 files, 376 codes, 376 keys

files: 7285

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(418, 450, 482), header=(3376, 1704), footer=(418,), gap=0),
    },
)
```

### 1 files, 367 codes, 363 keys

files: 1407

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(457,), gap=17511),
        "s1": Section(None, header=(2863,), gap=8771),
        "s2": Section(PulseDistance(457, 518, 1492), header=(457, 518), footer=(2863,), gap=8771),
        "s3": Section(PulseDistance(457, 518, 1492), header=(457, 1492), footer=(457,), gap=101502),
    },
)
```

### 1 files, 362 codes, 362 keys

files: 1702

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(670, 518, 579), header=(4355, 4446), footer=(670,), gap=40077),
        "s1": Section(PulseDistance(670, 518, 579), header=(9014, 4446), footer=(670,), gap=20038),
        "s2": Section(PulseDistance(670, 518, 579), header=(670, 518), footer=(670,), gap=101502),
    },
)
```

### 1 files, 361 codes, 361 keys

files: 1112

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(396, 457, 1310), header=(290, 457), footer=(396,), gap=25398),
        "s1": Section(PulseDistance(396, 457, 1310), header=(3441, 1766), footer=(426,), gap=101502),
    },
)
```

### 1 files, 358 codes, 358 keys

files: 1084

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(29997,), gap=50096),
        "s1": Section(PulseDistance(426, 396, 1249), header=(3380, 1675), footer=(426,), gap=101502),
    },
)
```

### 1 files, 358 codes, 358 keys

files: 1089

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(487, 396, 30119), gap=50157),
        "s1": Section(PulseDistance(426, 487, 1279), header=(3380, 1675), footer=(487,), gap=101502),
    },
)
```

### 1 files, 354 codes, 354 keys

files: 1262

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(609, 457, 1523), header=(4416, 4294), footer=(579,), gap=5086),
        "s1": Section(PulseDistance(609, 457, 1523), header=(4416, 4294), footer=(579,), gap=101502),
    },
)
```

### 1 files, 351 codes, 351 keys

files: 7740

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(470, 608, 1682), header=(4360, 4470), footer=(469,), gap=5285),
        "s1": Section(PulseDistance(470, 608, 1682), header=(4360, 4470), footer=(469,), gap=0),
    },
)
```

### 1 files, 341 codes, 341 keys

files: 1082

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(365, 518, 1279), header=(3289, 1705), footer=(365,), gap=101502),
    },
)
```

### 1 files, 326 codes, 326 keys

files: 1686

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 335, 1157), header=(3106, 1523), footer=(457,), gap=101502),
    },
)
```

### 1 files, 326 codes, 326 keys

files: 1690

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(5938,), gap=7522),
        "s1": Section(PulseDistance(457, 1523, 3533), header=(487, 3533), footer=(487,), gap=7522),
        "s2": Section(None, header=(487,), gap=101502),
    },
)
```

### 1 files, 321 codes, 321 keys

files: 1720

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 335, 365), header=(3106, 1675), footer=(518,), gap=101502),
    },
)
```

### 1 files, 321 codes, 321 keys

files: 1761

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(548, 274, 1035), header=(3137, 1553), footer=(518,), gap=69982),
        "s1": Section(PulseDistance(548, 274, 1035), header=(3137, 1553), footer=(518,), gap=101502),
    },
)
```

### 1 files, 321 codes, 321 keys

files: 2260

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(396, 548, 1431), header=(3715, 1827), footer=(396,), gap=101502),
    },
)
```

### 1 files, 316 codes, 316 keys

files: 1265

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(579, 487, 1614), header=(4355, 4507), footer=(579,), gap=5421),
        "s1": Section(PulseDistance(579, 487, 1614), header=(4355, 4507), footer=(579,), gap=101502),
    },
)
```

### 1 files, 313 codes, 313 keys

files: 1107

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(365, 700, 1766), header=(4994, 2132), footer=(305,), gap=29449),
        "s1": Section(PulseDistance(365, 700, 1766), header=(4994, 2132), footer=(426,), gap=101502),
    },
)
```

### 1 files, 301 codes, 301 keys

files: 1041

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(609, 548, 1644), header=(8862, 4446), footer=(640,), gap=101502),
    },
)
```

### 1 files, 301 codes, 301 keys

files: 1345

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(731, 731, 1675), header=(7857, 4203), footer=(1858,), gap=20404),
        "s1": Section(PulseDistance(731, 731, 1675), header=(7857, 4203), footer=(1858,), gap=101502),
    },
)
```

### 1 files, 301 codes, 301 keys

files: 1601

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(579, 609, 1705), header=(8740, 4507), footer=(579,), gap=19917),
        "s1": Section(PulseDistance(579, 609, 1705), header=(609, 1705), footer=(579,), gap=101502),
    },
)
```

### 1 files, 301 codes, 301 keys

files: 1640

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(609, 548, 1584), header=(3045, 3045), footer=(548,), gap=19978),
    },
)
```

### 1 files, 301 codes, 301 keys

files: 2600

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 365, 1188), header=(3350, 1644), footer=(457,), gap=101502),
    },
)
```

### 1 files, 281 codes, 281 keys

files: 1385

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(761, 396, 1431), header=(4446, 4263), footer=(761,), gap=101502),
    },
)
```

### 1 files, 269 codes, 269 keys

files: 2660

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(3259,), gap=9075),
        "s1": Section(PulseDistance(731, 487, 1431), header=(624, 1523), footer=(624,), gap=101502),
    },
)
```

### 1 files, 265 codes, 265 keys

files: 1122

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(396, 365, 426), header=(3380, 1644), footer=(426,), gap=9136),
        "s1": Section(PulseDistance(396, 365, 426), header=(3380, 1644), footer=(426,), gap=101502),
    },
)
```

### 1 files, 261 codes, 261 keys

files: 1520

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(39194,), gap=99004),
        "s1": Section(PulseDistance(396, 365, 1249), header=(3198, 1705), footer=(426,), gap=19978),
    },
)
```

### 1 files, 257 codes, 257 keys

files: 1126

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(396, 487, 1310), header=(3228, 1736), footer=(396,), gap=101502),
    },
)
```

### 1 files, 257 codes, 257 keys

files: 2400

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 487, 518), header=(3685, 1462), footer=(548,), gap=101502),
    },
)
```

### 1 files, 257 codes, 257 keys

files: 2520

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 487, 1157), header=(3685, 1523), footer=(548,), gap=101502),
    },
)
```

### 1 files, 256 codes, 256 keys

files: 3320

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 670, 1736), header=(8771, 4416), footer=(457,), gap=101502),
    },
)
```

### 1 files, 241 codes, 241 keys

files: 1001

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 579, 1705), header=(8862, 4629), footer=(335,), gap=101502),
    },
)
```

### 1 files, 241 codes, 241 keys

files: 1948

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 670, 731), header=(8740, 4416), footer=(457,), gap=101502),
    },
)
```

### 1 files, 240 codes, 240 keys

files: 1401

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(579,), gap=17846),
        "s1": Section(None, header=(2954,), gap=8984),
        "s2": Section(PulseDistance(457, 487, 1523), header=(487, 548), footer=(2954,), gap=8984),
        "s3": Section(PulseDistance(457, 487, 1523), header=(487, 1492), footer=(2954,), gap=8984),
        "s4": Section(PulseDistance(457, 487, 1523), header=(487, 1492), footer=(487,), gap=101502),
    },
)
```

### 1 files, 210 codes, 210 keys

files: 1291

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 365, 1188), header=(3350, 1584), footer=(457,), gap=101502),
    },
)
```

### 1 files, 205 codes, 205 keys

files: 1092

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(29905,), gap=49944),
        "s1": Section(PulseDistance(396, 396, 1249), header=(3259, 1675), footer=(396,), gap=101502),
    },
)
```

### 1 files, 205 codes, 205 keys

files: 1116

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(396, 670, 700), header=(5055, 2132), footer=(396,), gap=29327),
        "s1": Section(PulseDistance(396, 670, 700), header=(5055, 2132), footer=(396,), gap=101502),
    },
)
```

### 1 files, 205 codes, 205 keys

files: 2321

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 640, 1766), header=(8953, 4598), footer=(548,), gap=101502),
    },
)
```

### 1 files, 181 codes, 181 keys

files: 1027

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(822, 914, 2649), header=(3441, 3533), footer=(853,), gap=13948),
        "s1": Section(PulseDistance(822, 914, 2649), header=(3441, 3533), footer=(853,), gap=101502),
    },
)
```

### 1 files, 181 codes, 181 keys

files: 1161

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(274, 487, 1035), header=(4507, 2649), footer=(244,), gap=20708),
        "s1": Section(None, header=(4507,), gap=6791),
        "s2": Section(None, header=(9227,), gap=5055),
        "s3": Section(PulseDistance(274, 487, 1035), header=(305, 457), footer=(244,), gap=20708),
        "s4": Section(None, header=(4507,), gap=101502),
    },
)
```

### 1 files, 181 codes, 181 keys

files: 1946

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(914, 914, 975), header=(2832, 2893), footer=(3776,), gap=67028),
        "s1": Section(PulseDistance(914, 914, 975), header=(2832, 2893), footer=(3776,), gap=101502),
    },
)
```

### 1 files, 181 codes, 181 keys

files: 2820

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(305, 457, 975), header=(4538, 2619), footer=(305,), gap=20480),
        "s1": Section(None, header=(4538,), gap=6639),
        "s2": Section(PulseDistance(305, 457, 975), header=(9197, 4933), footer=(305,), gap=20480),
        "s3": Section(None, header=(4538,), gap=101502),
    },
)
```

### 1 files, 169 codes, 169 keys

files: 2640

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(548, 487, 1492), header=(548, 3441), footer=(548,), gap=101502),
    },
)
```

### 1 files, 161 codes, 161 keys

files: 1127

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(487, 335, 1188), header=(3502, 1644), footer=(487,), gap=12912),
        "s1": Section(PulseDistance(487, 335, 1188), header=(3502, 1644), footer=(487,), gap=101502),
    },
)
```

### 1 files, 161 codes, 161 keys

files: 8720

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(458, 439, 536), header=(865, 754), footer=(517,), gap=0),
    },
)
```

### 1 files, 157 codes, 157 keys

files: 1500

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(426, 396, 426), header=(3350, 1644), footer=(426,), gap=101502),
    },
)
```

### 1 files, 157 codes, 157 keys

files: 1687

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(365, 396, 1218), header=(3015, 1614), footer=(396,), gap=101502),
    },
)
```

### 1 files, 144 codes, 144 keys

files: 1086

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(426, 518, 1249), header=(3319, 1675), footer=(365,), gap=101502),
    },
)
```

### 1 files, 141 codes, 141 keys

files: 1386

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 640, 1736), header=(4263, 4507), footer=(457,), gap=5299),
        "s1": Section(PulseDistance(457, 640, 1736), header=(4263, 4507), footer=(457,), gap=101502),
    },
)
```

### 1 files, 137 codes, 137 keys

files: 1346

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(700, 761, 1675), header=(7948, 4203), footer=(1827,), gap=20404),
        "s1": Section(PulseDistance(700, 761, 1675), header=(7948, 4203), footer=(1827,), gap=101502),
    },
)
```

### 1 files, 127 codes, 127 keys

files: 1947

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 792, 1553), header=(5299, 1979), footer=(457,), gap=101502),
    },
)
```

### 1 files, 122 codes, 122 keys

files: 2180

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(426, 518, 1340), header=(3167, 1858), footer=(426,), gap=101502),
    },
)
```

### 1 files, 121 codes, 121 keys

files: 1684

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 335, 396), header=(3533, 1675), footer=(457,), gap=9958),
        "s1": Section(PulseDistance(457, 335, 396), header=(3533, 1675), footer=(457,), gap=101502),
    },
)
```

### 1 files, 118 codes, 118 keys

files: 1240

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(548, 579, 609), header=(9014, 4538), footer=(548,), gap=13521),
        "s1": Section(PulseDistance(548, 579, 609), header=(9014, 4538), footer=(548,), gap=13521),
        "s2": Section(PulseDistance(548, 579, 609), header=(9014, 4538), footer=(548,), gap=101502),
    },
)
```

### 1 files, 91 codes, 91 keys

files: 1123

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 335, 1157), header=(3076, 1523), footer=(457,), gap=101502),
    },
)
```

### 1 files, 91 codes, 91 keys

files: 1341

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 487, 1553), header=(7857, 4172), footer=(1614,), gap=30423),
        "s1": Section(PulseDistance(518, 487, 1553), header=(7857, 4172), footer=(1614,), gap=101502),
    },
)
```

### 1 files, 91 codes, 91 keys

files: 2140

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(396, 365, 426), header=(4751, 2589), footer=(305,), gap=20982),
        "s1": Section(None, header=(4751,), gap=6517),
        "s2": Section(None, header=(9410,), gap=5208),
        "s3": Section(PulseDistance(396, 365, 426), header=(396, 335), footer=(396,), gap=20982),
        "s4": Section(None, header=(4751,), gap=101502),
    },
)
```

### 1 files, 79 codes, 79 keys

files: 1181

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(609, 609, 1705), header=(8923, 4507), footer=(609,), gap=19978),
        "s1": Section(PulseDistance(609, 609, 1705), header=(609, 609), footer=(609,), gap=39955),
        "s2": Section(PulseDistance(609, 609, 1705), header=(8923, 4507), footer=(609,), gap=19978),
        "s3": Section(PulseDistance(609, 609, 1705), header=(609, 609), footer=(609,), gap=101502),
    },
)
```

### 1 files, 64 codes, 64 keys

files: 2700

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(9014,), gap=5360),
        "s1": Section(PulseDistance(609, 579, 1553), header=(640, 1553), footer=(640,), gap=101502),
    },
)
```

### 1 files, 61 codes, 61 keys

files: 1187

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(640, 548, 1675), header=(8923, 4477), footer=(640,), gap=19947),
        "s1": Section(PulseDistance(640, 548, 1675), header=(640, 1644), footer=(640,), gap=101502),
    },
)
```

### 1 files, 60 codes, 60 keys

files: 1186

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(640, 548, 1644), header=(8953, 4477), footer=(640,), gap=19947),
        "s1": Section(PulseDistance(640, 548, 1644), header=(640, 548), footer=(640,), gap=39925),
        "s2": Section(PulseDistance(640, 548, 1644), header=(8953, 4477), footer=(640,), gap=19947),
        "s3": Section(PulseDistance(640, 548, 1644), header=(640, 548), footer=(640,), gap=101502),
    },
)
```

### 1 files, 58 codes, 58 keys

files: 1139

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(426, 396, 426), header=(3259, 1644), footer=(396,), gap=11024),
        "s1": Section(PulseDistance(426, 396, 426), header=(3259, 1644), footer=(396,), gap=101502),
    },
)
```

### 1 files, 56 codes, 56 keys

files: 1945

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(944, 1035, 2071), header=(2863, 2954), footer=(3959,), gap=101502),
    },
)
```

### 1 files, 43 codes, 43 keys

files: 1119

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 426, 1279), header=(3472, 1705), footer=(426,), gap=29631),
        "s1": Section(PulseDistance(457, 426, 1279), header=(3472, 1705), footer=(426,), gap=101502),
    },
)
```

## Conflicts

- SmartIR 1064: LG / Unknown: name taken by TableDevice/1061
- SmartIR 1128: Mitsubishi Electric / MSZ-HJ25VA: name taken by TableDevice/1127
- SmartIR 1265: Toshiba / RAS-25SKVP2-ND: name taken by ToshibaAcDevice/None
- SmartIR 1284: Fujitsu / AR-REG1U: name taken by FujitsuAcDevice/ARRAH2E
- SmartIR 1287: Fujitsu / AR-REB1E: name taken by FujitsuAcDevice/ARREB1E
- SmartIR 1289: Fujitsu / AR-REW1E: name taken by FujitsuAcDevice/ARREW4E
- SmartIR 1293: Fujitsu / AR-REB1E: name taken by FujitsuAcDevice/ARREB1E
- SmartIR 1294: Fujitsu / AR-RY4: name taken by FujitsuAcDevice/ARRY4
- SmartIR 1381: Midea / Unknown: name taken by TableDevice/1380
- SmartIR 1481: Junkers / Excellence: name taken by TableDevice/1480
- SmartIR 1521: Hisense / Unknown: name taken by TableDevice/1520
- SmartIR 1540: Whirlpool / SPIS412L: name taken by WhirlpoolAcDevice/DG11J13A
- SmartIR 1624: Tornado / Super Legend 40: name taken by TableDevice/1621
- SmartIR 1741: Kelvinator / KSV26CRC: name taken by KelvinatorDevice/None
- SmartIR 1741: Kelvinator / KSV26HRC: name taken by KelvinatorDevice/None
- SmartIR 1741: Kelvinator / KSV35CRC: name taken by KelvinatorDevice/None
- SmartIR 1741: Kelvinator / KSV35HRC: name taken by KelvinatorDevice/None
- SmartIR 1741: Kelvinator / KSV53HRC: name taken by KelvinatorDevice/None
- SmartIR 1741: Kelvinator / KSV62HRC: name taken by KelvinatorDevice/None
- SmartIR 1741: Kelvinator / KSV70CRC: name taken by KelvinatorDevice/None
- SmartIR 1741: Kelvinator / KSV80HRC: name taken by KelvinatorDevice/None
- SmartIR 1782: Trotec / RG57H3(B)/BGCEF-M: name taken by MideaDevice/None
- SmartIR 1782: Trotec / PAC 2100 X: name taken by MideaDevice/None
- SmartIR 1941: Electra / Unknown: name taken by TableDevice/1940
- SmartIR 1943: Electra / Unknown: name taken by TableDevice/1940
- SmartIR 1947: Electra / Electra: name taken by TableDevice/1945
- SmartIR 7062: LG / P12RK: name taken by TableDevice/1062
- SmartIR 7065: LG / LG080EC: name taken by TableDevice/1065
- SmartIR 7065: LG / LG100EC: name taken by TableDevice/1065
- SmartIR 7065: LG / LG150EC: name taken by TableDevice/1065
- SmartIR 7065: LG / LG200EC: name taken by TableDevice/1065
- SmartIR 7124: Mitsubishi / MSZ-SF25VE3: name taken by TableDevice/1124
- SmartIR 7124: Mitsubishi / MSZ-SF35VE3: name taken by TableDevice/1124
- SmartIR 7124: Mitsubishi / MSZ-SF42VE3: name taken by TableDevice/1124
- SmartIR 7124: Mitsubishi / MSZ-SF50VE3: name taken by TableDevice/1124
- SmartIR 7124: Mitsubishi / MSZ-AP20VG: name taken by TableDevice/1124
- SmartIR 7124: Mitsubishi / MSZ-AP25VGD: name taken by TableDevice/1124
- SmartIR 7285: Fujitsu / AR-RCE1E: name taken by TableDevice/1285
- SmartIR 7386: Midea / KFR-32GW: name taken by TableDevice/1386

## Rows: 538 proposed (rows.py)

