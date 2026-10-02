# SmartIR climate import

- covered: 62
- near: 129
- unknown: 152
- unsupported: 13
- not JSON: 2680

## Files

Skipped: codes that could not be read; flagged (!) when they are over 10% of the file.

Codes: read from the file, decoded by the candidate, verified (sent by pyhvac for their labelled state), relabelled (sent by pyhvac for another state: the file's label is wrong).

| file | brand | verdict | candidate | units | codes | decoded | verified | relabelled | skipped | gaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 1000 | Toyotomi | near | GreeDevice/YX1FSF | C | 181 | 181 | 118 | 62 | 0 | mode (1) |
| 1001 | Toyotomi | unknown |  |  | 241 | 0 | 0 | 0 | 0 |  |
| 1020 | Panasonic | near | PanasonicAcDevice/JKE | C | 121 | 118 | 0 | 0 | 0 | model_13 (118), mode (1) |
| 1021 | Panasonic | near | PanasonicAcDevice/DKE | C | 121 | 121 | 0 | 0 | 0 | byte 19 bit 3 (121), model_23 (121), swing_h (121), byte 20 bit 7 (121), mode (1) |
| 1022 | Panasonic | near | PanasonicAcDevice/RKR | C | 349 | 322 | 167 | 0 | 0 | byte 14 bit 0 (154), mode (1) |
| 1023 | Panasonic | near | PanasonicAcDevice/RKR | C | 361 | 361 | 0 | 0 | 0 | model_23 (361), temperature (84), power (2) |
| 1024 | Panasonic | near | PanasonicAcDevice/JKE | C | 241 | 239 | 0 | 0 | 0 | model_13 (239), mode (1), fan (1), power (1) |
| 1025 | Panasonic | near | PanasonicAcDevice/DKE | C | 25 | 25 | 0 | 0 | 0 | model_13 (25), model_23 (25), mode (16) |
| 1026 | Panasonic | near | PanasonicAcDevice/JKE | C | 181 | 179 | 0 | 0 | 0 | model_13 (179), fan (74), mode (1) |
| 1027 | Panasonic | unknown |  |  | 181 | 0 | 0 | 0 | 0 |  |
| 1028 | Panasonic | near | PanasonicAcDevice/RKR | C | 271 | 271 | 0 | 0 | 0 | model_23 (271), temperature (84), power (2) |
| 1029 | Panasonic | near | PanasonicAcDevice/DKE | C | 361 | 326 | 324 | 0 | 0 | model_23 (2), clock (2), mode (1) |
| 1030 | Panasonic | near | PanasonicAcDevice/JKE | C | 2160 | 2055 | 0 | 0 | 0 | model_13 (2055), temperature (486), swing_h (1), swing_v (1), fan (1) |
| 1031 | Panasonic | near | MitsubishiHeavy88Device | C | 209 | 207 | 157 | 49 | 0 | mode (1) |
| 1032 | Panasonic | near | PanasonicAcDevice/NKE | C | 301 | 295 | 0 | 0 | 0 | model_23 (295), temperature (70), fan (60), powerful (45), mode (1) |
| 1040 | Ggeneral Electric | near | ElectraAcDevice/aux | C | 205 | 205 | 0 | 0 | 0 | byte 2 bit 1 (187), byte 2 bit 0 (154), byte 3 bit 4 (154), byte 3 bit 3 (154), byte 2 bit 3 (136), byte 3 bit 2 (119), byte 3 bit 0 (94), byte 2 bit 4 (69), heat_flag (68), byte 2 bit 2 (68), byte 3 bit 1 (58), fan (17) |
| 1041 | Ggeneral Electric | unknown |  |  | 301 | 0 | 0 | 0 | 0 |  |
| 1042 | Ggeneral Electric | covered | FujitsuAcDevice/ARRAH2E | C | 336 | 335 | 223 | 112 | 0 |  |
| 1043 | General Electric | unknown |  |  | 336 | 0 | 0 | 0 | 0 |  |
| 1044 | General Electric | near | HaierYrw02Device/A | F | 365 | 357 | 0 | 0 | 0 | use_fahrenheit (357), extra_degree_f (121), temperature (119), quiet (78), mode (1), swing_v (1) |
| 1060 | LG | covered | LgAcDevice/GE6711AR2853M | C | 261 | 261 | 209 | 52 | 0 |  |
| 1061 | LG | near | Lg2Device/AKB74955603 | C | 361 | 337 | 1 | 0 | 0 | unnamed (246), temperature (168), frames (90), fan (85) |
| 1062 | LG | near | LgAcDevice/GE6711AR2853M | C | 261 | 239 | 152 | 48 | 0 | unused (39), temp (36) |
| 1063 | LG | covered | Lg2Device/AKB74955603 | C | 391 | 388 | 244 | 144 | 0 |  |
| 1064 | LG | covered | LgAcDevice/GE6711AR2853M | C | 79 | 79 | 53 | 26 | 0 |  |
| 1065 | LG | near | LgNativeDevice/generic | C | 181 | 176 | 1 | 0 | 0 | fan (175), change (174), temp (101), mode (43) |
| 1066 | LG | covered | Lg2Device/AKB74955603 | C | 391 | 377 | 234 | 143 | 0 |  |
| 1067 | LG | covered | LgAcDevice/GE6711AR2853M | C | 79 | 79 | 79 | 0 | 0 |  |
| 1068 | LG | near | Lg2Device/AKB74955603 | C | 313 | 313 | 85 | 150 | 0 | frames (78) |
| 1069 | LG | covered | Lg2Device/AKB74955603 | C | 209 | 200 | 104 | 96 | 0 |  |
| 1070 | LG | covered | Lg2Device/AKB74955603 | C | 261 | 246 | 162 | 84 | 0 |  |
| 1080 | Hitachi | near | Hitachi264Device | C | 136 | 136 | 135 | 0 | 0 | mode (1), temperature (1) |
| 1081 | Hitachi | near | Hitachi296Device | C | 137 | 133 | 8 | 0 | 0 | byte 11 bit 0 (121), byte 11 bit 1 (121), byte 11 bit 2 (121), byte 9 bit 1 (34), byte 9 bit 3 (34), temperature (9), unset_high (8), byte 11 bit 4 (1), mode (1), byte 11 bit 6 (1) |
| 1082 | Hitachi | unknown |  |  | 341 | 0 | 0 | 0 | 0 |  |
| 1083 | LG | near | Hitachi264Device | C | 205 | 204 | 153 | 50 | 0 | mode (1), temperature (1), byte 13 bit 0 (1) |
| 1084 | Hitachi | unknown |  |  | 358 | 0 | 0 | 0 | 0 |  |
| 1085 | Hitachi | near | Mitsubishi112Device | C | 38 | 35 | 0 | 0 | 0 | byte 11 bit 7 (35), swing_h (35), swing_v (35), temperature (5), mode (1) |
| 1086 | Hitachi | unknown |  |  | 144 | 0 | 0 | 0 | 0 |  |
| 1087 | Hitachi | unknown |  |  | 426 | 0 | 0 | 0 | 0 |  |
| 1088 | Hitachi | unknown |  |  | 426 | 0 | 0 | 0 | 0 |  |
| 1089 | Hitachi | unknown |  |  | 358 | 0 | 0 | 0 | 0 |  |
| 1090 | Hitachi | near | HitachiAcDevice | C | 1701 | 1701 | 0 | 0 | 0 | byte 23 bit 0 (1701), temperature (340), fan (204), min_temp (20) |
| 1091 | Hitachi | near | KelonDevice | C | 452 | 445 | 0 | 355 | 0 | power_toggle (90), temperature (90), smart (90) |
| 1092 | Hitachi | unknown |  |  | 205 | 0 | 0 | 0 | 0 |  |
| 1100 | Daikin | near | PanasonicAcDevice/JKE | C | 261 | 255 | 0 | 0 | 0 | byte 2 bit 0 (255), byte 3 bit 7 (255), byte 1 bit 5 (255), byte 0 bit 4 (255), byte 3 bit 4 (255), on_timer (255), byte 1 bit 3 (255), byte 9 bit 5 (255), byte 2 bit 1 (255), byte 11 bit 2 (255), byte 10 bit 7 (255), byte 19 bit 3 (255), byte 9 bit 6 (255), byte 3 bit 5 (255), byte 10 bit 1 (255), byte 0 bit 0 (255), byte 2 bit 2 (255), byte 10 bit 2 (255), byte 10 bit 6 (255), swing_v (255), byte 20 bit 7 (255), byte 8 bit 4 (255), byte 3 bit 6 (255), model_23 (255), byte 1 bit 1 (255), byte 9 bit 7 (255), byte 3 bit 2 (255), byte 9 bit 1 (255), off_timer (255), byte 9 bit 3 (255), byte 8 bit 1 (255), byte 1 bit 7 (255), byte 9 bit 4 (255), byte 10 bit 0 (255), byte 2 bit 6 (255), byte 2 bit 7 (255), byte 1 bit 6 (255), byte 0 bit 1 (255), byte 15 bit 7 (255), byte 1 bit 4 (255), byte 8 bit 0 (255), byte 7 bit 2 (255), fan (89), temperature (53), byte 14 bit 7 (52), byte 14 bit 6 (52), mode (13) |
| 1101 | Daikin | unknown |  |  | 521 | 0 | 0 | 0 | 0 |  |
| 1102 | Daikin | near | Daikin64Device | C | 271 | 271 | 0 | 0 | 0 | byte 5 bit 4 (271), byte 4 bit 6 (271), byte 5 bit 5 (271), byte 4 bit 1 (271), power (271), byte 3 bit 4 (271), byte 5 bit 2 (271), byte 5 bit 0 (271), byte 2 bit 5 (233), byte 3 bit 2 (181), byte 2 bit 0 (154), byte 2 bit 4 (129), byte 3 bit 0 (121), byte 2 bit 6 (120), fan (120), byte 2 bit 1 (109), byte 3 bit 1 (91), temperature (84), byte 2 bit 3 (30), byte 2 bit 2 (22), byte 3 bit 3 (1) |
| 1103 | Daikin | unknown |  |  | 65 | 0 | 0 | 0 | 0 |  |
| 1104 | Daikin | unknown |  |  | 316 | 0 | 0 | 0 | 0 |  |
| 1105 | Dalkin | unknown |  |  | 1036 | 0 | 0 | 0 | 0 |  |
| 1106 | Daikin | unknown |  |  | 456 | 0 | 0 | 0 | 0 |  |
| 1107 | Daikin | unknown |  |  | 313 | 0 | 0 | 0 | 0 |  |
| 1108 | Daikin | unknown |  |  | 601 | 0 | 0 | 0 | 0 |  |
| 1109 | Daikin | near | Daikin176Device | C | 193 | 186 | 0 | 0 | 0 | alt_mode (186), fan (94), mode (1), temperature (1) |
| 1110 | Daikin | near | Daikin152Device | C | 181 | 178 | 0 | 0 | 0 | byte 18 bit 3 (178), temperature (116), fan (45), mode (15) |
| 1111 | Daikin | near | Daikin160Device | C | 67 | 67 | 66 | 0 | 0 | mode (1) |
| 1112 | Daikin | unknown |  |  | 361 | 0 | 0 | 0 | 0 |  |
| 1113 | Daikin | unknown |  |  | 598 | 0 | 0 | 0 | 0 |  |
| 1114 | Daikin | unknown |  |  | 520 | 0 | 0 | 0 | 0 |  |
| 1115 | Daikin | unknown |  |  | 1801 | 0 | 0 | 0 | 0 |  |
| 1116 | Daikin | unknown |  |  | 205 | 0 | 0 | 0 | 0 |  |
| 1117 | Daikin | unknown |  |  | 553 | 0 | 0 | 0 | 0 |  |
| 1118 | Daikin | unknown |  |  | 85 | 0 | 0 | 0 | 0 |  |
| 1119 | Daikin | unknown |  |  | 43 | 0 | 0 | 0 | 0 |  |
| 1120 | Mitsubishi Electric | unknown |  |  | 180 | 0 | 0 | 0 | 1 |  |
| 1121 | Mitsubishi Electric | unknown |  |  | 65 | 0 | 0 | 0 | 0 |  |
| 1122 | Mitsubishi | unknown |  |  | 265 | 0 | 0 | 0 | 0 |  |
| 1123 | Mitsubishi Electric | unknown |  |  | 91 | 0 | 0 | 0 | 0 |  |
| 1124 | Mitsubishi | unknown |  |  | 481 | 0 | 0 | 0 | 0 |  |
| 1125 | Mitsubishi Electric | unknown |  |  | 257 | 0 | 0 | 0 | 0 |  |
| 1126 | Mitsubishi Electric | unknown |  |  | 257 | 0 | 0 | 0 | 0 |  |
| 1127 | Mitsubishi Electric | unknown |  |  | 161 | 0 | 0 | 0 | 0 |  |
| 1128 | Mitsubishi Electric | near | MitsubishiAcDevice | C | 321 | 302 | 0 | 0 | 0 | clock (302), temperature (145), mode_aux (77), vane_bit (49), fan_auto (41), mode (1) |
| 1129 | Mitsubishi Electric  | near | MitsubishiAcDevice | C | 2689 | 2584 | 0 | 0 | 0 | clock (2584), swing_v (2278), fan_auto (925), temperature (661), mode_aux (642), fan (450), vane_bit (237) |
| 1130 | Mitsubishi Electric | near | MitsubishiAcDevice | C | 193 | 176 | 0 | 0 | 0 | clock (176), swing_v (176), temperature (105), mode_aux (49), vane_bit (32), fan_auto (17), mode (1) |
| 1131 | Mitsubishi Electric | near | Mitsubishi136Device | C | 145 | 132 | 87 | 44 | 0 | mode (1) |
| 1132 | Mitsubishi Electric | near | Mitsubishi112Device | C | 193 | 193 | 0 | 0 | 0 | byte 5 bit 7 (193), swing_h (193), temperature (120), mode (1) |
| 1133 | Mitsubishi Electric Starmex | near | MitsubishiAcDevice | C | 2129 | 2123 | 0 | 0 | 0 | clock (2011), swing_v (1722), temperature (1260), mode_aux (673), fan_auto (322), frames (112), vane_bit (99), fan (16), mode (1) |
| 1134 | Mitsubishi Electric | near | MitsubishiAcDevice | C | 241 | 237 | 0 | 0 | 0 | clock (237), swing_v (237), temperature (150), mode_aux (81), fan_auto (54), vane_bit (10), mode (1) |
| 1135 | Mitsubishi | near | MitsubishiAcDevice | C | 481 | 474 | 0 | 0 | 0 | swing_h (474), clock (474), mode_aux (189), temperature (180), fan_auto (100), swing_v (64), vane_bit (34), mode (1) |
| 1136 | Mitsubishi Electric | unknown |  |  | 289 | 0 | 0 | 0 | 0 |  |
| 1137 | Mitsubishi Electric | unknown |  |  | 2241 | 0 | 0 | 0 | 0 |  |
| 1138 | Mitsubishi Electric | near | MitsubishiAcDevice | C | 321 | 309 | 0 | 0 | 0 | byte 14 bit 4 (309), byte 32 bit 4 (309), clock (309), isee (309), swing_h (309), mode_aux (77), mode (77), temperature (75), fan_auto (63), ecocool (17) |
| 1139 | Mitsubishi | unknown |  |  | 58 | 0 | 0 | 0 | 0 |  |
| 1140 | Actron | covered | CoolixDevice | C | 113 | 113 | 113 | 0 | 0 |  |
| 1160 | Carrier | covered | CoolixDevice | C | 281 | 280 | 181 | 99 | 0 |  |
| 1161 | Carrier | unknown |  |  | 181 | 0 | 0 | 0 | 0 |  |
| 1162 | Carrier | unknown |  |  | 57 | 0 | 0 | 0 | 0 |  |
| 1163 | Carrier | near | MideaDevice | F | 501 | 465 | 0 | 0 | 0 | fahrenheit (465), temperature (448), fan (135), unknown (70) |
| 1164 | Carrier | covered | CoolixDevice | C | 238 | 231 | 191 | 40 | 1 |  |
| 1165 | Carrier | unknown |  |  | 321 | 0 | 0 | 0 | 0 |  |
| 1166 | Carrier | unknown |  |  | 130 | 0 | 0 | 0 | 0 |  |
| 1180 | Gree | unknown |  |  | 301 | 0 | 0 | 0 | 0 |  |
| 1181 | Gree | unknown |  |  | 79 | 0 | 0 | 0 | 0 |  |
| 1182 | Gree | unknown |  |  | 301 | 0 | 0 | 0 | 0 |  |
| 1183 | Gree | unknown |  |  | 961 | 0 | 0 | 0 | 0 |  |
| 1184 | Gree | unknown |  |  | 301 | 0 | 0 | 0 | 0 |  |
| 1185 | Gree | near | GreeDevice/YX1FSF | C | 301 | 299 | 225 | 0 | 0 | byte 7 bit 3 (60), light (14), mode (1), temp (1) |
| 1186 | Gree | unknown |  |  | 60 | 0 | 0 | 0 | 0 |  |
| 1187 | Gree | unknown |  |  | 61 | 0 | 0 | 0 | 0 |  |
| 1188 | Gree | unknown |  |  | 521 | 0 | 0 | 0 | 0 |  |
| 1200 | Tosot | near | GreeDevice/YAW1F | C | 301 | 301 | 0 | 60 | 0 | display_temp (121), xfan (120), swing_auto (120), swing_v (120), temp (1), mode (1), model_a (1) |
| 1220 | Sungold | near | MideaDevice | F | 201 | 201 | 0 | 0 | 0 | fahrenheit (201), temperature (192), unknown (61), fan (11) |
| 1240 | Consul | unknown |  |  | 118 | 0 | 0 | 0 | 0 |  |
| 1241 | Consul | near | KelonDevice | C | 241 | 219 | 0 | 174 | 0 | power_toggle (45), dry_grade (45), fan (30) |
| 1260 | Toshiba | unknown |  |  | 281 | 0 | 0 | 0 | 0 |  |
| 1261 |  Toshiba | unknown |  |  | 421 | 0 | 0 | 0 | 0 |  |
| 1262 | Toshiba | unknown |  |  | 354 | 0 | 0 | 0 | 0 |  |
| 1263 | Toshiba | unknown |  |  | 421 | 0 | 0 | 0 | 0 |  |
| 1264 | Toshiba | unknown |  |  | 421 | 0 | 0 | 0 | 0 |  |
| 1265 | Toshiba | unknown |  |  | 316 | 0 | 0 | 0 | 0 |  |
| 1280 | Fujitsu | near | FujitsuAcDevice/ARRAH2E | C | 144 | 135 | 1 | 0 | 52 (!) | byte 8 bit 0 (134), byte 15 bit 0 (86), byte 10 bit 0 (48), byte 15 bit 1 (48), byte 15 bit 2 (23), byte 15 bit 3 (12) |
| 1281 | Fujitsu | near | FujitsuAcDevice/ARRAH2E | C | 700 | 697 | 1 | 325 | 1 | byte 8 bit 0 (346), byte 15 bit 0 (320), byte 15 bit 1 (181), byte 15 bit 2 (128), byte 8 bit 5 (84), byte 15 bit 4 (61), byte 15 bit 5 (55), byte 8 bit 4 (50), byte 15 bit 7 (42), byte 8 bit 6 (40), byte 8 bit 7 (40), byte 15 bit 6 (38), byte 10 bit 0 (30), byte 10 bit 1 (30), byte 15 bit 3 (27), byte 10 bit 5 (25), byte 10 bit 2 (15) |
| 1282 | Fujitsu | near | FujitsuAcDevice/ARDB1 | C | 375 | 375 | 218 | 22 | 1 | frames (135) |
| 1283 | Fujitsu | unknown |  |  | 157 | 0 | 0 | 0 | 0 |  |
| 1284 | Fujitsu | unknown |  |  | 326 | 0 | 0 | 0 | 0 |  |
| 1285 | Fujitsu | unknown |  |  | 376 | 0 | 0 | 0 | 0 |  |
| 1286 | Fujitsu | covered | FujitsuAcDevice/ARDB1 | C | 326 | 325 | 200 | 125 | 0 |  |
| 1287 | Fujitsu | covered | FujitsuAcDevice/ARRAH2E | C | 336 | 336 | 224 | 112 | 0 |  |
| 1288 | Fujitsu | unknown |  |  | 209 | 0 | 0 | 0 | 0 |  |
| 1289 | Fujitsu | near | FujitsuAcDevice/ARREW4E | C | 209 | 193 | 1 | 0 | 52 (!) | byte 14 bit 5 (192), byte 11 bit 3 (192), byte 12 bit 2 (192), byte 14 bit 0 (192), byte 15 bit 7 (164), byte 11 bit 4 (128), byte 13 bit 0 (116), byte 15 bit 0 (107), byte 15 bit 1 (106), byte 13 bit 6 (101), byte 15 bit 2 (100), byte 15 bit 4 (95), byte 11 bit 0 (89), byte 15 bit 6 (87), byte 15 bit 5 (83), byte 13 bit 3 (72), byte 15 bit 3 (67), byte 13 bit 5 (65), byte 12 bit 0 (64), byte 13 bit 2 (63), byte 13 bit 1 (59), byte 13 bit 4 (42), byte 8 bit 4 (28), byte 8 bit 3 (28), byte 8 bit 5 (24), byte 8 bit 6 (24), byte 8 bit 7 (24) |
| 1290 | Fujitsu | unknown |  |  | 376 | 0 | 0 | 0 | 0 |  |
| 1291 | Fujitsu | unknown |  |  | 210 | 0 | 0 | 0 | 52 (!) |  |
| 1292 | Fujitsu | covered | FujitsuAcDevice/ARRAH2E | C | 1301 | 1298 | 850 | 448 | 0 |  |
| 1293 | Fujitsu | covered | FujitsuAcDevice/ARRAH2E | C | 651 | 650 | 426 | 224 | 0 |  |
| 1294 | Fujitsu | unknown |  |  | 548 | 0 | 0 | 0 | 0 |  |
| 1300 | Sharp | near | SharpAcDevice/A907 | C | 301 | 299 | 0 | 0 | 0 | byte 9 bit 4 (223), swing (149), temp_flags (148), temperature (139), frames (75), fan (74), mode (1), byte 9 bit 5 (1) |
| 1301 | Sharp | near | SharpAcDevice/A903 | C | 241 | 241 | 15 | 105 | 0 | temperature (117), mode (61), temp_flags (60) |
| 1320 | Haier | near | HaierYrw02Device/A | C | 301 | 301 | 0 | 0 | 0 | byte 2 bit 1 (301), byte 2 bit 4 (301) |
| 1321 | Haier | near | HaierYrw02Device/A | C | 181 | 181 | 50 | 130 | 0 | mode (1), swing_v (1) |
| 1322 | Haier | near | Haier176Device/A | C | 241 | 224 | 112 | 111 | 0 | frames (1) |
| 1340 | Tadiran | near | AmcorDevice | C | 136 | 136 | 57 | 3 | 0 | vent (76), temp (42), mode (1) |
| 1341 | Tadiran | unknown |  |  | 91 | 0 | 0 | 0 | 0 |  |
| 1342 | Tadiran | unknown |  |  | 121 | 0 | 0 | 0 | 0 |  |
| 1343 | Tadiran | unknown |  |  | 181 | 0 | 0 | 0 | 0 |  |
| 1344 | Tadiran | near | GreeDevice/YAW1F | C | 1321 | 1291 | 1059 | 231 | 60 | model_a (1), mode (1), xfan (1) |
| 1345 | Tadiran | unknown |  |  | 301 | 0 | 0 | 0 | 0 |  |
| 1346 | Tadiran | unknown |  |  | 137 | 0 | 0 | 0 | 0 |  |
| 1360 | Springer | covered | CoolixDevice | C | 273 | 265 | 209 | 56 | 8 |  |
| 1380 | Midea | covered | CoolixDevice | C | 157 | 151 | 114 | 37 | 0 |  |
| 1381 | Midea | covered | CoolixDevice | C | 67 | 66 | 66 | 0 | 0 |  |
| 1382 | Midea | covered | CoolixDevice | C | 281 | 275 | 205 | 70 | 0 |  |
| 1383 | Midea | covered | CoolixDevice | C | 225 | 216 | 120 | 96 | 0 |  |
| 1384 | Midea | covered | CoolixDevice | C | 65 | 62 | 62 | 0 | 0 |  |
| 1385 | Midea | unknown |  |  | 281 | 0 | 0 | 0 | 0 |  |
| 1386 | Midea | unknown |  |  | 141 | 0 | 0 | 0 | 0 |  |
| 1387 | Midea | covered | CoolixDevice | C | 281 | 258 | 153 | 105 | 0 |  |
| 1388 | Midea | unknown |  |  | 57 | 0 | 0 | 0 | 0 |  |
| 1389 | Midea | covered | CoolixDevice | F | 289 | 285 | 194 | 91 | 0 |  |
| 1390 | Midea | covered | CoolixDevice | C | 281 | 259 | 154 | 105 | 0 |  |
| 1391 | Midea | covered | CoolixDevice | C | 281 | 264 | 170 | 94 | 0 |  |
| 1392 | Midea | near | MideaDevice | C | 127 | 115 | 49 | 0 | 0 | temperature (56), unknown (24) |
| 1393 | Midea | near | MideaDevice | C | 131 | 130 | 97 | 0 | 0 | unknown (30), temperature (4), mode (1) |
| 1394 | Midea | covered | CoolixDevice | C | 281 | 278 | 194 | 84 | 0 |  |
| 1395 | Midea | near | MideaDevice | C | 284 | 278 | 112 | 81 | 0 | temperature (57), fan (43), unknown (42), mode (1) |
| 1400 | Samsung | unknown |  |  | 449 | 0 | 0 | 0 | 2 |  |
| 1401 | Samsung | unknown |  |  | 240 | 0 | 0 | 0 | 1 |  |
| 1402 | Samsung | near | GreeDevice/YAW1F | C | 751 | 726 | 0 | 0 | 0 | wifi (726), byte 5 bit 5 (726), byte 5 bit 7 (726), xfan (298), turbo (58), temp (2), display_temp (1), mode (1) |
| 1403 | Samsung | unknown |  |  | 417 | 0 | 0 | 0 | 0 |  |
| 1404 | Samsung | unknown |  |  | 841 | 0 | 0 | 0 | 0 |  |
| 1405 | Samsung | covered | CoolixDevice | C | 197 | 187 | 187 | 0 | 0 |  |
| 1406 | Samsung | unsupported |  |  | 0 | 0 | 0 | 0 | 195 (!) |  |
| 1407 | Samsung | unknown |  |  | 367 | 0 | 0 | 0 | 0 |  |
| 1408 | Samsung | unknown |  |  | 901 | 0 | 0 | 0 | 0 |  |
| 1420 | Sintech | unknown |  |  | 257 | 0 | 0 | 0 | 0 |  |
| 1440 | Akai | near | GoodweatherDevice | C | 341 | 337 | 193 | 115 | 0 | temperature (28), air_flow (17), byte 8 bit 4 (12) |
| 1441 | Akai | near | Tcl112AcDevice/GZ055BE1 | C | 257 | 254 | 0 | 0 | 0 | timer_indicator (254), temperature (121), fan (64), mode (1) |
| 1460 | Alliance | covered | CoolixDevice | C | 211 | 211 | 127 | 84 | 0 |  |
| 1480 | Junkers | near | GreeDevice/YAW1F | C | 181 | 181 | 45 | 15 | 0 | fan (61), model_a (60), display_temp (60), wifi (60), byte 5 bit 5 (60), swing_auto (60), swing_v (60), mode (1) |
| 1481 | Junkers | near | GreeDevice/YX1FSF | C | 361 | 360 | 0 | 60 | 0 | model_a (299), display_temp (299), wifi (60), byte 5 bit 5 (60), temp (11), mode (1) |
| 1500 | Sanyo | unknown |  |  | 157 | 0 | 0 | 0 | 0 |  |
| 1501 | Sanyo | unknown |  |  | 286 | 0 | 0 | 0 | 0 |  |
| 1520 | Hisense | unknown |  |  | 261 | 0 | 0 | 0 | 0 |  |
| 1521 | Hisense | near | KelonDevice | C | 121 | 114 | 0 | 59 | 0 | frames (55) |
| 1522 | Hisense | near | KelonDevice | C | 361 | 361 | 2 | 275 | 0 | power_toggle (84), dry_grade (84), fan (70) |
| 1540 | Whirlpool | covered | KelonDevice | C | 105 | 96 | 0 | 96 | 0 |  |
| 1560 | Tadiran | near | AmcorDevice | C | 136 | 136 | 57 | 3 | 0 | vent (76), temp (42), mode (1) |
| 1580 | Chigo | near | GoodweatherDevice | C | 118 | 112 | 1 | 0 | 0 | command (111), mode (36) |
| 1581 | Chigo | near | GoodweatherDevice | C | 290 | 286 | 0 | 0 | 0 | air_flow (286), command (285), mode (135), temperature (113), byte 8 bit 4 (14) |
| 1582 | Chigo | near | NeoclimaDevice | C | 222 | 222 | 0 | 0 | 0 | follow (222), byte 3 bit 5 (222), temp (80), mode (1) |
| 1600 | Beko | covered | ElectraAcDevice/aux | C | 154 | 151 | 101 | 50 | 0 |  |
| 1601 | Beko | unknown |  |  | 301 | 0 | 0 | 0 | 5 |  |
| 1602 | Beko | unknown |  |  | 321 | 0 | 0 | 0 | 0 |  |
| 1603 | Beko | near | HaierYrw02Device/A | C | 361 | 343 | 327 | 15 | 0 | mode (1) |
| 1604 | Beko | covered | CoolixDevice | C | 229 | 218 | 192 | 26 | 2 |  |
| 1620 | Tornado | covered | CoolixDevice | C | 118 | 112 | 88 | 24 | 0 |  |
| 1621 | Tornado | covered | KelonDevice | C | 121 | 117 | 0 | 117 | 0 |  |
| 1622 | Tornado | near | ElectraAcDevice/aux | C | 545 | 530 | 528 | 0 | 0 | heat_flag (2), power (2), mode (1), byte 6 bit 4 (1) |
| 1623 | Tornado | near | GoodweatherDevice | C | 91 | 89 | 0 | 0 | 0 | air_flow (89), command (88), swing_v (30), mode (1) |
| 1624 | Tornado | covered | KelonDevice | C | 121 | 117 | 0 | 117 | 0 |  |
| 1625 | Tornado | near | NeoclimaDevice | C | 91 | 88 | 0 | 0 | 0 | follow (88), byte 3 bit 5 (88) |
| 1626 | Tornado | near | ElectraAcDevice/aux | C | 121 | 120 | 119 | 0 | 0 | heat_flag (1), byte 4 bit 4 (1), power (1), fan (1), mode (1), byte 6 bit 4 (1), byte 10 bit 7 (1) |
| 1627 | Tornado | near | KelonDevice | C | 241 | 240 | 119 | 6 | 0 | dry_grade (111), temperature (60), fan (41) |
| 1640 | FUJIKO | unknown |  |  | 301 | 0 | 0 | 0 | 0 |  |
| 1660 | ROYAL | unknown |  |  | 281 | 0 | 0 | 0 | 0 |  |
| 1661 | ROYAL | unknown |  |  | 385 | 0 | 0 | 0 | 0 |  |
| 1680 | Mitsubishi Heavy | unknown |  |  | 157 | 0 | 0 | 0 | 0 |  |
| 1681 | Mitsubishi Heavy | near | MitsubishiHeavy88Device | C | 196 | 185 | 51 | 0 | 0 | byte 5 bit 4 (122), byte 5 bit 0 (122), swing_h (122), fan (85) |
| 1682 | Mitsubishi Heavy | near | TranscoldDevice | C | 157 | 152 | 0 | 0 | 0 | byte 0 bit 4 (152), fan (152), mode (99), temp (1) |
| 1683 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 196 | 177 | 0 | 0 | 0 | byte 13 bit 7 (177), temp (51), mode (1) |
| 1684 | Mitsubishi Heavy Industries | unknown |  |  | 121 | 0 | 0 | 0 | 0 |  |
| 1685 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 325 | 320 | 0 | 0 | 0 | byte 13 bit 6 (320), byte 13 bit 5 (320), temp (60), fan (52), mode (1) |
| 1686 | Mitsubishi Heavy | unknown |  |  | 326 | 0 | 0 | 0 | 0 |  |
| 1687 | Mitsubishi Heavy | unknown |  |  | 157 | 0 | 0 | 0 | 0 |  |
| 1688 | Mitsubishi Heavy | unknown |  |  | 261 | 0 | 0 | 0 | 0 |  |
| 1689 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 326 | 296 | 0 | 0 | 4 | byte 13 bit 7 (296), swing_h (177), swing_v (177), byte 13 bit 6 (119), temp (51), fan (48), mode (1) |
| 1690 | Mitsubishi Heavy | unknown |  |  | 326 | 0 | 0 | 0 | 0 |  |
| 1691 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 976 | 905 | 199 | 104 | 0 | byte 13 bit 6 (463), d (180), three (180), swing_h (137), swing_v (137), byte 13 bit 5 (124), temp (114), fan (96), mode (1), power (1) |
| 1692 | Mitsubishi Heavy | unknown |  |  | 157 | 0 | 0 | 0 | 13 |  |
| 1700 | Electrolux | covered | CoolixDevice | C | 57 | 57 | 57 | 0 | 0 |  |
| 1701 | Electrolux | near | GreeDevice/YAW1F | C | 181 | 181 | 177 | 3 | 0 | mode (1), temp (1) |
| 1702 | Electrolux | unknown |  |  | 362 | 0 | 0 | 0 | 14 |  |
| 1703 | Electrolux | covered | ElectraAcDevice/aux | C | 273 | 273 | 237 | 36 | 0 |  |
| 1704 | Electrolux | covered | CoolixDevice | C | 182 | 180 | 179 | 1 | 1 |  |
| 1705 | Electrolux | near | ElectraAcDevice/aux | C | 545 | 541 | 504 | 35 | 0 | heat_flag (2), power (2), fan (2), mode (2), swing_h (1), byte 2 bit 4 (1), byte 10 bit 7 (1) |
| 1720 | Erisson | unknown |  |  | 321 | 0 | 0 | 0 | 0 |  |
| 1740 | Kelvinator | covered | CoolixDevice/quiet | C | 351 | 346 | 248 | 98 | 0 |  |
| 1741 | Kelvinator | unknown |  |  | 451 | 0 | 0 | 0 | 0 |  |
| 1760 | Daitsu | covered | CoolixDevice | C | 281 | 273 | 192 | 81 | 0 |  |
| 1761 | Daitsu | unknown |  |  | 321 | 0 | 0 | 0 | 0 |  |
| 1762 | Daitsu | near | AirspoolDevice | F | 257 | 232 | 0 | 0 | 0 | byte 4 bit 6 (232), byte 3 bit 1 (232), byte 3 bit 0 (232), byte 4 bit 5 (232), byte 13 bit 3 (232), byte 4 bit 0 (232), byte 5 bit 6 (232), byte 13 bit 4 (231), byte 5 bit 2 (231), byte 6 bit 1 (187), byte 6 bit 0 (168), byte 13 bit 0 (65), byte 13 bit 2 (47), byte 13 bit 1 (46), byte 6 bit 7 (45), byte 6 bit 5 (45), byte 13 bit 5 (45), byte 6 bit 6 (45), byte 13 bit 6 (1), byte 11 bit 1 (1), byte 12 bit 7 (1) |
| 1763 | Daitsu | unknown |  |  | 301 | 0 | 0 | 0 | 0 |  |
| 1764 | Daitsu | near | GreeDevice/YAW1F | C | 301 | 271 | 0 | 0 | 0 | byte 5 bit 5 (271), byte 5 bit 7 (271), swing_v (44), temp (1), mode (1) |
| 1780 | Trotec | near | GreeDevice/YAW1F | C | 121 | 120 | 0 | 0 | 0 | byte 5 bit 5 (120), xfan (16), mode (1), temp (1) |
| 1781 | Trotec | near | GreeDevice/YAW1F | C | 226 | 219 | 203 | 15 | 0 | mode (1), temp (1) |
| 1782 | Trotec | near | MideaDevice | C | 169 | 169 | 59 | 67 | 0 | temperature (43), fan (29), unknown (14), mode (1) |
| 1800 | Ballu | covered | ElectraAcDevice/aux | C | 137 | 135 | 134 | 1 | 0 |  |
| 1801 | Ballu | covered | CoolixDevice | C | 168 | 164 | 86 | 78 | 1 |  |
| 1820 | Riello | near | Hitachi264Device | C | 273 | 255 | 0 | 0 | 0 | byte 29 bit 1 (254), byte 29 bit 5 (254), byte 29 bit 2 (254), byte 31 bit 2 (254), byte 31 bit 0 (254), fan (65), temperature (64), frames (1) |
| 1840 | Hualing | near | Mitsubishi112Device | C | 257 | 250 | 0 | 0 | 0 | swing_h (250), temperature (118), mode (65), byte 6 bit 3 (64) |
| 1860 | Simbio | unknown |  |  | 129 | 0 | 0 | 0 | 0 |  |
| 1880 | Saunier Duval | near | GreeDevice/YAW1F | C | 121 | 121 | 120 | 0 | 0 | model_a (1), mode (1), temp (1) |
| 1900 | TCL | unknown |  |  | 33 | 0 | 0 | 0 | 0 |  |
| 1901 | TCL | near | AirspoolDevice | F | 129 | 123 | 0 | 0 | 0 | byte 4 bit 6 (123), byte 3 bit 1 (123), byte 3 bit 0 (123), byte 4 bit 5 (123), byte 4 bit 0 (123), byte 5 bit 6 (123), byte 8 bit 7 (122), byte 5 bit 2 (122), byte 6 bit 1 (93), byte 6 bit 0 (92), byte 13 bit 5 (62), byte 13 bit 1 (61), byte 6 bit 6 (61), byte 13 bit 4 (61), byte 13 bit 7 (61), byte 13 bit 2 (60), byte 7 bit 7 (60), byte 7 bit 3 (60), byte 7 bit 4 (60), byte 13 bit 3 (60), byte 13 bit 6 (44), byte 6 bit 5 (32), byte 13 bit 0 (31), byte 6 bit 7 (30) |
| 1920 | Aokesi | near | ElectraAcDevice/aux | C | 118 | 118 | 0 | 0 | 0 | fan (118), temperature (40), mode (39), heat_flag (15) |
| 1940 | Electra | near | AirwellDevice | C | 181 | 179 | 0 | 1 | 0 | power_toggle (178), temperature (1) |
| 1941 | Electra | covered | CoolixDevice/16C | C | 181 | 181 | 181 | 0 | 0 |  |
| 1942 | Electra | unknown |  |  | 203 | 0 | 0 | 0 | 2 |  |
| 1943 | Electra | covered | CoolixDevice/16C | C | 181 | 181 | 181 | 0 | 0 |  |
| 1944 | Electra | covered | CoolixDevice | C | 113 | 110 | 108 | 2 | 0 |  |
| 1945 | Electra | unknown |  |  | 56 | 0 | 0 | 0 | 11 (!) |  |
| 1946 | Electra | unknown |  |  | 181 | 0 | 0 | 0 | 0 |  |
| 1947 | Electra | unknown |  |  | 127 | 0 | 0 | 0 | 0 |  |
| 1948 | Electra | unknown |  |  | 241 | 0 | 0 | 0 | 0 |  |
| 1960 | AUX | near | ElectraAcDevice/aux | C | 118 | 118 | 0 | 0 | 0 | fan (118), temperature (40), mode (39), heat_flag (15) |
| 1961 | AUX | covered | ElectraAcDevice/aux | C | 991 | 981 | 651 | 330 | 0 |  |
| 1962 | AUX | covered | ElectraAcDevice/aux | C | 427 | 405 | 358 | 47 | 0 |  |
| 1963 | AUX | covered | ElectraAcDevice/aux | C | 512 | 505 | 334 | 171 | 0 |  |
| 1980 | Fuji | covered | FujitsuAcDevice/ARDB1 | C | 79 | 79 | 79 | 0 | 0 |  |
| 2000 | Aeronik | near | GreeDevice/YAW1F | C | 301 | 299 | 0 | 0 | 0 | display_temp (299), wifi (299), byte 5 bit 5 (299), ifeel (298), swing_v (179), swing_auto (119), temp (1), mode (1) |
| 2020 | Ariston | covered | CoolixDevice | C | 281 | 272 | 175 | 97 | 0 |  |
| 2040 | Pioneer | near | MideaDevice | C | 501 | 488 | 0 | 0 | 0 | fahrenheit (488), temperature (472), fan (147), unknown (76), mode (1) |
| 2041 | Pioneer | unknown |  |  | 1121 | 0 | 0 | 0 | 0 |  |
| 2060 | Dimplex | near | Tcl112AcDevice/GZ055BE1 | C | 321 | 312 | 0 | 0 | 0 | timer_indicator (312), temperature (240), fan (139), byte 11 bit 0 (28), mode (1) |
| 2080 | Sendo | covered | ElectraAcDevice/aux | C | 205 | 201 | 201 | 0 | 0 |  |
| 2100 | Mirage | unknown |  |  | 57 | 0 | 0 | 0 | 0 |  |
| 2120 | Technibel | unknown |  |  | 392 | 0 | 0 | 0 | 0 |  |
| 2140 | Unionaire | unknown |  |  | 91 | 0 | 0 | 0 | 0 |  |
| 2160 | Lennox | unknown |  |  | 227 | 0 | 0 | 0 | 1 |  |
| 2161 | Lennox | covered | CoolixDevice | C | 281 | 264 | 124 | 140 | 0 |  |
| 2162 | Lennox | unknown |  |  | 331 | 0 | 0 | 0 | 0 |  |
| 2180 | Hokkaido | unknown |  |  | 122 | 0 | 0 | 0 | 0 |  |
| 2200 | IGC | near | KelonDevice | C | 241 | 230 | 0 | 178 | 0 | power_toggle (52), dry_grade (52), fan (39) |
| 2220 | Blueridge | near | MideaDevice | C | 526 | 496 | 0 | 21 | 0 | fahrenheit (475), temperature (455), fan (185), unknown (99), mode (1) |
| 2240 | DeLonghi | unknown |  |  | 154 | 0 | 0 | 0 | 0 |  |
| 2241 | DeLonghi | near | ElectraAcDevice/aux | C | 181 | 177 | 102 | 15 | 0 | temperature (60), fan (45) |
| 2242 | DeLonghi | unknown |  |  | 501 | 0 | 0 | 0 | 0 |  |
| 2243 | DeLonghi | near | Mitsubishi112Device | C | 321 | 311 | 0 | 0 | 0 | swing_h (311), swing_v (311), temperature (184), mode (65), fan (64), byte 6 bit 3 (64) |
| 2260 | Profio | unknown |  |  | 321 | 0 | 0 | 0 | 0 |  |
| 2280 | Hantech | unknown |  |  | 91 | 0 | 0 | 0 | 0 |  |
| 2281 | Hantech | unknown |  |  | 97 | 0 | 0 | 0 | 0 |  |
| 2300 | Zanussi | near | GoodweatherDevice | C | 242 | 237 | 0 | 0 | 0 | air_flow (237), command (236), temperature (56), mode (1) |
| 2301 | Zanussi | near | KelvinatorDevice | C | 151 | 143 | 0 | 0 | 0 | timer (143), turbo (30), fan (29), ion_filter (1), xfan (1), mode (1) |
| 2320 | Whynter | unknown |  |  | 225 | 0 | 0 | 0 | 3 |  |
| 2321 | Whynter | unknown |  |  | 205 | 0 | 0 | 0 | 2 |  |
| 2340 | Vortex | unknown |  |  | 241 | 0 | 0 | 0 | 0 |  |
| 2360 | Flouu | near | GreeDevice/YX1FSF | C | 196 | 192 | 0 | 0 | 0 | display_temp (191), mode (61), byte 7 bit 3 (59), temp (57), byte 5 bit 5 (1) |
| 2380 | BAXI | covered | ElectraAcDevice/aux | C | 627 | 602 | 602 | 0 | 34 |  |
| 2400 | Yamatsu | unknown |  |  | 257 | 0 | 0 | 0 | 0 |  |
| 2420 | VS | near | ElectraAcDevice/aux | C | 340 | 323 | 0 | 0 | 1 | byte 3 bit 4 (248), byte 3 bit 3 (196), byte 3 bit 0 (143), byte 3 bit 1 (93), byte 3 bit 2 (90), heat_flag (60), byte 2 bit 2 (44), byte 2 bit 4 (44), byte 2 bit 0 (34), byte 2 bit 1 (34), fan (17), byte 3 bit 5 (11) |
| 2440 | Vaillant | unknown |  |  | 196 | 0 | 0 | 0 | 0 |  |
| 2460 | FanWorld | covered | ElectraAcDevice/aux | C | 273 | 263 | 242 | 21 | 0 |  |
| 2480 | Rotenso | covered | CoolixDevice | C | 281 | 281 | 197 | 84 | 0 |  |
| 2500 | Endesa | near | KelonDevice | C | 361 | 361 | 3 | 274 | 0 | power_toggle (84), dry_grade (84), fan (70) |
| 2520 | Galanz | unknown |  |  | 257 | 0 | 0 | 0 | 0 |  |
| 2540 | Audinac | near | MirageDevice/KKG9AC1 | C | 301 | 301 | 0 | 0 | 0 | seconds (241), minutes (241), mode (241), frames (60), hours (1), swing_power (1) |
| 2560 | Mistral | near | Trotec3550Device | C | 271 | 245 | 59 | 158 | 0 | temp_f (27), mode (1) |
| 2580 | KOREL | unknown |  |  | 793 | 0 | 0 | 0 | 33 |  |
| 2600 | Equation | unknown |  |  | 301 | 0 | 0 | 0 | 0 |  |
| 2620 | Komeco | covered | CoolixDevice | C | 281 | 280 | 196 | 84 | 0 |  |
| 2640 | Fisher | unknown |  |  | 169 | 0 | 0 | 0 | 0 |  |
| 2641 | Fisher | covered | CoolixDevice | C | 281 | 255 | 171 | 84 | 0 |  |
| 2660 | Hyundai | unknown |  |  | 269 | 0 | 0 | 0 | 0 |  |
| 2661 | Hyundai | unknown |  |  | 482 | 0 | 0 | 0 | 0 |  |
| 2662 | Hyndai | unknown |  |  | 341 | 0 | 0 | 0 | 0 |  |
| 2700 | Kolin | unknown |  |  | 64 | 0 | 0 | 0 | 0 |  |
| 2720 | AEG | unknown |  |  | 273 | 0 | 0 | 0 | 1 |  |
| 2740 | Bosch | unknown |  |  | 376 | 0 | 0 | 0 | 0 |  |
| 2760 | Tristar | near | GoodweatherDevice | C | 137 | 129 | 5 | 16 | 0 | command (106), temperature (39), byte 8 bit 4 (5), mode (1), air_flow (1) |
| 2780 | Xiaomi | unknown |  |  | 993 | 0 | 0 | 0 | 0 |  |
| 2800 | ELGIN | covered | ElectraAcDevice/aux | C | 35 | 35 | 18 | 17 | 0 |  |
| 2801 | ELGIN | unknown |  |  | 29 | 0 | 0 | 0 | 0 |  |
| 2820 | Pearl | unknown |  |  | 181 | 0 | 0 | 0 | 0 |  |
| 2840 | HTW | unknown |  |  | 281 | 0 | 0 | 0 | 0 |  |
| 2860 | Senville | unknown |  |  | 211 | 0 | 0 | 0 | 0 |  |
| 2880 | Bora | unknown |  |  | 312 | 0 | 0 | 0 | 0 |  |
| 2900 | Goodman | near | MideaDevice | C | 169 | 165 | 82 | 0 | 0 | temperature (56), unknown (40), mode (1) |
| 2920 | Best | near | AirspoolDevice | F | 241 | 241 | 0 | 0 | 0 | byte 4 bit 6 (241), byte 3 bit 1 (241), byte 3 bit 0 (241), byte 4 bit 5 (241), byte 13 bit 3 (241), byte 4 bit 0 (241), byte 13 bit 4 (241), byte 5 bit 6 (241), byte 5 bit 2 (240), byte 6 bit 1 (181), byte 6 bit 0 (181), byte 13 bit 2 (61), byte 13 bit 0 (60), byte 13 bit 1 (60), byte 6 bit 7 (60), byte 6 bit 5 (60), byte 13 bit 5 (60), byte 6 bit 6 (60) |
| 2940 | SAGA | near | GoodweatherDevice | C | 545 | 544 | 0 | 0 | 0 | command (543), air_flow (271), byte 8 bit 4 (32), temperature (32), swing_v (14), mode (1) |
| 2960 | EcoAir | near | MideaDevice | C | 281 | 278 | 0 | 0 | 0 | fahrenheit (278), temperature (278), fan (98), unknown (41), mode (1) |
| 2980 | Agratto | unknown |  |  | 94 | 0 | 0 | 0 | 0 |  |
| 3000 | Philco | near | MirageDevice/KKG29AC1 | C | 273 | 248 | 0 | 0 | 0 | pad5 (248), mode (130) |
| 3020 | Klasse | near | AirspoolDevice | F | 241 | 232 | 0 | 0 | 0 | byte 13 bit 6 (232), byte 3 bit 1 (232), byte 4 bit 6 (232), byte 6 bit 1 (232), byte 3 bit 0 (232), byte 4 bit 5 (232), byte 3 bit 4 (232), byte 13 bit 3 (232), byte 4 bit 0 (232), byte 5 bit 2 (231), byte 6 bit 0 (152), byte 13 bit 0 (80), byte 13 bit 2 (1) |
| 3040 | Viessmann | near | GreeDevice/YAW1F | C | 241 | 230 | 0 | 0 | 0 | wifi (230), byte 5 bit 5 (230), byte 5 bit 7 (230), mode (1) |
| 3060 | HappyTree | near | AirspoolDevice | F | 241 | 236 | 0 | 0 | 0 | byte 4 bit 6 (236), byte 3 bit 1 (236), byte 8 bit 6 (236), byte 8 bit 7 (236), byte 3 bit 0 (236), byte 4 bit 5 (236), byte 4 bit 0 (236), byte 5 bit 2 (235), byte 7 bit 7 (234), byte 7 bit 3 (234), byte 7 bit 4 (234), byte 13 bit 6 (204), byte 6 bit 6 (159), byte 6 bit 1 (159), byte 6 bit 0 (156), byte 13 bit 0 (80), byte 6 bit 7 (78), byte 13 bit 1 (77), byte 13 bit 2 (76), byte 6 bit 5 (75), byte 13 bit 5 (75), byte 13 bit 7 (66), byte 13 bit 3 (3), byte 13 bit 4 (2) |
| 3080 | Voltas | near | VoltasDevice/122LZF | C | 722 | 659 | 0 | 1 | 0 | wifi (638), temperature (424), fan (223), swing_v (144), swing_h_change (134), byte 6 bit 3 (43), off_timer_hrs (43), byte 6 bit 0 (43), byte 6 bit 2 (43), byte 2 bit 4 (43), byte 5 bit 6 (43), byte 3 bit 5 (43), on_timer_hrs (43), byte 6 bit 6 (43), mode (43), off_timer_mins (43), byte 4 bit 6 (43), power (43), on_timer_mins (43), swing_h (39), byte 8 bit 0 (18), byte 1 bit 4 (13), byte 3 bit 4 (6), frames (1) |
| 3100 | Cecotec | near | AirspoolDevice | F | 321 | 305 | 0 | 0 | 0 | byte 4 bit 6 (305), byte 3 bit 1 (305), byte 8 bit 7 (305), byte 3 bit 0 (305), byte 4 bit 5 (305), byte 4 bit 0 (305), byte 5 bit 6 (305), byte 5 bit 2 (304), byte 6 bit 1 (230), byte 6 bit 0 (225), byte 6 bit 6 (219), byte 13 bit 5 (177), byte 13 bit 1 (155), byte 13 bit 4 (155), byte 13 bit 2 (154), byte 13 bit 6 (152), byte 13 bit 3 (150), byte 6 bit 7 (121), byte 13 bit 7 (101), byte 6 bit 5 (89), byte 13 bit 0 (80) |
| 3120 | Cooper & Hunter | near | GreeDevice/YAW1F | C | 601 | 546 | 0 | 0 | 0 | byte 5 bit 5 (546), wifi (544), byte 5 bit 7 (544), temp (5), mode (3), byte 3 bit 7 (2), byte 3 bit 6 (2), byte 3 bit 5 (2), model_a (2), power (2), fan (2), swing_auto (2), byte 3 bit 4 (2), light (2), swing_v (2) |
| 3140 | Argo | unknown |  |  | 181 | 0 | 0 | 0 | 0 |  |
| 3160 | AquaThermal | near | AirtonDevice | C | 321 | 319 | 0 | 0 | 0 | byte 4 bit 4 (318), fan (64), turbo (48), mode (1), temperature (1) |
| 3180 | Devanti | unknown |  |  | 257 | 0 | 0 | 0 | 0 |  |
| 3200 | Friedrich | near | Lg2Device/AKB74955603 | F | 325 | 325 | 136 | 0 | 0 | power (108), frames (81), temperature (36) |
| 3220 | Mundoclima | covered | ElectraAcDevice/aux | C | 341 | 324 | 68 | 256 | 0 |  |
| 3240 | Casper | unknown |  |  | 749 | 0 | 0 | 0 | 0 |  |
| 3300 | PARKAIR | covered | ElectraAcDevice/aux | C | 121 | 120 | 105 | 15 | 0 |  |
| 3320 | Chunlan | unknown |  |  | 256 | 0 | 0 | 0 | 0 |  |
| 3340 | Wide | near | MirageDevice/KKG29AC1 | C | 273 | 263 | 0 | 0 | 0 | pad5 (247), recycle_heat (66), swing_v (64), fan (48), temperature (48), frames (16) |
| 3360 | Kaden | covered | CoolixDevice | C | 281 | 273 | 163 | 110 | 0 |  |
| 3380 | Zephir | covered | ElectraAcDevice/aux | C | 141 | 136 | 105 | 31 | 0 |  |
| 4060 | LG | unsupported |  |  | 0 | 0 | 0 | 0 | 157 (!) |  |
| 4100 | Daikin | unsupported |  |  | 0 | 0 | 0 | 0 | 157 (!) |  |
| 4124 | Mitsubishi Electric | unsupported |  |  | 0 | 0 | 0 | 0 | 170 (!) |  |
| 4129 | Mitsubishi Electric | unsupported |  |  | 0 | 0 | 0 | 0 | 170 (!) |  |
| 4180 | Gree | unsupported |  |  | 0 | 0 | 0 | 0 | 301 (!) |  |
| 4181 | Gree | unsupported |  |  | 0 | 0 | 0 | 0 | 301 (!) |  |
| 4285 | Fujitsu | unsupported |  |  | 0 | 0 | 0 | 0 | 376 (!) |  |
| 4380 | Midea | unsupported |  |  | 0 | 0 | 0 | 0 | 281 (!) |  |
| 4381 | Midea | unsupported |  |  | 0 | 0 | 0 | 0 | 58 (!) |  |
| 4580 | Chigo | unsupported |  |  | 0 | 0 | 0 | 0 | 118 (!) |  |
| 4581 | Chigo | unsupported |  |  | 0 | 0 | 0 | 0 | 157 (!) |  |
| 4800 | TechnoLux | unsupported |  |  | 0 | 0 | 0 | 0 | 241 (!) |  |
| 5120 | Daikin | near | PanasonicAcDevice/JKE | C | 703 | 679 | 0 | 0 | 0 | byte 2 bit 0 (679), byte 3 bit 7 (679), byte 1 bit 5 (679), byte 0 bit 4 (679), byte 3 bit 4 (679), on_timer (679), byte 1 bit 3 (679), byte 9 bit 5 (679), byte 2 bit 1 (679), byte 11 bit 2 (679), byte 10 bit 7 (679), byte 19 bit 3 (679), byte 9 bit 6 (679), byte 3 bit 5 (679), byte 10 bit 1 (679), byte 0 bit 0 (679), byte 2 bit 2 (679), byte 10 bit 2 (679), byte 10 bit 6 (679), byte 20 bit 7 (679), byte 8 bit 4 (679), byte 3 bit 6 (679), model_23 (679), byte 1 bit 1 (679), byte 9 bit 7 (679), byte 3 bit 2 (679), byte 9 bit 1 (679), off_timer (679), byte 9 bit 3 (679), byte 8 bit 1 (679), byte 1 bit 7 (679), byte 9 bit 4 (679), byte 10 bit 0 (679), byte 2 bit 6 (679), byte 2 bit 7 (679), byte 1 bit 6 (679), byte 0 bit 1 (679), byte 15 bit 7 (679), byte 1 bit 4 (679), byte 8 bit 0 (679), byte 7 bit 2 (679), swing_v (343), temperature (121), fan (99), byte 14 bit 0 (30), byte 14 bit 6 (14), mode (2), byte 14 bit 7 (1) |
| 5140 | Mitsubishi Electric | near | Mitsubishi112Device | C | 1345 | 1308 | 0 | 0 | 0 | swing_h (1308), temperature (428), swing_v (184), fan (1), mode (1) |
| 5520 | Hisense | near | KelonDevice | C | 241 | 223 | 0 | 167 | 0 | power_toggle (56), dry_grade (56), fan (42) |
| 7062 | LG | covered | LgAcDevice/GE6711AR2853M | C | 105 | 101 | 53 | 48 | 0 |  |
| 7065 | LG | near | LgNativeDevice/generic | C | 181 | 176 | 1 | 0 | 0 | fan (175), change (174), temp (101), mode (43) |
| 7124 | Mitsubishi | unknown |  |  | 481 | 0 | 0 | 0 | 0 |  |
| 7260 | Toshiba | unknown |  |  | 449 | 0 | 0 | 0 | 112 (!) |  |
| 7285 | Fujitsu | unknown |  |  | 376 | 0 | 0 | 0 | 0 |  |
| 7300 | SHARP | near | SharpAcDevice/A903 | C | 179 | 179 | 0 | 0 | 1 | byte 11 bit 1 (179), temp_flags (59), temperature (56), fan (45), mode (1) |
| 7386 | Midea | unknown |  |  | 351 | 0 | 0 | 0 | 0 |  |
| 7740 | Kelvinator | unknown |  |  | 351 | 0 | 0 | 0 | 0 |  |
| 7741 | Family | unknown |  |  | 401 | 0 | 0 | 0 | 0 |  |
| 8700 | Kolin | unknown |  |  | 256 | 0 | 0 | 0 | 0 |  |
| 8720 | Viomi | unknown |  |  | 161 | 0 | 0 | 0 | 0 |  |
| 8800 | Sigma | unknown |  |  | 242 | 0 | 0 | 0 | 0 |  |

## Clusters of unknown files

### 7 files, 1141 codes, 729 keys

files: 1388, 1660, 2100, 2320, 2801, 2840, 2860

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(548, 518, 1614), header=(4355, 4416), footer=(518,), gap=5208),
        "s1": Section(PulseDistance(548, 518, 1614), header=(4355, 4416), footer=(518,), gap=101502),
    },
)
```

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

### 2 files, 727 codes, 656 keys

files: 2740, 7386

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(540, 540, 1614), header=(4400, 4385), footer=(540,), gap=5208),
        "s1": Section(PulseDistance(540, 540, 1614), header=(4400, 4385), footer=(540,), gap=5208),
        "s2": Section(PulseDistance(540, 540, 1614), header=(4400, 4385), footer=(540,), gap=0),
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

### 2 files, 451 codes, 322 keys

files: 1165, 1166

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(548, 487, 1523), header=(8436, 4172), footer=(548,), gap=19917),
        "s1": Section(PulseDistance(548, 487, 1523), header=(8436, 4172), footer=(548,), gap=19917),
        "s2": Section(PulseDistance(548, 487, 1523), header=(8436, 4172), footer=(548,), gap=101502),
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

### 1 files, 1801 codes, 1801 keys

files: 1115

```
Protocol(
    "draft",
    {
        "s0": Section(None, header=(9806,), gap=9776),
        "s1": Section(None, header=(9806,), gap=9776),
        "s2": Section(PulseDistance(365, 365, 944), header=(4629, 2467), footer=(365,), gap=20282),
        "s3": Section(PulseDistance(365, 365, 944), header=(365, 944), footer=(4629,), gap=101502),
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

files: 7285

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(418, 450, 482), header=(3376, 1704), footer=(418,), gap=0),
    },
)
```

### 1 files, 367 codes, 367 keys

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

### 1 files, 286 codes, 286 keys

files: 1501

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 365, 1218), header=(3380, 1614), footer=(457,), gap=101502),
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

### 1 files, 209 codes, 209 keys

files: 1288

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(609, 518, 1675), header=(8984, 4507), footer=(609,), gap=101502),
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

files: 1283

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(640, 487, 1614), header=(9075, 4446), footer=(609,), gap=101502),
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

### 1 files, 154 codes, 154 keys

files: 2240

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(548, 548, 579), header=(9045, 4477), footer=(548,), gap=101502),
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

- SmartIR 1287: Fujitsu / AR-REB1E: name taken by FujitsuAcDevice/ARREB1E
- SmartIR 1293: Fujitsu / AR-REB1E: name taken by FujitsuAcDevice/ARREB1E
- SmartIR 1540: Whirlpool / SPIS412L: name taken by WhirlpoolAcDevice/DG11J13A

## Rows: 22 proposed (rows.py)

