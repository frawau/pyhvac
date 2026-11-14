# SmartIR climate import

- covered: 164
- near: 122
- unknown: 61
- unsupported: 9
- not JSON: 2680

## Files

Skipped: codes that could not be read; flagged (!) when they are over 10% of the file.

Codes: read from the file, decoded by the candidate, verified (sent by pyhvac for their labelled state), relabelled (sent by pyhvac for another state: the file's label is wrong).

| file | brand | verdict | candidate | units | codes | decoded | verified | relabelled | skipped | gaps |
|---|---|---|---|---|---|---|---|---|---|---|
| 1000 | Toyotomi | covered | GreeDevice/YX1FSF | C | 181 | 181 | 118 | 63 | 0 |  |
| 1001 | Toyotomi | unknown |  |  | 241 | 0 | 0 | 0 | 0 |  |
| 1020 | Panasonic | covered | PanasonicAcDevice/JKE-M13 | C | 121 | 120 | 119 | 1 | 0 |  |
| 1021 | Panasonic | near | PanasonicAcDevice/JKE | C | 121 | 121 | 0 | 1 | 0 | byte 19 bit 3 (120), model_23 (120), byte 20 bit 7 (120) |
| 1022 | Panasonic | near | PanasonicAcDevice/RKR | C | 349 | 329 | 174 | 1 | 0 | byte 14 bit 0 (154) |
| 1023 | Panasonic | covered | PanasonicAcDevice/RKR-81 | C | 361 | 361 | 275 | 86 | 0 |  |
| 1024 | Panasonic | covered | PanasonicAcDevice/JKE-M13 | C | 241 | 240 | 238 | 2 | 0 |  |
| 1025 | Panasonic | covered | PanasonicAcDevice/RKR-81 | C | 25 | 25 | 9 | 16 | 0 |  |
| 1026 | Panasonic | covered | PanasonicAcDevice/JKE-M13 | C | 181 | 179 | 104 | 75 | 0 |  |
| 1027 | Panasonic | covered | PanasonicAc32Device | C | 181 | 165 | 164 | 1 | 0 |  |
| 1028 | Panasonic | covered | PanasonicAcDevice/RKR-81 | C | 271 | 271 | 185 | 86 | 0 |  |
| 1029 | Panasonic | near | PanasonicAcDevice/DKE | C | 361 | 345 | 343 | 1 | 0 | model_23 (1) |
| 1030 | Panasonic | covered | PanasonicAcDevice/JKE-M13 | C | 2160 | 2117 | 1614 | 503 | 0 |  |
| 1031 | Panasonic | covered | MitsubishiHeavy88Device | C | 209 | 209 | 159 | 50 | 0 |  |
| 1032 | Panasonic | near | PanasonicNativeDevice/4 way cassette | C | 301 | 293 | 18 | 1 | 0 | byte 17 bit 5 (274), byte 23 bit 5 (274), mode (274), byte 17 bit 6 (274), byte 23 bit 7 (274), swing (274), fan (52), profile (42) |
| 1040 | Ggeneral Electric | near | ElectraAcDevice | C | 205 | 205 | 0 | 1 | 0 | byte 2 bit 1 (187), byte 3 bit 4 (153), byte 2 bit 0 (153), byte 3 bit 3 (153), byte 2 bit 3 (136), byte 3 bit 2 (119), byte 3 bit 0 (93), byte 2 bit 4 (68), temperature (68), byte 2 bit 2 (68), byte 3 bit 1 (57), fan (17) |
| 1041 | Ggeneral Electric | covered | KelvinatorDevice | C | 301 | 297 | 59 | 238 | 0 |  |
| 1042 | Ggeneral Electric | covered | FujitsuAcDevice/ARRAH2E | C | 336 | 335 | 223 | 112 | 0 |  |
| 1043 | General Electric | near | FujitsuAcDevice/ARRAH2E | C | 336 | 285 | 1 | 0 | 0 | byte 8 bit 0 (284), byte 15 bit 0 (208), byte 15 bit 1 (113), byte 15 bit 2 (85), byte 10 bit 0 (76), byte 15 bit 4 (32), byte 15 bit 3 (27), byte 15 bit 7 (26), byte 15 bit 5 (24), byte 10 bit 1 (20), byte 8 bit 6 (19), byte 8 bit 4 (19), byte 8 bit 5 (19), byte 15 bit 6 (18), byte 8 bit 7 (18), byte 10 bit 2 (10) |
| 1044 | General Electric | near | HaierYrw02Device/A | F | 365 | 363 | 0 | 1 | 0 | use_fahrenheit (362), extra_degree_f (121), temperature (119), quiet (79) |
| 1060 | LG | covered | LgAcDevice/GE6711AR2853M | C | 261 | 261 | 209 | 52 | 0 |  |
| 1061 | LG | near | Lg2Device/AKB74955603 | C | 361 | 361 | 1 | 360 | 0 |  |
| 1062 | LG | covered | LgAcDevice/GE6711AR2853M | C | 261 | 259 | 159 | 100 | 0 |  |
| 1063 | LG | covered | Lg2Device/AKB74955603 | C | 391 | 390 | 246 | 144 | 0 |  |
| 1064 | LG | covered | LgAcDevice/GE6711AR2853M | C | 79 | 79 | 53 | 26 | 0 |  |
| 1065 | LG | near | Lg2Device/AKB74955603 | C | 181 | 178 | 1 | 177 | 0 |  |
| 1066 | LG | covered | Lg2Device/AKB74955603 | C | 391 | 390 | 235 | 155 | 0 |  |
| 1067 | LG | covered | LgAcDevice/GE6711AR2853M | C | 79 | 79 | 79 | 0 | 0 |  |
| 1068 | LG | covered | Lg2Device/AKB74955603 | C | 313 | 313 | 85 | 228 | 0 |  |
| 1069 | LG | covered | Lg2Device/AKB74955603 | C | 209 | 209 | 113 | 96 | 0 |  |
| 1070 | LG | covered | Lg2Device/AKB74955603 | C | 261 | 261 | 165 | 96 | 0 |  |
| 1080 | Hitachi | covered | Hitachi264Device | C | 136 | 136 | 135 | 1 | 0 |  |
| 1081 | Hitachi | near | Hitachi296Device | C | 137 | 133 | 8 | 1 | 0 | byte 11 bit 0 (121), byte 11 bit 2 (121), byte 11 bit 1 (121), byte 9 bit 1 (34), byte 9 bit 3 (34), temperature (8), unset_high (8) |
| 1082 | Hitachi | near | Hitachi296Device | C | 341 | 333 | 37 | 19 | 0 | byte 11 bit 0 (176), byte 11 bit 2 (176), byte 11 bit 1 (176), byte 9 bit 1 (100), byte 9 bit 3 (100), temperature (97), byte 11 bit 4 (82), mode (82), byte 11 bit 6 (82), fan (67), unset_high (15) |
| 1083 | LG | covered | Hitachi264Device | C | 205 | 204 | 153 | 51 | 0 |  |
| 1084 | Hitachi | near | HitachiAcDevice | C | 358 | 351 | 0 | 1 | 0 | byte 15 bit 5 (350), byte 14 bit 5 (350), byte 14 bit 6 (350), byte 15 bit 6 (350), min_temp (110), byte 9 bit 5 (77), temperature (68), byte 9 bit 6 (1), byte 9 bit 4 (1) |
| 1085 | Hitachi | near | Mitsubishi112Device | C | 38 | 37 | 0 | 1 | 0 | swing_h (36), byte 11 bit 7 (36), swing_v (36), temperature (5) |
| 1086 | Hitachi | unknown |  |  | 144 | 0 | 0 | 0 | 0 |  |
| 1087 | Hitachi | near | HitachiAcDevice | C | 426 | 421 | 156 | 19 | 0 | min_temp (166), temperature (92), byte 9 bit 5 (85), fan (47) |
| 1088 | Hitachi | unknown |  |  | 426 | 0 | 0 | 0 | 0 |  |
| 1089 | Hitachi | near | HitachiAcDevice | C | 358 | 293 | 0 | 0 | 0 | byte 23 bit 0 (186), byte 25 bit 5 (186), byte 25 bit 4 (186), frames (107), byte 9 bit 5 (33), temperature (33), min_temp (2), mode (1) |
| 1090 | Hitachi | near | HitachiAcDevice | C | 1701 | 1701 | 0 | 1 | 0 | byte 23 bit 0 (1700), temperature (340), fan (204), min_temp (20) |
| 1091 | Hitachi | near | KelonDevice/16C | C | 452 | 448 | 121 | 237 | 0 | smart (90), temperature (90) |
| 1092 | Hitachi | near | HitachiAcDevice | C | 205 | 201 | 0 | 1 | 0 | byte 15 bit 5 (200), byte 14 bit 5 (200), byte 14 bit 6 (200) |
| 1100 | Daikin | near | Daikin216Device | C | 261 | 259 | 154 | 53 | 0 | byte 14 bit 7 (52), temperature (52), fan (39) |
| 1101 | Daikin | covered | Daikin312Device | C | 521 | 521 | 520 | 1 | 0 |  |
| 1102 | Daikin | near | Daikin128Device | C | 271 | 271 | 0 | 270 | 0 | frames (1) |
| 1103 | Daikin | covered | MitsubishiAcDevice/remote | C | 65 | 62 | 61 | 1 | 0 |  |
| 1104 | Daikin | unknown |  |  | 316 | 0 | 0 | 0 | 0 |  |
| 1105 | Dalkin | unknown |  |  | 1036 | 0 | 0 | 0 | 0 |  |
| 1106 | Daikin | covered | Daikin312Device | C | 456 | 453 | 452 | 1 | 0 |  |
| 1107 | Daikin | near | Daikin160Device | C | 313 | 308 | 86 | 96 | 0 | temperature (78), byte 16 bit 7 (78), fan (65), mode (48) |
| 1108 | Daikin | covered | Daikin312Device | C | 601 | 601 | 600 | 1 | 0 |  |
| 1109 | Daikin | near | Daikin176Device | C | 193 | 189 | 1 | 1 | 0 | alt_mode (187), fan (95), temperature (1) |
| 1110 | Daikin | covered | DaikinArcDevice | C | 181 | 181 | 180 | 1 | 0 |  |
| 1111 | Daikin | covered | Daikin160Device | C | 67 | 67 | 66 | 1 | 0 |  |
| 1112 | Daikin | covered | DaikinArcDevice | C | 361 | 361 | 360 | 1 | 0 |  |
| 1113 | Daikin | covered | GreeDevice/YX1FSF | C | 598 | 587 | 499 | 88 | 0 |  |
| 1114 | Daikin | covered | Daikin312Device | C | 520 | 517 | 516 | 1 | 0 |  |
| 1115 | Daikin | near | Daikin64Device | C | 1801 | 1764 | 0 | 1763 | 0 | frames (1) |
| 1116 | Daikin | near | Daikin176Device | C | 205 | 198 | 151 | 0 | 0 | fan (47) |
| 1117 | Daikin | covered | Daikin312Device | C | 553 | 551 | 550 | 1 | 0 |  |
| 1118 | Daikin | covered | Daikin312Device | C | 85 | 85 | 84 | 1 | 0 |  |
| 1119 | Daikin | covered | Daikin216Device | C | 43 | 41 | 13 | 28 | 0 |  |
| 1120 | Mitsubishi Electric | near | MitsubishiAcDevice/remote | C | 180 | 174 | 0 | 1 | 1 | byte 14 bit 1 (166), byte 32 bit 1 (166), swing_v (60), temperature (56), frames (7) |
| 1121 | Mitsubishi Electric | covered | MitsubishiAcDevice/remote | C | 65 | 62 | 61 | 1 | 0 |  |
| 1122 | Mitsubishi | unknown |  |  | 265 | 0 | 0 | 0 | 0 |  |
| 1123 | Mitsubishi Electric | near | MitsubishiHeavy152Device | C | 91 | 87 | 0 | 1 | 0 | byte 13 bit 5 (86), byte 13 bit 6 (14), swing_v (14), temp (1) |
| 1124 | Mitsubishi | unknown |  |  | 481 | 0 | 0 | 0 | 0 |  |
| 1125 | Mitsubishi Electric | near | MitsubishiAcDevice/remote | C | 257 | 200 | 0 | 0 | 0 | byte 14 bit 0 (189), byte 14 bit 1 (189), byte 32 bit 1 (189), swing_h (189), byte 32 bit 0 (189), temperature (120), frames (11) |
| 1126 | Mitsubishi Electric | unknown |  |  | 257 | 0 | 0 | 0 | 0 |  |
| 1127 | Mitsubishi Electric | covered | MitsubishiAcDevice/remote | C | 161 | 141 | 140 | 1 | 0 |  |
| 1128 | Mitsubishi Electric | covered | MitsubishiAcDevice/remote | C | 321 | 310 | 162 | 148 | 0 |  |
| 1129 | Mitsubishi Electric  | covered | MitsubishiAcDevice/remote | C | 2689 | 2656 | 1985 | 671 | 0 |  |
| 1130 | Mitsubishi Electric | covered | MitsubishiAcDevice/remote | C | 193 | 177 | 71 | 106 | 0 |  |
| 1131 | Mitsubishi Electric | covered | Mitsubishi136Device | C | 145 | 141 | 96 | 45 | 0 |  |
| 1132 | Mitsubishi Electric | covered | Tcl112AcDevice/GZ055BE1-R | C | 193 | 181 | 61 | 120 | 0 |  |
| 1133 | Mitsubishi Electric Starmex | near | MitsubishiAcDevice/remote | C | 2129 | 2127 | 753 | 1262 | 0 | frames (112) |
| 1134 | Mitsubishi Electric | covered | MitsubishiAcDevice/remote | C | 241 | 239 | 88 | 151 | 0 |  |
| 1135 | Mitsubishi | near | MitsubishiAcDevice/remote | C | 481 | 480 | 0 | 1 | 0 | swing_h (477), temperature (180), swing_v (64), frames (2) |
| 1136 | Mitsubishi Electric | covered | MitsubishiAcDevice/remote | C | 289 | 249 | 97 | 152 | 0 |  |
| 1137 | Mitsubishi Electric | covered | MitsubishiAcDevice/remote | C | 2241 | 1911 | 995 | 916 | 0 |  |
| 1138 | Mitsubishi Electric | near | MitsubishiAcDevice/remote | C | 321 | 317 | 0 | 1 | 0 | byte 14 bit 4 (312), isee (312), swing_h (312), byte 32 bit 4 (312), mode (76), mode_aux (76), temperature (75), ecocool (16), frames (4) |
| 1139 | Mitsubishi | unknown |  |  | 58 | 0 | 0 | 0 | 0 |  |
| 1140 | Actron | covered | CoolixDevice | C | 113 | 113 | 113 | 0 | 0 |  |
| 1160 | Carrier | covered | CoolixDevice | C | 281 | 281 | 195 | 86 | 0 |  |
| 1161 | Carrier | unknown |  |  | 181 | 0 | 0 | 0 | 0 |  |
| 1162 | Carrier | unknown |  |  | 57 | 0 | 0 | 0 | 0 |  |
| 1163 | Carrier | covered | MideaDevice/RG57-F | F | 501 | 485 | 481 | 4 | 0 |  |
| 1164 | Carrier | covered | CoolixDevice | C | 238 | 233 | 193 | 40 | 1 |  |
| 1165 | Carrier | unknown |  |  | 321 | 0 | 0 | 0 | 0 |  |
| 1166 | Carrier | unknown |  |  | 130 | 0 | 0 | 0 | 0 |  |
| 1180 | Gree | near | GreeDevice/YX1FSF | C | 301 | 300 | 238 | 2 | 0 | swing_auto (60), byte 5 bit 5 (60), wifi (60), model_a (60), display_temp (60), swing_v (60) |
| 1181 | Gree | near | KelvinatorDevice | C | 79 | 61 | 21 | 23 | 0 | frames (11), byte 7 bit 3 (6), turbo (3), quiet (2) |
| 1182 | Gree | near | KelvinatorDevice | C | 301 | 301 | 61 | 239 | 0 | frames (1) |
| 1183 | Gree | covered | GreeDevice/YAW1F-0 | C | 961 | 952 | 474 | 478 | 0 |  |
| 1184 | Gree | near | GreeDevice/YX1FSF-H | C | 301 | 298 | 201 | 62 | 0 | byte 5 bit 5 (35), turbo (11) |
| 1185 | Gree | covered | GreeDevice/YX1FSF-H | C | 301 | 300 | 285 | 15 | 0 |  |
| 1186 | Gree | covered | GreeDevice/YAW1F-wifi | C | 60 | 57 | 56 | 1 | 0 |  |
| 1187 | Gree | near | GreeDevice/YAW1F | C | 61 | 61 | 0 | 61 | 0 |  |
| 1188 | Gree | near | GreeDevice/YAW1F-wifi | F | 521 | 493 | 0 | 1 | 0 | byte 5 bit 7 (490), use_fahrenheit (490), temp_extra_degree_f (173), frames (2), temp (1) |
| 1200 | Tosot | near | GreeDevice/YAW1F | C | 301 | 301 | 0 | 181 | 0 | display_temp (120) |
| 1220 | Sungold | covered | MideaDevice/RG57-F | F | 201 | 201 | 189 | 12 | 0 |  |
| 1240 | Consul | unknown |  |  | 118 | 0 | 0 | 0 | 0 |  |
| 1241 | Consul | covered | KelonDevice/dry-grade | C | 241 | 238 | 169 | 69 | 0 |  |
| 1260 | Toshiba | covered | ToshibaAcDevice | C | 281 | 220 | 78 | 142 | 0 |  |
| 1261 |  Toshiba | covered | ToshibaAcDevice | C | 421 | 420 | 127 | 293 | 0 |  |
| 1262 | Toshiba | covered | MideaDevice/RG57-F | F | 354 | 316 | 312 | 4 | 0 |  |
| 1263 | Toshiba | near | ToshibaAcDevice | C | 421 | 319 | 92 | 174 | 0 | frames (53) |
| 1264 | Toshiba | covered | ToshibaAcDevice | C | 421 | 404 | 124 | 280 | 0 |  |
| 1265 | Toshiba | near | ToshibaAcDevice | C | 316 | 308 | 0 | 280 | 0 | frames (28) |
| 1280 | Fujitsu | near | FujitsuAcDevice/ARRAH2E | C | 144 | 142 | 1 | 0 | 52 (!) | byte 8 bit 0 (141), byte 15 bit 0 (90), byte 15 bit 1 (52), byte 10 bit 0 (51), byte 15 bit 2 (26), byte 15 bit 3 (13) |
| 1281 | Fujitsu | near | FujitsuAcDevice/ARRAH2E | C | 700 | 698 | 1 | 325 | 1 | byte 8 bit 0 (347), byte 15 bit 0 (321), byte 15 bit 1 (182), byte 15 bit 2 (128), byte 8 bit 5 (84), byte 15 bit 4 (61), byte 15 bit 5 (55), byte 8 bit 4 (50), byte 15 bit 7 (42), byte 8 bit 6 (40), byte 8 bit 7 (40), byte 15 bit 6 (38), byte 10 bit 0 (30), byte 10 bit 1 (30), byte 15 bit 3 (27), byte 10 bit 5 (25), byte 10 bit 2 (15) |
| 1282 | Fujitsu | unknown |  |  | 375 | 0 | 0 | 0 | 1 |  |
| 1283 | Fujitsu | unknown |  |  | 157 | 0 | 0 | 0 | 0 |  |
| 1284 | Fujitsu | unknown |  |  | 326 | 0 | 0 | 0 | 0 |  |
| 1285 | Fujitsu | unknown |  |  | 376 | 0 | 0 | 0 | 0 |  |
| 1286 | Fujitsu | covered | FujitsuAcDevice/ARDB1 | C | 326 | 325 | 200 | 125 | 0 |  |
| 1287 | Fujitsu | covered | FujitsuAcDevice/ARRAH2E | C | 336 | 336 | 224 | 112 | 0 |  |
| 1288 | Fujitsu | unknown |  |  | 209 | 0 | 0 | 0 | 0 |  |
| 1289 | Fujitsu | near | FujitsuAcDevice/ARREW4E | C | 209 | 193 | 1 | 0 | 52 (!) | byte 14 bit 0 (192), byte 14 bit 5 (192), byte 11 bit 3 (192), byte 12 bit 2 (192), byte 15 bit 7 (164), byte 11 bit 4 (128), byte 13 bit 0 (116), byte 15 bit 0 (107), byte 15 bit 1 (106), byte 13 bit 6 (101), byte 15 bit 2 (100), byte 15 bit 4 (95), byte 11 bit 0 (89), byte 15 bit 6 (87), byte 15 bit 5 (83), byte 13 bit 3 (72), byte 15 bit 3 (67), byte 13 bit 5 (65), byte 12 bit 0 (64), byte 13 bit 2 (63), byte 13 bit 1 (59), byte 13 bit 4 (42), byte 8 bit 3 (28), byte 8 bit 4 (28), byte 8 bit 6 (24), byte 8 bit 5 (24), byte 8 bit 7 (24) |
| 1290 | Fujitsu | unknown |  |  | 376 | 0 | 0 | 0 | 0 |  |
| 1291 | Fujitsu | near | FujitsuAcDevice/ARRAH2E | C | 210 | 206 | 1 | 0 | 52 (!) | byte 11 bit 4 (204), byte 12 bit 1 (204), byte 8 bit 0 (204), byte 13 bit 4 (178), byte 13 bit 6 (178), byte 15 bit 5 (150), byte 13 bit 0 (137), byte 15 bit 0 (130), byte 15 bit 7 (121), byte 15 bit 2 (108), byte 13 bit 3 (100), byte 15 bit 1 (100), byte 15 bit 3 (98), byte 15 bit 6 (87), byte 11 bit 0 (78), byte 15 bit 4 (76), byte 13 bit 2 (67), byte 11 bit 2 (62), byte 13 bit 1 (51), byte 10 bit 0 (39), byte 8 bit 5 (35), byte 8 bit 7 (35), byte 8 bit 6 (30), byte 8 bit 4 (30), byte 11 bit 3 (13), frames (1) |
| 1292 | Fujitsu | covered | FujitsuAcDevice/ARRAH2E | C | 1301 | 1300 | 852 | 448 | 0 |  |
| 1293 | Fujitsu | covered | FujitsuAcDevice/ARRAH2E | C | 651 | 651 | 427 | 224 | 0 |  |
| 1294 | Fujitsu | near | FujitsuAcDevice/ARRAH2E | C | 548 | 522 | 390 | 131 | 0 | frames (1) |
| 1300 | Sharp | near | SharpAcDevice/A907 | C | 301 | 301 | 0 | 0 | 0 | byte 9 bit 4 (225), temp_flags (150), swing (150), temperature (141), fan (75), frames (75), mode (1), byte 9 bit 5 (1) |
| 1301 | Sharp | near | SharpAcDevice/A903 | C | 241 | 241 | 15 | 106 | 0 | temperature (116), temp_flags (60), mode (60) |
| 1320 | Haier | near | HaierYrw02Device/A | C | 301 | 301 | 0 | 1 | 0 | byte 2 bit 4 (300), byte 2 bit 1 (300) |
| 1321 | Haier | covered | HaierYrw02Device/A | C | 181 | 181 | 50 | 131 | 0 |  |
| 1322 | Haier | covered | Haier176Device/A | C | 241 | 233 | 120 | 113 | 0 |  |
| 1340 | Tadiran | near | AmcorDevice | C | 136 | 136 | 57 | 3 | 0 | vent (76), temp (42), mode (1) |
| 1341 | Tadiran | unknown |  |  | 91 | 0 | 0 | 0 | 0 |  |
| 1342 | Tadiran | covered | GreeDevice/YAW1F | C | 121 | 113 | 56 | 57 | 0 |  |
| 1343 | Tadiran | near | GreeDevice/YAW1F-wifi | C | 181 | 157 | 20 | 1 | 0 | byte 5 bit 7 (135), fan (19), model_a (3), frames (1) |
| 1344 | Tadiran | covered | GreeDevice/YAW1F | C | 1321 | 1315 | 1076 | 239 | 60 |  |
| 1345 | Tadiran | near | AmcorDevice | C | 301 | 295 | 57 | 3 | 0 | byte 13 bit 0 (203), byte 13 bit 1 (203), byte 5 bit 1 (203), byte 5 bit 0 (203), vent (89), fan (60), mode (1), frames (1) |
| 1346 | Tadiran | covered | AmcorDevice | C | 137 | 135 | 134 | 1 | 0 |  |
| 1360 | Springer | covered | CoolixDevice | C | 273 | 273 | 213 | 60 | 8 |  |
| 1380 | Midea | covered | CoolixDevice | C | 157 | 156 | 117 | 39 | 0 |  |
| 1381 | Midea | covered | CoolixDevice | C | 67 | 67 | 67 | 0 | 0 |  |
| 1382 | Midea | covered | CoolixDevice | C | 281 | 280 | 208 | 72 | 0 |  |
| 1383 | Midea | covered | CoolixDevice | C | 225 | 221 | 123 | 98 | 0 |  |
| 1384 | Midea | covered | CoolixDevice | C | 65 | 64 | 64 | 0 | 0 |  |
| 1385 | Midea | unknown |  |  | 281 | 0 | 0 | 0 | 0 |  |
| 1386 | Midea | unknown |  |  | 141 | 0 | 0 | 0 | 0 |  |
| 1387 | Midea | covered | CoolixDevice | C | 281 | 274 | 164 | 110 | 0 |  |
| 1388 | Midea | covered | CoolixDevice | C | 57 | 54 | 53 | 1 | 0 |  |
| 1389 | Midea | covered | CoolixDevice | F | 289 | 289 | 193 | 96 | 0 |  |
| 1390 | Midea | covered | CoolixDevice | C | 281 | 275 | 165 | 110 | 0 |  |
| 1391 | Midea | covered | CoolixDevice | C | 281 | 275 | 177 | 98 | 0 |  |
| 1392 | Midea | covered | MideaDevice/RG57 | C | 127 | 125 | 125 | 0 | 0 |  |
| 1393 | Midea | covered | MideaDevice/RG57 | C | 131 | 131 | 130 | 1 | 0 |  |
| 1394 | Midea | covered | CoolixDevice | C | 281 | 280 | 196 | 84 | 0 |  |
| 1395 | Midea | covered | MideaDevice/RG57 | C | 284 | 280 | 276 | 4 | 0 |  |
| 1400 | Samsung | unknown |  |  | 449 | 0 | 0 | 0 | 2 |  |
| 1401 | Samsung | near | SamsungAcDevice | C | 240 | 229 | 88 | 2 | 1 | frames (109), byte 19 bit 2 (30), byte 18 bit 4 (1) |
| 1402 | Samsung | near | GreeDevice/YAW1F-wifi | C | 751 | 732 | 403 | 300 | 0 | turbo (29), xfan (29) |
| 1403 | Samsung | unknown |  |  | 417 | 0 | 0 | 0 | 0 |  |
| 1404 | Samsung | unknown |  |  | 841 | 0 | 0 | 0 | 0 |  |
| 1405 | Samsung | covered | CoolixDevice | C | 197 | 192 | 192 | 0 | 0 |  |
| 1406 | Samsung | unsupported |  |  | 0 | 0 | 0 | 0 | 195 (!) |  |
| 1407 | Samsung | unknown |  |  | 367 | 0 | 0 | 0 | 0 |  |
| 1408 | Samsung | unknown |  |  | 901 | 0 | 0 | 0 | 0 |  |
| 1420 | Sintech | near | Mitsubishi112Device | C | 257 | 193 | 0 | 1 | 0 | byte 4 bit 7 (192), swing_h (192), byte 8 bit 6 (192), temperature (64), fan (16) |
| 1440 | Akai | near | GoodweatherDevice | C | 341 | 341 | 197 | 115 | 0 | temperature (28), air_flow (17), byte 8 bit 4 (12) |
| 1441 | Akai | covered | Tcl112AcDevice/GZ055BE1-R | C | 257 | 254 | 128 | 126 | 0 |  |
| 1460 | Alliance | covered | CoolixDevice | C | 211 | 211 | 127 | 84 | 0 |  |
| 1480 | Junkers | near | GreeDevice/YAW1F | C | 181 | 181 | 45 | 16 | 0 | model_a (60), fan (60), swing_auto (60), byte 5 bit 5 (60), wifi (60), display_temp (60), swing_v (60) |
| 1481 | Junkers | near | GreeDevice/YX1FSF | C | 361 | 361 | 0 | 61 | 0 | model_a (300), display_temp (300), byte 5 bit 5 (60), wifi (60), temp (12) |
| 1500 | Sanyo | unknown |  |  | 157 | 0 | 0 | 0 | 0 |  |
| 1501 | Sanyo | unknown |  |  | 286 | 0 | 0 | 0 | 0 |  |
| 1520 | Hisense | covered | FujitsuAcDevice/ARRAH2E | C | 261 | 261 | 261 | 0 | 0 |  |
| 1521 | Hisense | unknown |  |  | 121 | 0 | 0 | 0 | 0 |  |
| 1522 | Hisense | covered | KelonDevice/dry-grade | C | 361 | 361 | 97 | 264 | 0 |  |
| 1540 | Whirlpool | covered | KelonDevice | C | 105 | 101 | 100 | 1 | 0 |  |
| 1560 | Tadiran | near | AmcorDevice | C | 136 | 136 | 57 | 3 | 0 | vent (76), temp (42), mode (1) |
| 1580 | Chigo | near | GoodweatherDevice | C | 118 | 112 | 1 | 0 | 0 | command (111), mode (36) |
| 1581 | Chigo | near | GoodweatherDevice | C | 290 | 287 | 0 | 1 | 0 | air_flow (286), command (286), mode (135), temperature (114), byte 8 bit 4 (14) |
| 1582 | Chigo | near | NeoclimaDevice | C | 222 | 222 | 0 | 1 | 0 | byte 3 bit 5 (221), follow (221), temp (80) |
| 1600 | Beko | covered | ElectraAcDevice/aux | C | 154 | 154 | 101 | 53 | 0 |  |
| 1601 | Beko | covered | GreeDevice/YAW1F | C | 301 | 297 | 132 | 165 | 5 |  |
| 1602 | Beko | unknown |  |  | 321 | 0 | 0 | 0 | 0 |  |
| 1603 | Beko | covered | HaierYrw02Device/A | C | 361 | 358 | 342 | 16 | 0 |  |
| 1604 | Beko | covered | CoolixDevice | C | 229 | 225 | 182 | 43 | 2 |  |
| 1620 | Tornado | covered | CoolixDevice | C | 118 | 117 | 91 | 26 | 0 |  |
| 1621 | Tornado | covered | KelonDevice/16C | C | 121 | 119 | 118 | 1 | 0 |  |
| 1622 | Tornado | near | ElectraAcDevice/aux | C | 545 | 544 | 542 | 0 | 0 | power (2), heat_flag (2), byte 6 bit 4 (1), mode (1) |
| 1623 | Tornado | near | GoodweatherDevice | C | 91 | 90 | 0 | 1 | 0 | air_flow (89), command (89), swing_v (30) |
| 1624 | Tornado | covered | KelonDevice/16C | C | 121 | 120 | 119 | 1 | 0 |  |
| 1625 | Tornado | near | NeoclimaDevice | C | 91 | 88 | 0 | 0 | 0 | byte 3 bit 5 (88), follow (88) |
| 1626 | Tornado | near | ElectraAcDevice/aux | C | 121 | 121 | 120 | 0 | 0 | byte 6 bit 4 (1), mode (1), fan (1), power (1), heat_flag (1), byte 4 bit 4 (1), byte 10 bit 7 (1) |
| 1627 | Tornado | near | KelonDevice/dry-grade | C | 241 | 240 | 134 | 46 | 0 | temperature (60), dry_grade (56) |
| 1640 | FUJIKO | unknown |  |  | 301 | 0 | 0 | 0 | 0 |  |
| 1660 | ROYAL | near | CoolixDevice | C | 281 | 274 | 179 | 81 | 0 | sensor_temp (14), byte 0 bit 2 (14), mode (14), byte 0 bit 0 (14), byte 6 bit 2 (14), byte 0 bit 1 (14), fan (14), temp (14), byte 6 bit 0 (14), byte 6 bit 1 (14) |
| 1661 | ROYAL | covered | Tcl112AcDevice/TAC09CHSD-X03 | C | 385 | 368 | 139 | 229 | 0 |  |
| 1680 | Mitsubishi Heavy | covered | MitsubishiHeavy88Device | C | 157 | 143 | 109 | 34 | 0 |  |
| 1681 | Mitsubishi Heavy | near | MitsubishiHeavy88Device | C | 196 | 196 | 52 | 1 | 0 | byte 5 bit 4 (130), byte 5 bit 0 (130), swing_h (130), fan (91) |
| 1682 | Mitsubishi Heavy | near | TranscoldDevice | C | 157 | 156 | 0 | 0 | 0 | fan (156), byte 0 bit 4 (156), mode (103), temp (1) |
| 1683 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 196 | 193 | 0 | 1 | 0 | byte 13 bit 7 (192), temp (57) |
| 1684 | Mitsubishi Heavy Industries | near | PanasonicAcDevice/JKE-M13 | C | 121 | 113 | 59 | 0 | 0 | frames (54) |
| 1685 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 325 | 323 | 0 | 1 | 0 | byte 13 bit 6 (322), byte 13 bit 5 (322), temp (60), fan (52) |
| 1686 | Mitsubishi Heavy | covered | MitsubishiHeavy152Device | C | 326 | 303 | 207 | 96 | 0 |  |
| 1687 | Mitsubishi Heavy | covered | MitsubishiHeavy88Device | C | 157 | 142 | 105 | 37 | 0 |  |
| 1688 | Mitsubishi Heavy | covered | MitsubishiHeavy88Device | C | 261 | 235 | 162 | 73 | 0 |  |
| 1689 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 326 | 322 | 0 | 1 | 4 | byte 13 bit 7 (321), swing_h (192), swing_v (192), byte 13 bit 6 (129), temp (57), fan (52) |
| 1690 | Mitsubishi Heavy | unknown |  |  | 326 | 0 | 0 | 0 | 0 |  |
| 1691 | Mitsubishi Heavy | near | MitsubishiHeavy152Device | C | 976 | 956 | 207 | 113 | 0 | byte 13 bit 6 (494), three (190), d (190), swing_h (142), swing_v (142), byte 13 bit 5 (129), temp (120), fan (102) |
| 1692 | Mitsubishi Heavy | covered | MitsubishiHeavy88Device | C | 157 | 136 | 73 | 63 | 13 |  |
| 1700 | Electrolux | covered | CoolixDevice | C | 57 | 57 | 57 | 0 | 0 |  |
| 1701 | Electrolux | covered | GreeDevice/YAW1F | C | 181 | 181 | 177 | 4 | 0 |  |
| 1702 | Electrolux | unknown |  |  | 362 | 0 | 0 | 0 | 14 |  |
| 1703 | Electrolux | covered | ElectraAcDevice/aux | C | 273 | 273 | 237 | 36 | 0 |  |
| 1704 | Electrolux | covered | CoolixDevice | C | 182 | 181 | 180 | 1 | 1 |  |
| 1705 | Electrolux | near | ElectraAcDevice/aux | C | 545 | 543 | 506 | 35 | 0 | mode (2), fan (2), power (2), heat_flag (2), byte 2 bit 4 (1), swing_h (1), byte 10 bit 7 (1) |
| 1720 | Erisson | covered | Tcl112AcDevice/GZ055BE1-R | C | 321 | 292 | 118 | 174 | 0 |  |
| 1740 | Kelvinator | covered | CoolixDevice/quiet | C | 351 | 350 | 252 | 98 | 0 |  |
| 1741 | Kelvinator | covered | KelvinatorDevice | C | 451 | 414 | 98 | 316 | 0 |  |
| 1760 | Daitsu | covered | CoolixDevice | C | 281 | 279 | 195 | 84 | 0 |  |
| 1761 | Daitsu | covered | Tcl112AcDevice/TAC09CHSD-R | C | 321 | 313 | 123 | 190 | 0 |  |
| 1762 | Daitsu | near | Tcl112AcDevice/TAC09CHSD-R | C | 257 | 241 | 115 | 125 | 0 | model (1), byte 11 bit 1 (1) |
| 1763 | Daitsu | covered | GreeDevice/YAW1F-0 | C | 301 | 300 | 299 | 1 | 0 |  |
| 1764 | Daitsu | near | GreeDevice/YAW1F-wifi | C | 301 | 294 | 0 | 1 | 0 | wifi (293), swing_v (58) |
| 1780 | Trotec | covered | GreeDevice/YAW1F-0 | C | 121 | 121 | 104 | 17 | 0 |  |
| 1781 | Trotec | covered | GreeDevice/YAW1F | C | 226 | 224 | 208 | 16 | 0 |  |
| 1782 | Trotec | near | MideaDevice/RG57 | C | 169 | 169 | 115 | 40 | 0 | fan_auto (14) |
| 1800 | Ballu | covered | ElectraAcDevice/aux | C | 137 | 136 | 135 | 1 | 0 |  |
| 1801 | Ballu | covered | CoolixDevice | C | 168 | 166 | 87 | 79 | 1 |  |
| 1820 | Riello | near | Hitachi264Device | C | 273 | 268 | 0 | 1 | 0 | byte 31 bit 2 (267), byte 29 bit 2 (267), byte 29 bit 5 (267), byte 29 bit 1 (267), byte 31 bit 0 (267), fan (65), temperature (64) |
| 1840 | Hualing | covered | Tcl112AcDevice/GZ055BE1-R | C | 257 | 248 | 131 | 117 | 0 |  |
| 1860 | Simbio | unknown |  |  | 129 | 0 | 0 | 0 | 0 |  |
| 1880 | Saunier Duval | covered | GreeDevice/YAW1F | C | 121 | 121 | 120 | 1 | 0 |  |
| 1900 | TCL | covered | Tcl112AcDevice/TAC09CHSD-RH | C | 33 | 30 | 27 | 3 | 0 |  |
| 1901 | TCL | covered | Tcl112AcDevice/TAC09CHSD-X83 | C | 129 | 124 | 45 | 79 | 0 |  |
| 1920 | Aokesi | near | ElectraAcDevice | C | 118 | 118 | 0 | 1 | 0 | fan (117), byte 9 bit 4 (54), mode (39) |
| 1940 | Electra | covered | AirwellDevice | C | 181 | 180 | 178 | 2 | 0 |  |
| 1941 | Electra | covered | CoolixDevice/16C | C | 181 | 181 | 181 | 0 | 0 |  |
| 1942 | Electra | unknown |  |  | 203 | 0 | 0 | 0 | 2 |  |
| 1943 | Electra | covered | CoolixDevice/16C | C | 181 | 181 | 181 | 0 | 0 |  |
| 1944 | Electra | covered | CoolixDevice | C | 113 | 113 | 111 | 2 | 0 |  |
| 1945 | Electra | near | AirwellDevice | C | 56 | 55 | 29 | 16 | 11 (!) | unnamed_high (10), fan (7) |
| 1946 | Electra | covered | AirwellDevice | C | 181 | 181 | 180 | 1 | 0 |  |
| 1947 | Electra | near | SanyoAc88Device | C | 127 | 123 | 0 | 1 | 0 | mode (122), byte 29 bit 0 (122), start_timer (122), byte 18 bit 0 (122), byte 3 bit 7 (122), byte 14 bit 7 (122), byte 25 bit 7 (122), byte 7 bit 0 (122), byte 12 bit 2 (111), byte 23 bit 2 (111), byte 1 bit 2 (111), byte 12 bit 4 (108), byte 1 bit 4 (108), byte 23 bit 4 (108), byte 12 bit 0 (91), byte 23 bit 0 (91), byte 1 bit 0 (90), byte 32 bit 7 (70), byte 21 bit 7 (70), byte 10 bit 7 (65), byte 10 bit 0 (41), byte 21 bit 0 (41), byte 32 bit 0 (41), byte 21 bit 1 (40), byte 10 bit 1 (40), byte 32 bit 1 (40), byte 23 bit 1 (30), byte 12 bit 1 (30), byte 1 bit 1 (29), byte 1 bit 6 (14), byte 23 bit 5 (14), byte 12 bit 6 (14), byte 23 bit 3 (14), byte 12 bit 3 (14), byte 23 bit 6 (14), byte 1 bit 5 (14), byte 12 bit 5 (14), byte 1 bit 3 (14) |
| 1948 | Electra | unknown |  |  | 241 | 0 | 0 | 0 | 0 |  |
| 1960 | AUX | near | ElectraAcDevice | C | 118 | 118 | 0 | 1 | 0 | fan (117), byte 9 bit 4 (54), mode (39) |
| 1961 | AUX | covered | ElectraAcDevice/aux | C | 991 | 989 | 659 | 330 | 0 |  |
| 1962 | AUX | covered | ElectraAcDevice/aux | C | 427 | 421 | 370 | 51 | 0 |  |
| 1963 | AUX | covered | ElectraAcDevice/aux | C | 512 | 510 | 339 | 171 | 0 |  |
| 1980 | Fuji | covered | FujitsuAcDevice/ARDB1 | C | 79 | 79 | 79 | 0 | 0 |  |
| 2000 | Aeronik | near | GreeDevice/YAW1F-wifi | C | 301 | 301 | 0 | 1 | 0 | ifeel (299), byte 5 bit 7 (299), display_temp (299), swing_v (179), swing_auto (119), frames (1) |
| 2020 | Ariston | covered | CoolixDevice | C | 281 | 276 | 193 | 83 | 0 |  |
| 2040 | Pioneer | covered | MideaDevice/RG57-F | F | 501 | 496 | 495 | 1 | 0 |  |
| 2041 | Pioneer | near | Tcl112AcDevice/TAC09CHSD-XC0 | F | 1121 | 1091 | 103 | 722 | 0 | byte 26 bit 2 (266), half_degree (256), byte 7 bit 7 (184), byte 7 bit 4 (184), swing_h (184), quiet (36), byte 20 bit 6 (24), temperature (1) |
| 2060 | Dimplex | near | Tcl112AcDevice/GZ055BE1-R | C | 321 | 321 | 18 | 275 | 0 | byte 11 bit 0 (28), temperature (16), fan (3) |
| 2080 | Sendo | covered | ElectraAcDevice/aux | C | 205 | 201 | 201 | 0 | 0 |  |
| 2100 | Mirage | covered | CoolixDevice | C | 57 | 53 | 53 | 0 | 0 |  |
| 2120 | Technibel | near | ArgoDevice/WREM2 | C | 392 | 369 | 0 | 1 | 0 | byte 7 bit 1 (368), byte 8 bit 3 (368), byte 7 bit 0 (368), byte 1 bit 5 (368), byte 8 bit 4 (368), byte 5 bit 5 (368), room_temp (368), byte 5 bit 6 (368), byte 8 bit 1 (368), byte 7 bit 2 (368), byte 5 bit 7 (368), byte 7 bit 6 (263), byte 7 bit 7 (228), byte 7 bit 5 (196), byte 7 bit 4 (184), byte 7 bit 3 (177), mode (92), byte 8 bit 2 (92), filter (91), byte 8 bit 0 (40), temperature (2) |
| 2140 | Unionaire | unknown |  |  | 91 | 0 | 0 | 0 | 0 |  |
| 2160 | Lennox | unknown |  |  | 227 | 0 | 0 | 0 | 1 |  |
| 2161 | Lennox | covered | CoolixDevice | C | 281 | 265 | 137 | 128 | 0 |  |
| 2162 | Lennox | covered | GreeDevice/YAW1F | C | 331 | 325 | 193 | 132 | 0 |  |
| 2180 | Hokkaido | unknown |  |  | 122 | 0 | 0 | 0 | 0 |  |
| 2200 | IGC | covered | KelonDevice/dry-grade | C | 241 | 241 | 64 | 177 | 0 |  |
| 2220 | Blueridge | covered | MideaDevice/RG57-F | F | 526 | 507 | 485 | 22 | 0 |  |
| 2240 | DeLonghi | unknown |  |  | 154 | 0 | 0 | 0 | 0 |  |
| 2241 | DeLonghi | near | ElectraAcDevice/aux | C | 181 | 180 | 105 | 15 | 0 | temperature (60), fan (45) |
| 2242 | DeLonghi | unknown |  |  | 501 | 0 | 0 | 0 | 0 |  |
| 2243 | DeLonghi | near | Mitsubishi112Device | C | 321 | 320 | 0 | 1 | 0 | swing_h (319), swing_v (319), temperature (184), fan (64), mode (64), byte 6 bit 3 (64) |
| 2260 | Profio | unknown |  |  | 321 | 0 | 0 | 0 | 0 |  |
| 2280 | Hantech | near | TechnibelAcDevice | C | 91 | 89 | 5 | 36 | 0 | temp_change (28), fan_change (20), temp (18) |
| 2281 | Hantech | near | TechnibelAcDevice | C | 97 | 95 | 4 | 45 | 0 | temp_change (30), fan_change (16), temp (15), swing_v (12) |
| 2300 | Zanussi | near | GoodweatherDevice | C | 242 | 239 | 0 | 1 | 0 | air_flow (238), command (238), temperature (56) |
| 2301 | Zanussi | near | KelvinatorDevice | C | 151 | 149 | 0 | 1 | 0 | timer (145), fan (30), turbo (30), frames (3) |
| 2320 | Whynter | unknown |  |  | 225 | 0 | 0 | 0 | 3 |  |
| 2321 | Whynter | unknown |  |  | 205 | 0 | 0 | 0 | 2 |  |
| 2340 | Vortex | near | KelvinatorDevice | C | 241 | 240 | 0 | 240 | 0 |  |
| 2360 | Flouu | near | GreeDevice/YX1FSF-H | C | 196 | 192 | 0 | 1 | 0 | display_temp (191), mode (60), temp (56) |
| 2380 | BAXI | covered | ElectraAcDevice/aux | C | 627 | 620 | 620 | 0 | 34 |  |
| 2400 | Yamatsu | unknown |  |  | 257 | 0 | 0 | 0 | 0 |  |
| 2420 | VS | near | ElectraAcDevice/aux | C | 340 | 335 | 1 | 1 | 1 | byte 3 bit 4 (253), byte 3 bit 3 (201), byte 3 bit 0 (149), byte 3 bit 2 (97), byte 3 bit 1 (95), heat_flag (65), byte 2 bit 4 (47), byte 2 bit 2 (47), byte 2 bit 1 (35), byte 2 bit 0 (35), fan (17), byte 3 bit 5 (13) |
| 2440 | Vaillant | near | GreeDevice/YAW1F-wifi | C | 196 | 196 | 0 | 1 | 0 | byte 5 bit 7 (195), swing_v (15), fan (6) |
| 2460 | FanWorld | covered | ElectraAcDevice/aux | C | 273 | 270 | 249 | 21 | 0 |  |
| 2480 | Rotenso | covered | CoolixDevice | C | 281 | 281 | 197 | 84 | 0 |  |
| 2500 | Endesa | covered | KelonDevice/dry-grade | C | 361 | 361 | 256 | 105 | 0 |  |
| 2520 | Galanz | unknown |  |  | 257 | 0 | 0 | 0 | 0 |  |
| 2540 | Audinac | near | MirageDevice/KKG29AC1 | C | 301 | 301 | 0 | 301 | 0 |  |
| 2560 | Mistral | near | Trotec3550Device | C | 271 | 268 | 65 | 173 | 0 | temp_f (30) |
| 2580 | KOREL | near | ElectraAcDevice/aux | C | 793 | 791 | 625 | 165 | 33 | byte 2 bit 4 (1), mode (1), sensor_update (1), byte 9 bit 3 (1), fan (1), power (1), half_degree (1), swing_h (1) |
| 2600 | Equation | unknown |  |  | 301 | 0 | 0 | 0 | 0 |  |
| 2620 | Komeco | covered | CoolixDevice | C | 281 | 281 | 197 | 84 | 0 |  |
| 2640 | Fisher | unknown |  |  | 169 | 0 | 0 | 0 | 0 |  |
| 2641 | Fisher | covered | CoolixDevice | C | 281 | 278 | 194 | 84 | 0 |  |
| 2660 | Hyundai | unknown |  |  | 269 | 0 | 0 | 0 | 0 |  |
| 2661 | Hyundai | unknown |  |  | 482 | 0 | 0 | 0 | 0 |  |
| 2662 | Hyndai | covered | ElectraAcDevice/aux | C | 341 | 341 | 273 | 68 | 0 |  |
| 2700 | Kolin | unknown |  |  | 64 | 0 | 0 | 0 | 0 |  |
| 2720 | AEG | near | ElectraAcDevice | C | 273 | 235 | 74 | 110 | 1 | temperature (51), fan (34) |
| 2740 | Bosch | near | Bosch144Device | C | 376 | 360 | 188 | 52 | 0 | temp_s1 (120), fan_s1 (60), mode_s1 (60) |
| 2760 | Tristar | near | GoodweatherDevice | C | 137 | 132 | 5 | 17 | 0 | command (109), temperature (39), byte 8 bit 4 (5) |
| 2780 | Xiaomi | unknown |  |  | 993 | 0 | 0 | 0 | 0 |  |
| 2800 | ELGIN | covered | ElectraAcDevice/aux | C | 35 | 35 | 18 | 17 | 0 |  |
| 2801 | ELGIN | covered | CoolixDevice | C | 29 | 29 | 15 | 14 | 0 |  |
| 2820 | Pearl | unknown |  |  | 181 | 0 | 0 | 0 | 0 |  |
| 2840 | HTW | covered | CoolixDevice | C | 281 | 256 | 174 | 82 | 0 |  |
| 2860 | Senville | covered | MideaDevice/RG57 | C | 211 | 208 | 207 | 1 | 0 |  |
| 2880 | Bora | near | Tcl112AcDevice/GZ055BE1-R | C | 312 | 288 | 0 | 14 | 0 | on_timer (274), byte 4 bit 6 (274), off_timer (274), byte 4 bit 2 (194), byte 4 bit 4 (194), byte 4 bit 1 (194), temperature (179), byte 9 bit 0 (143), byte 12 bit 4 (143), byte 10 bit 0 (131), byte 12 bit 0 (90), byte 12 bit 1 (77), swing_h (39), fan (12), byte 12 bit 2 (12) |
| 2900 | Goodman | covered | MideaDevice/RG57 | C | 169 | 166 | 165 | 1 | 0 |  |
| 2920 | Best | covered | Tcl112AcDevice/TAC09CHSD-RH | C | 241 | 241 | 78 | 163 | 0 |  |
| 2940 | SAGA | near | GoodweatherDevice | C | 545 | 544 | 0 | 1 | 0 | command (543), air_flow (271), byte 8 bit 4 (32), temperature (32), swing_v (14) |
| 2960 | EcoAir | covered | MideaDevice/RG57-F | C | 281 | 280 | 279 | 1 | 0 |  |
| 2980 | Agratto | near | Tcl112AcDevice/TAC09CHSD-RH | C | 94 | 84 | 55 | 1 | 0 | model (27), frames (1) |
| 3000 | Philco | near | MirageDevice/KKG29AC1 | C | 273 | 273 | 0 | 272 | 0 | mode (1), pad5 (1) |
| 3020 | Klasse | near | Tcl112AcDevice/TAC09CHSD-R | C | 241 | 239 | 0 | 18 | 0 | byte 3 bit 4 (221), byte 17 bit 4 (221), light (221), temperature (135), fan (109) |
| 3040 | Viessmann | covered | GreeDevice/YAW1F-wifi | C | 241 | 238 | 237 | 1 | 0 |  |
| 3060 | HappyTree | covered | Tcl112AcDevice/TAC09CHSD-X80 | C | 241 | 241 | 119 | 122 | 0 |  |
| 3080 | Voltas | near | VoltasDevice/122LZF | C | 722 | 683 | 0 | 11 | 0 | wifi (655), temperature (430), fan (214), swing_v (137), swing_h_change (125), mode (34), on_timer_mins (34), off_timer_mins (34), byte 6 bit 3 (34), byte 2 bit 4 (34), on_timer_hrs (34), byte 6 bit 6 (34), byte 6 bit 0 (34), off_timer_hrs (34), byte 6 bit 2 (34), byte 3 bit 5 (34), byte 4 bit 6 (34), power (34), byte 5 bit 6 (34), swing_h (30), byte 8 bit 0 (18), byte 1 bit 4 (4), byte 3 bit 4 (2) |
| 3100 | Cecotec | covered | Tcl112AcDevice/TAC09CHSD-X83 | C | 321 | 314 | 125 | 189 | 0 |  |
| 3120 | Cooper & Hunter | near | GreeDevice/YAW1F-wifi | C | 601 | 584 | 577 | 5 | 0 | frames (2) |
| 3140 | Argo | near | ArgoDevice/WREM2 | C | 181 | 171 | 0 | 1 | 0 | byte 7 bit 1 (170), byte 7 bit 7 (170), byte 8 bit 3 (170), byte 7 bit 0 (170), byte 5 bit 5 (170), byte 5 bit 6 (170), byte 7 bit 2 (170), byte 5 bit 7 (170), byte 7 bit 3 (137), byte 8 bit 0 (120), byte 8 bit 4 (110), room_temp (110), byte 7 bit 5 (110), byte 7 bit 4 (94), temperature (60), byte 8 bit 2 (60), byte 7 bit 6 (60), byte 8 bit 1 (60), ifeel (60), fan (45) |
| 3160 | AquaThermal | near | AirtonDevice | C | 321 | 321 | 0 | 1 | 0 | byte 4 bit 4 (320), fan (64), turbo (48) |
| 3180 | Devanti | covered | Tcl112AcDevice/TAC09CHSD-R | C | 257 | 251 | 159 | 92 | 0 |  |
| 3200 | Friedrich | near | Lg2Device/AKB74955603 | F | 325 | 325 | 136 | 45 | 0 | power (108), temperature (36), frames (36) |
| 3220 | Mundoclima | covered | ElectraAcDevice/aux | C | 341 | 341 | 68 | 273 | 0 |  |
| 3240 | Casper | covered | ElectraAcDevice | C | 749 | 712 | 577 | 135 | 0 |  |
| 3300 | PARKAIR | covered | ElectraAcDevice/aux | C | 121 | 120 | 105 | 15 | 0 |  |
| 3320 | Chunlan | unknown |  |  | 256 | 0 | 0 | 0 | 0 |  |
| 3340 | Wide | near | MirageDevice/KKG29AC1 | C | 273 | 268 | 0 | 267 | 0 | pad5 (1) |
| 3360 | Kaden | covered | CoolixDevice | C | 281 | 278 | 167 | 111 | 0 |  |
| 3380 | Zephir | covered | ElectraAcDevice/aux | C | 141 | 139 | 106 | 33 | 0 |  |
| 4060 | LG | unsupported |  |  | 0 | 0 | 0 | 0 | 157 (!) |  |
| 4100 | Daikin | covered | Daikin216Device | C | 157 | 154 | 152 | 2 | 0 |  |
| 4124 | Mitsubishi Electric | near | MitsubishiAcDevice/remote | C | 130 | 130 | 0 | 1 | 40 (!) | byte 32 bit 7 (129), byte 14 bit 7 (129), swing_v (39), temperature (15) |
| 4129 | Mitsubishi Electric | unsupported |  |  | 0 | 0 | 0 | 0 | 170 (!) |  |
| 4180 | Gree | near | GreeDevice/YX1FSF | C | 301 | 301 | 195 | 46 | 0 | model_a (45), byte 5 bit 5 (15), wifi (15), temp (1) |
| 4181 | Gree | unsupported |  |  | 0 | 0 | 0 | 0 | 301 (!) |  |
| 4285 | Fujitsu | unsupported |  |  | 0 | 0 | 0 | 0 | 376 (!) |  |
| 4380 | Midea | covered | CoolixDevice | C | 281 | 281 | 197 | 84 | 0 |  |
| 4381 | Midea | unsupported |  |  | 0 | 0 | 0 | 0 | 58 (!) |  |
| 4580 | Chigo | unsupported |  |  | 0 | 0 | 0 | 0 | 118 (!) |  |
| 4581 | Chigo | unsupported |  |  | 0 | 0 | 0 | 0 | 157 (!) |  |
| 4800 | TechnoLux | unsupported |  |  | 0 | 0 | 0 | 0 | 241 (!) |  |
| 5120 | Daikin | near | Daikin216Device | C | 703 | 693 | 556 | 106 | 0 | byte 14 bit 0 (30), fan (5), temperature (2), byte 14 bit 7 (1) |
| 5140 | Mitsubishi Electric | near | Mitsubishi112Device | C | 1345 | 1317 | 0 | 1 | 0 | swing_h (1316), temperature (428), swing_v (188), fan (1) |
| 5520 | Hisense | covered | KelonDevice/dry-grade | C | 241 | 241 | 63 | 178 | 0 |  |
| 7062 | LG | covered | LgAcDevice/GE6711AR2853M | C | 105 | 103 | 55 | 48 | 0 |  |
| 7065 | LG | near | Lg2Device/AKB74955603 | C | 181 | 178 | 1 | 177 | 0 |  |
| 7124 | Mitsubishi | unknown |  |  | 481 | 0 | 0 | 0 | 0 |  |
| 7260 | Toshiba | near | ToshibaAcDevice | C | 449 | 449 | 55 | 338 | 112 (!) | frames (56) |
| 7285 | Fujitsu | unknown |  |  | 376 | 0 | 0 | 0 | 0 |  |
| 7300 | SHARP | near | SharpAcDevice/A903 | C | 179 | 179 | 0 | 0 | 1 | byte 11 bit 1 (179), temp_flags (59), temperature (56), fan (45), mode (1) |
| 7386 | Midea | near | Bosch144Device | C | 351 | 351 | 197 | 70 | 0 | fan_s1 (84) |
| 7740 | Kelvinator | unknown |  |  | 351 | 0 | 0 | 0 | 0 |  |
| 7741 | Family | unknown |  |  | 401 | 0 | 0 | 0 | 0 |  |
| 8700 | Kolin | near | GreeDevice/YAW1F-wifi | C | 256 | 256 | 0 | 1 | 0 | byte 7 bit 0 (255), swing_auto (60), swing_h (60), swing_v (60), temp (1) |
| 8720 | Viomi | unknown |  |  | 161 | 0 | 0 | 0 | 0 |  |
| 8800 | Sigma | covered | GreeDevice/YAW1F | C | 242 | 241 | 240 | 1 | 0 |  |

## Clusters of unknown files

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

### 2 files, 883 codes, 690 keys

files: 2661, 7741

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(487, 305, 335), header=(3045, 1584), footer=(487,), gap=70195),
        "s1": Section(PulseDistance(487, 305, 335), header=(3045, 1584), footer=(487,), gap=101502),
    },
)
```

### 2 files, 702 codes, 376 keys

files: 1284, 1285

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(396, 426, 457), header=(3228, 1644), footer=(396,), gap=101502),
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

### 2 files, 284 codes, 242 keys

files: 1162, 2160

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 548, 1644), header=(4324, 4385), footer=(518,), gap=7461),
        "s1": Section(PulseDistance(518, 548, 1644), header=(4324, 4385), footer=(518,), gap=101502),
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

### 1 files, 375 codes, 375 keys

files: 1282

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 365, 1157), header=(3350, 1553), footer=(457,), gap=101502),
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

files: 1602

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 518, 1188), header=(3380, 1644), footer=(548,), gap=101502),
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

files: 1104

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 396, 457), header=(305, 396), footer=(457,), gap=25337),
        "s1": Section(PulseDistance(457, 396, 457), header=(3472, 1705), footer=(457,), gap=34778),
        "s2": Section(PulseDistance(457, 396, 457), header=(3472, 1705), footer=(457,), gap=34778),
        "s3": Section(PulseDistance(457, 396, 457), header=(3472, 1705), footer=(457,), gap=101502),
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

### 1 files, 225 codes, 225 keys

files: 2320

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(579, 518, 1614), header=(4385, 4416), footer=(579,), gap=5208),
        "s1": Section(PulseDistance(579, 518, 1614), header=(4385, 4416), footer=(579,), gap=101502),
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

files: 2321

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 640, 1766), header=(8953, 4598), footer=(548,), gap=101502),
    },
)
```

### 1 files, 203 codes, 203 keys

files: 1942

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(518, 670, 1766), header=(9014, 4598), footer=(609,), gap=101502),
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

### 1 files, 129 codes, 129 keys

files: 1860

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(457, 548, 1218), header=(3624, 1614), footer=(487,), gap=101502),
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

files: 1521

```
Protocol(
    "draft",
    {
        "s0": Section(PulseDistance(609, 518, 579), header=(8496, 4340), footer=(518,), gap=101502),
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

## Conflicts

- SmartIR 1287: Fujitsu / AR-REB1E: name taken by FujitsuAcDevice/ARREB1E
- SmartIR 1293: Fujitsu / AR-REB1E: name taken by FujitsuAcDevice/ARREB1E
- SmartIR 1540: Whirlpool / SPIS412L: name taken by WhirlpoolAcDevice/DG11J13A

## Rows: 10 proposed (rows.py)

