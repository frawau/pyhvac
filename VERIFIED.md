# Verified units

pyhvac generates each model's codes from its remote's protocol; most
models are listed because their remote's codes match, not because someone
saw the unit follow. A ✅ means someone sent pyhvac's codes to that unit
and it worked.

**Help by verifying yours.** If pyhvac (through hvactest, IR HVAC or your
own code) drives your unit, open a pull request that puts ✅ in its row's
Verified column and says in Notes what you checked and with which pyhvac
version, for example: "modes, 18-30 °C, fan, swing, off/on; 0.2.0". Check
at least every mode, a few setpoints, the fan speeds and off/on, and say
in Notes anything that did not work. If your unit is not
listed, see [Getting a unit supported](README.md#getting-a-unit-supported).

Rows are kept by `python tools/verified.py`, which adds a row for each new
model and keeps the ticks.

| Brand | Model | Kind | Protocol | Verified | Notes |
|---|---|---|---|:---:|---|
| AEG | Chillflex Pro AXP26U338CW | unit | ElectraAc |  |  |
| AEG | Chillflex Pro AXP26U558HW | unit | ElectraAc |  |  |
| AEG | Chillflex Pro AXP34U338CW | unit | ElectraAc |  |  |
| Airspool | AIRSPOOL protocol | remote | Airspool |  |  |
| Airspool | Mini-split | unit | Airspool |  |  |
| Airton | AIRTON protocol | remote | Airton |  |  |
| Airton | RD1A1 | remote | Airton |  |  |
| Airton | SMVH09B-2A2A3NH | unit | Airton |  |  |
| Airwell | AIRWELL protocol | remote | Airwell |  |  |
| Airwell | DC Series | unit | Airwell |  |  |
| Airwell | RC04 | remote | Airwell |  |  |
| Airwell | RC08B | remote | Coolix |  |  |
| Airwell | RC08W | remote | Airwell |  |  |
| Alaska | SAC9010QC | unit | TechnibelAc |  |  |
| Amana | PBC093G00CC | unit | Gree (YAW1F) |  |  |
| Amana | YX1FF | remote | Gree (YAW1F) |  |  |
| Amcor | ADR-853H | unit | Amcor |  |  |
| Amcor | AMCOR protocol | remote | Amcor |  |  |
| Amcor | TAC-444 | remote | Amcor |  |  |
| Amcor | TAC-495 | remote | Amcor |  |  |
| Argo | ARGO SAC_WREM2 protocol | remote | Argo (WREM2) |  |  |
| Argo | ARGO SAC_WREM3 protocol | remote | Argo (WREM3) |  |  |
| Argo | Ulisse 13 DCI | unit | Argo (WREM2) |  |  |
| Argo | Ulisse Eco | unit | Argo (WREM3) |  |  |
| Argo | WREM2 | remote | Argo (WREM2) |  |  |
| Argo | WREM3 | remote | Argo (WREM3) |  |  |
| AUX | KFR-35GW/BpNFW=3 | unit | ElectraAc |  |  |
| AUX | YKR-T/011 | remote | ElectraAc |  |  |
| Beko | BINR 070/071 | unit | Coolix |  |  |
| Beko | RG57K7(B)/BGEF | remote | Coolix |  |  |
| Bosch | B1ZAI2441W | unit | Coolix |  |  |
| Bosch | B1ZAO2441W | unit | Coolix |  |  |
| Bosch | BOSCH144 protocol | remote | Bosch144 |  |  |
| Bosch | CL3000i-Set 26 E | unit | Bosch144 |  |  |
| Bosch | RG10A(G2S)BGEF | remote | Bosch144 |  |  |
| Bosch | RG36B4/BGE | remote | Coolix |  |  |
| Carrier | 42NQV025M2 / 38NYV025M2 | unit | ToshibaAc |  |  |
| Carrier | 42NQV035M2 / 38NYV035M2 | unit | ToshibaAc |  |  |
| Carrier | 42NQV050M2 / 38NYV050M2 | unit | ToshibaAc |  |  |
| Carrier | 42NQV060M2 / 38NYV060M2 | unit | ToshibaAc |  |  |
| Carrier | 42QG5A55970 | remote | CarrierAc64 |  |  |
| Carrier | 53NGK009/012 | unit | CarrierAc64 |  |  |
| Carrier | 619EGX0090E0 | unit | CarrierAc64 |  |  |
| Carrier | 619EGX0120E0 | unit | CarrierAc64 |  |  |
| Carrier | 619EGX0180E0 | unit | CarrierAc64 |  |  |
| Carrier | 619EGX0220E0 | unit | CarrierAc64 |  |  |
| Carrier | CARRIER_AC64 protocol | remote | CarrierAc64 |  |  |
| Centek | SCT-65Q09 | unit | ElectraAc |  |  |
| Centek | YKR-P/002E | remote | ElectraAc |  |  |
| Comfee | MPD1-12CRN7 | unit | Midea |  |  |
| Cooper & Hunter | CH-S09FTXG | unit | Gree (YAW1F) |  |  |
| Cooper & Hunter | YB1F2 | remote | Gree (YAW1F) |  |  |
| Corona | AR-01 | remote | CoronaAc |  |  |
| Corona | CORONA_AC protocol | remote | CoronaAc |  |  |
| Corona | CSH-N2211 | unit | CoronaAc |  |  |
| Corona | CSH-N2511 | unit | CoronaAc |  |  |
| Corona | CSH-N2811 | unit | CoronaAc |  |  |
| Corona | CSH-N4011 | unit | CoronaAc |  |  |
| Daewoo | DSB-F0934ELH-V | unit | Tcl112Ac (GZ055BE1) |  |  |
| Daewoo | GYKQ-52E | remote | Tcl112Ac (GZ055BE1) |  |  |
| Daichi | D-H | unit | Haier176 (A) |  |  |
| Daikin | 17 Series FTXB09AXVJU | unit | Daikin128 |  |  |
| Daikin | 17 Series FTXB12AXVJU | unit | Daikin128 |  |  |
| Daikin | 17 Series FTXB24AXVJU | unit | Daikin128 |  |  |
| Daikin | ARC423A5 | remote | Daikin160 |  |  |
| Daikin | ARC433** | remote | DaikinArc |  |  |
| Daikin | ARC433B69 | remote | Daikin216 |  |  |
| Daikin | ARC466A12 | remote | DaikinArc |  |  |
| Daikin | ARC466A33 | remote | DaikinArc |  |  |
| Daikin | ARC466A67 | remote | Daikin312 |  |  |
| Daikin | ARC477A1 | remote | Daikin2 |  |  |
| Daikin | ARC480A5 | remote | Daikin152 |  |  |
| Daikin | ARC484A4 | remote | Daikin216 |  |  |
| Daikin | BRC4C151 | remote | Daikin176 |  |  |
| Daikin | BRC4C153 | remote | Daikin176 |  |  |
| Daikin | BRC52B63 | remote | Daikin128 |  |  |
| Daikin | DAIKIN protocol | remote | DaikinArc |  |  |
| Daikin | DAIKIN128 protocol | remote | Daikin128 |  |  |
| Daikin | DAIKIN152 protocol | remote | Daikin152 |  |  |
| Daikin | DAIKIN160 protocol | remote | Daikin160 |  |  |
| Daikin | DAIKIN176 protocol | remote | Daikin176 |  |  |
| Daikin | DAIKIN2 protocol | remote | Daikin2 |  |  |
| Daikin | DAIKIN216 protocol | remote | Daikin216 |  |  |
| Daikin | DAIKIN312 protocol | remote | Daikin312 |  |  |
| Daikin | DAIKIN64 protocol | remote | Daikin64 |  |  |
| Daikin | DAIKIN_NATIVE protocol | remote | DaikinNative |  |  |
| Daikin | DGS01 | remote | Daikin64 |  |  |
| Daikin | FFN-C/FCN-F Series | unit | Daikin64 |  |  |
| Daikin | FFQ35B8V1B | unit | Daikin176 |  |  |
| Daikin | FTE12HV2S | unit | Daikin160 |  |  |
| Daikin | FTQ60TV16U2 | unit | Daikin216 |  |  |
| Daikin | FTWX35AXV1 | unit | Daikin64 |  |  |
| Daikin | FTXM-M | unit | DaikinArc |  |  |
| Daikin | FTXM20R5V1B | unit | Daikin312 |  |  |
| Daikin | FTXZ25NV1B | unit | Daikin2 |  |  |
| Daikin | FTXZ35NV1B | unit | Daikin2 |  |  |
| Daikin | FTXZ50NV1B | unit | Daikin2 |  |  |
| Daikin | M Series | unit | DaikinArc |  |  |
| Daikin | Smash II | unit | DaikinNative | ✅ | the maintainer's unit |
| Danby | DAC080BGUWDB | unit | Midea |  |  |
| Danby | DAC100BGUWDB | unit | Midea |  |  |
| Danby | DAC120BGUWDB | unit | Midea |  |  |
| Danby | R09C/BCGE | remote | Midea |  |  |
| De'Longhi | DELONGHI_AC protocol | remote | DelonghiAc |  |  |
| De'Longhi | PAC A95 | unit | DelonghiAc |  |  |
| De'Longhi | PAC EM90 | unit | ElectraAc |  |  |
| Duux | Blizzard Smart 10K / DXMA04 | unit | Trotec |  |  |
| EcoClim | ECOCLIM protocol | remote | Ecoclim |  |  |
| EcoClim | HYSFR-P348 | remote | Ecoclim |  |  |
| EcoClim | ZC200DPO | unit | Ecoclim |  |  |
| EKOKAI | GREE YAW1F protocol | remote | Gree (YAW1F) |  |  |
| Electra | AXW12DCS | unit | ElectraAc |  |  |
| Electra | Classic INV 17 | unit | ElectraAc |  |  |
| Electra | ELECTRA_AC protocol | remote | ElectraAc |  |  |
| Electra | YKR-M/003E | remote | ElectraAc |  |  |
| Electrolux | YKR-H/531E | unit | ElectraAc |  |  |
| Eurom | EUROM protocol | remote | Eurom |  |  |
| Eurom | Polar 16CH | unit | Eurom |  |  |
| Frigidaire | FGPC102AB1 | unit | ElectraAc |  |  |
| Fujitsu | AGTV14LAC | unit | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | AR-DB1 | remote | FujitsuAc (ARDB1) |  |  |
| Fujitsu | AR-DL10 | remote | FujitsuAc (ARDB1) |  |  |
| Fujitsu | AR-RAC1E | remote | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | AR-RAE1E | remote | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | AR-RAH1U | remote | FujitsuAc (ARREB1E) |  |  |
| Fujitsu | AR-RAH2E | remote | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | AR-RAH2U | remote | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | AR-REB1E | remote | FujitsuAc (ARREB1E) |  |  |
| Fujitsu | AR-REB4E | remote | FujitsuAc (ARREB1E) |  |  |
| Fujitsu | AR-REG1U | remote | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | AR-REW1E | remote | FujitsuAc (ARREW4E) |  |  |
| Fujitsu | AR-REW4E | remote | FujitsuAc (ARREW4E) |  |  |
| Fujitsu | AR-RY4 | remote | FujitsuAc (ARRY4) |  |  |
| Fujitsu | AST9RSGCW | unit | FujitsuAc (ARDB1) |  |  |
| Fujitsu | ASTB09LBC | unit | FujitsuAc (ARRY4) |  |  |
| Fujitsu | ASTG09K | unit | FujitsuAc (ARREW4E) |  |  |
| Fujitsu | ASTG18K | unit | FujitsuAc (ARREW4E) |  |  |
| Fujitsu | ASU12RLF | unit | FujitsuAc (ARREB1E) |  |  |
| Fujitsu | ASU30C1 | unit | FujitsuAc (ARDB1) |  |  |
| Fujitsu | ASYG09KETA-B | unit | FujitsuAc (ARREW4E) |  |  |
| Fujitsu | ASYG30LFCA | unit | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | ASYG7LMCA | unit | FujitsuAc (ARREB1E) |  |  |
| Fujitsu | FUJITSU_AC ARDB1 protocol | remote | FujitsuAc (ARDB1) |  |  |
| Fujitsu | FUJITSU_AC ARJW2 protocol | remote | FujitsuAc (ARJW2) |  |  |
| Fujitsu | FUJITSU_AC ARRAH2E protocol | remote | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | FUJITSU_AC ARREB1E protocol | remote | FujitsuAc (ARREB1E) |  |  |
| Fujitsu | FUJITSU_AC ARREW4E protocol | remote | FujitsuAc (ARREW4E) |  |  |
| Fujitsu | FUJITSU_AC ARRY4 protocol | remote | FujitsuAc (ARRY4) |  |  |
| Fujitsu | AOHG09LLC | unit | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | AR-JW17 | remote | FujitsuAc (ARDB1) |  |  |
| Fujitsu | AR-JW2 | remote | FujitsuAc (ARJW2) |  |  |
| Fujitsu | AR-RCE1E | remote | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | ASHG09LLCA | unit | FujitsuAc (ARRAH2E) |  |  |
| GE | 6711AR2853M | remote | LgAc (GE6711AR2853M) |  |  |
| GE | AG1BH09AW101 | unit | LgAc (GE6711AR2853M) |  |  |
| Goodweather | GOODWEATHER protocol | remote | Goodweather |  |  |
| Goodweather | ZH/JT-03 | remote | Goodweather |  |  |
| Gree | GREE YAW1F protocol | remote | Gree (YAW1F) |  |  |
| Gree | VIR09HP115V1AH | unit | Gree (YAW1F) |  |  |
| Gree | VIR12HP230V1AH | unit | Gree (YAW1F) |  |  |
| Gree | YAA1FBF | remote | Gree (YAW1F) |  |  |
| Gree | YAN1F1 | remote | Gree (YAW1F) |  |  |
| Gree | YAP0F8 | remote | Kelvinator |  |  |
| Gree | YAPOF3 | remote | Kelvinator |  |  |
| Gree | YB1F2F | remote | Gree (YAW1F) |  |  |
| Gree | YX1F2F | remote | Gree (YX1FSF) |  |  |
| Green | YBOFB | remote | Gree (YBOFB) |  |  |
| Green | YBOFB2 | remote | Gree (YBOFB) |  |  |
| Haier | HAIER_AC protocol | remote | HaierAc |  |  |
| Haier | HAIER_AC160 protocol | remote | Haier160 |  |  |
| Haier | HAIER_AC176 V9014557_A protocol | remote | Haier176 (A) |  |  |
| Haier | HAIER_AC176 V9014557_B protocol | remote | Haier176 (B) |  |  |
| Haier | HAIER_AC_YRW02 V9014557_A protocol | remote | HaierYrw02 (A) |  |  |
| Haier | HAIER_AC_YRW02 V9014557_B protocol | remote | HaierYrw02 (B) |  |  |
| Haier | HSU-09HMC203 | unit | HaierYrw02 (A) |  |  |
| Haier | HSU07-HEA03 | remote | HaierAc |  |  |
| Haier | KFR-26GW/83@UI-Ge | unit | Haier160 |  |  |
| Haier | V9014557 M47 8D | remote | Haier176 (A) |  |  |
| Haier | YR-W02 | remote | HaierYrw02 (A) |  |  |
| Hitachi | HITACHI_AC protocol | remote | HitachiAc |  |  |
| Hitachi | HITACHI_AC1 R_LT0541_HTA_A protocol | remote | Hitachi1 (A) |  |  |
| Hitachi | HITACHI_AC1 R_LT0541_HTA_B protocol | remote | Hitachi1 (B) |  |  |
| Hitachi | HITACHI_AC264 protocol | remote | Hitachi264 |  |  |
| Hitachi | HITACHI_AC296 protocol | remote | Hitachi296 |  |  |
| Hitachi | HITACHI_AC344 protocol | remote | Hitachi344 |  |  |
| Hitachi | HITACHI_AC424 protocol | remote | Hitachi424 |  |  |
| Hitachi | KAZE-312KSDP | unit | Hitachi1 (A) |  |  |
| Hitachi | LT0541-HTA | remote | Hitachi1 (A) |  |  |
| Hitachi | R-LT0541-HTA/Y.K.1.1-1 V2.3 | remote | Hitachi1 (A) |  |  |
| Hitachi | RAK-25NH5 | unit | Hitachi264 |  |  |
| Hitachi | RAR-2P2 | remote | Hitachi264 |  |  |
| Hitachi | RAR-3U3 | remote | Hitachi296 |  |  |
| Hitachi | RAR-8P2 | remote | Hitachi424 |  |  |
| Hitachi | RAS-22NK | unit | Hitachi344 |  |  |
| Hitachi | RAS-35THA6 | remote | HitachiAc |  |  |
| Hitachi | RAS-70YHA3 | unit | Hitachi296 |  |  |
| Hitachi | RAS-AJ25H | unit | Hitachi424 |  |  |
| Hitachi | RF11T1 | remote | Hitachi344 |  |  |
| Hitachi | Series VI | unit | Hitachi1 (A) |  |  |
| Kastron | RG57A7/BGEF | remote | Coolix |  |  |
| Kaysun | Casual CF | unit | Midea |  |  |
| Kaysun | Casual CF (COOLIX) | unit | Coolix |  |  |
| Kelon | ON/OFF 9000-12000 | unit | Kelon |  |  |
| Kelvinator | KELVINATOR protocol | remote | Kelvinator |  |  |
| Kelvinator | KSV26CRC | unit | Kelvinator |  |  |
| Kelvinator | KSV26HRC | unit | Kelvinator |  |  |
| Kelvinator | KSV35CRC | unit | Kelvinator |  |  |
| Kelvinator | KSV35HRC | unit | Kelvinator |  |  |
| Kelvinator | KSV53HRC | unit | Kelvinator |  |  |
| Kelvinator | KSV62HRC | unit | Kelvinator |  |  |
| Kelvinator | KSV70CRC | unit | Kelvinator |  |  |
| Kelvinator | KSV70HRC | unit | Kelvinator |  |  |
| Kelvinator | KSV80HRC | unit | Kelvinator |  |  |
| Kelvinator | YALIF | remote | Kelvinator |  |  |
| Keystone | RG57H4(B)BGEF | remote | Midea |  |  |
| Leberg | LBS-TOR07 | unit | Tcl112Ac (TAC09CHSD) |  |  |
| Lennox | M22A | unit | Midea |  |  |
| Lennox | M33A | unit | Midea |  |  |
| Lennox | M33B | unit | Midea |  |  |
| Lennox | MCFA | unit | Midea |  |  |
| Lennox | MCFB | unit | Midea |  |  |
| Lennox | MMDA | unit | Midea |  |  |
| Lennox | MMDB | unit | Midea |  |  |
| Lennox | MWMA | unit | Midea |  |  |
| Lennox | MWMA009S4-3P | unit | Midea |  |  |
| Lennox | MWMA012S4-3P | unit | Midea |  |  |
| Lennox | MWMB | unit | Midea |  |  |
| Lennox | RG57A6/BGEFU1 | remote | Midea |  |  |
| LG | 6711A20083V | remote | LgAc (LG6711A20083V) |  |  |
| LG | A4UW30GFA2 | unit | Lg2 (AKB74955603) |  |  |
| LG | AKB73315611 | remote | Lg2 (AKB74955603) |  |  |
| LG | AKB73757604 | remote | Lg2 (AKB73757604) |  |  |
| LG | AKB74395308 | remote | Lg2 (AKB75215403) |  |  |
| LG | AKB74955603 | remote | Lg2 (AKB74955603) |  |  |
| LG | AKB75215403 | remote | Lg2 (AKB75215403) |  |  |
| LG | AMNW09GSJA0 | unit | Lg2 (AKB74955603) |  |  |
| LG | AMNW24GTPA1 | unit | Lg2 (AKB73757604) |  |  |
| LG | Dual Inverter | unit | LgNative (dual inverter) |  |  |
| LG | Inverter V | unit | LgNative (inverter v) |  |  |
| LG | LG_NATIVE protocol | remote | LgNative (generic) |  |  |
| LG | MS05SQ NW0 | unit | Lg2 (AKB74955603) |  |  |
| LG | S4-W12JA3AA | unit | Lg2 (AKB75215403) |  |  |
| LG | TS-H122ERM1 | remote | LgAc (LG6711A20083V) |  |  |
| Mabe | MMI18HDBWCA6MI8 | unit | Haier176 (A) |  |  |
| Mabe | V12843 HJ200223 | remote | Haier176 (A) |  |  |
| Maxell | KKG9A-C1 | remote | Mirage (KKG9AC1) |  |  |
| Maxell | MX-CH18CF | unit | Mirage (KKG9AC1) |  |  |
| Midea | COOLIX protocol | remote | Coolix |  |  |
| Midea | MIDEA protocol | remote | Midea |  |  |
| Midea | MS12FU-10HRDN1-QRD0GW(B) | unit | Coolix |  |  |
| Midea | MSABAU-07HRFN1-QRD0GW | unit | Coolix |  |  |
| Midea | RG52D/BGE | remote | Coolix |  |  |
| Mirage | MIRAGE KKG29AC1 protocol | remote | Mirage (KKG29AC1) |  |  |
| Mirage | MIRAGE KKG9AC1 protocol | remote | Mirage (KKG9AC1) |  |  |
| Mirage | VLU series | unit | Mirage (KKG9AC1) |  |  |
| Mitsubishi Electric | 001CP T7WE10714 | remote | Mitsubishi136 |  |  |
| Mitsubishi Electric | KM14A 0179213 | remote | MitsubishiAc |  |  |
| Mitsubishi Electric | KPOA | remote | Mitsubishi112 |  |  |
| Mitsubishi Electric | MITSUBISHI112 protocol | remote | Mitsubishi112 |  |  |
| Mitsubishi Electric | MITSUBISHI112 I-feel remote | remote | Mitsubishi112 (i-feel) | ✅ | the maintainer's unit |
| Mitsubishi Electric | MITSUBISHI136 protocol | remote | Mitsubishi136 |  |  |
| Mitsubishi Electric | MITSUBISHI_AC protocol | remote | MitsubishiAc |  |  |
| Mitsubishi Electric | MLZ-RX5017AS | unit | MitsubishiAc |  |  |
| Mitsubishi Electric | MS-GK24VA | unit | MitsubishiAc |  |  |
| Mitsubishi Electric | MSH-A24WV | unit | Mitsubishi112 |  |  |
| Mitsubishi Electric | MSZ-FHnnVE | unit | MitsubishiAc |  |  |
| Mitsubishi Electric | MSZ-GV2519 | unit | MitsubishiAc |  |  |
| Mitsubishi Electric | MSZ-SF25VE3 | unit | MitsubishiAc |  |  |
| Mitsubishi Electric | MSZ-ZW4017S | unit | MitsubishiAc |  |  |
| Mitsubishi Electric | MUH-A24WV | unit | Mitsubishi112 |  |  |
| Mitsubishi Electric | PAR-FA32MA | remote | Mitsubishi136 |  |  |
| Mitsubishi Electric | PEAD-RP71JAA | unit | Mitsubishi136 |  |  |
| Mitsubishi Electric | RH151 | remote | MitsubishiAc |  |  |
| Mitsubishi Electric | RH151/M21ED6426 | remote | MitsubishiAc |  |  |
| Mitsubishi Electric | SG153/M21EDF426 | remote | MitsubishiAc |  |  |
| Mitsubishi Electric | SG15D | remote | MitsubishiAc |  |  |
| Mitsubishi Heavy Industries | MITSUBISHI_HEAVY_152 protocol | remote | MitsubishiHeavy152 |  |  |
| Mitsubishi Heavy Industries | MITSUBISHI_HEAVY_88 protocol | remote | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | RKX502A001C | remote | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | RLA502A700B | remote | MitsubishiHeavy152 |  |  |
| Mitsubishi Heavy Industries | SRKxxZJ-S | unit | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | SRKxxZM-S | unit | MitsubishiHeavy152 |  |  |
| Mitsubishi Heavy Industries | SRKxxZMXA-S | unit | MitsubishiHeavy152 |  |  |
| MRCOOL | RG57A6/BGEFU1 | remote | Midea |  |  |
| Neoclima | NEOCLIMA protocol | remote | Neoclima |  |  |
| Neoclima | NS-09AHTI | unit | Neoclima |  |  |
| Neoclima | ZH/TY-01 | remote | Neoclima |  |  |
| O General | AR-RCL1E | remote | FujitsuAc (ARRAH2E) |  |  |
| Panasonic | 4-Way Cassette | unit | PanasonicNative (4 way cassette) | ✅ | the maintainer's unit |
| Panasonic | A75C2295 | remote | PanasonicAc32 |  |  |
| Panasonic | A75C2311 | remote | PanasonicAc (CKP) |  |  |
| Panasonic | A75C2616-1 | remote | PanasonicAc (DKE) |  |  |
| Panasonic | A75C3704 | remote | PanasonicAc (DKE) |  |  |
| Panasonic | A75C3747 | remote | PanasonicAc (JKE) |  |  |
| Panasonic | A75C4762 | remote | PanasonicAc (RKR) |  |  |
| Panasonic | CKP series | unit | PanasonicAc (CKP) |  |  |
| Panasonic | CS-E12QKEW | unit | PanasonicAc (DKE) |  |  |
| Panasonic | CS-E7PKR | unit | PanasonicAc (DKE) |  |  |
| Panasonic | CS-E9CKP series | unit | PanasonicAc32 |  |  |
| Panasonic | CS-ME10CKPG | unit | PanasonicAc (CKP) |  |  |
| Panasonic | CS-ME12CKPG | unit | PanasonicAc (CKP) |  |  |
| Panasonic | CS-ME14CKPG | unit | PanasonicAc (CKP) |  |  |
| Panasonic | CS-YW9MKD | unit | PanasonicAc (JKE) |  |  |
| Panasonic | CS-Z24RKR | unit | PanasonicAc (RKR) |  |  |
| Panasonic | CS-Z9RKR | unit | PanasonicAc (RKR) |  |  |
| Panasonic | DKE series | unit | PanasonicAc (DKE) |  |  |
| Panasonic | DKW series | unit | PanasonicAc (DKE) |  |  |
| Panasonic | JKE series | unit | PanasonicAc (JKE) |  |  |
| Panasonic | NKE series | unit | PanasonicAc (NKE) |  |  |
| Panasonic | PANASONIC_AC32 protocol | remote | PanasonicAc32 |  |  |
| Panasonic | PANASONIC_NATIVE protocol | remote | PanasonicNative (generic) |  |  |
| Panasonic | PKR series | unit | PanasonicAc (DKE) |  |  |
| Panasonic | PN1122V | remote | PanasonicAc (DKE) |  |  |
| Panasonic | RKR series | unit | PanasonicAc (RKR) |  |  |
| Pioneer System | RG66B6(B)/BGEFU1 | remote | Midea |  |  |
| Pioneer System | RUBO18GMFILCAD | unit | Midea |  |  |
| Pioneer System | RYBO12GMFILCAD | unit | Midea |  |  |
| Pioneer System | UB018GMFILCFHD | unit | Midea |  |  |
| Pioneer System | WS012GMFI22HLD | unit | Midea |  |  |
| Pioneer System | WS018GMFI22HLD | unit | Midea |  |  |
| Rhoss | Idrowall MPCV 20-30-35-40 | unit | Rhoss |  |  |
| Rhoss | RHOSS protocol | remote | Rhoss |  |  |
| RusClimate | EACS/I-09HAR_X/N3 | unit | Gree (YAW1F) |  |  |
| RusClimate | YAW1F | remote | Gree (YAW1F) |  |  |
| Samsung | AR09FSSDAWKNFA | unit | SamsungAc |  |  |
| Samsung | AR09HSFSBWKN | unit | SamsungAc |  |  |
| Samsung | AR12HSSDBWKNEU | unit | SamsungAc |  |  |
| Samsung | AR12KSFPEWQNET | unit | SamsungAc |  |  |
| Samsung | AR12NXCXAWKXEU | unit | SamsungAc |  |  |
| Samsung | AR12TXEAAWKNEU | unit | SamsungAc |  |  |
| Samsung | DB93-14195A | remote | SamsungAc |  |  |
| Samsung | DB96-24901C | remote | SamsungAc |  |  |
| Samsung | SAMSUNG_AC protocol | remote | SamsungAc |  |  |
| Sanyo | RCS-2HS4E | remote | SanyoAc |  |  |
| Sanyo | RCS-2S4E | remote | SanyoAc |  |  |
| Sanyo | SANYO_AC protocol | remote | SanyoAc |  |  |
| Sanyo | SANYO_AC88 protocol | remote | SanyoAc88 |  |  |
| Sanyo | SAP-K121AHA | unit | SanyoAc |  |  |
| Sanyo | SAP-K242AH | unit | SanyoAc |  |  |
| Sharp | A5VEY | unit | Kelvinator |  |  |
| Sharp | AH-A12REVP-1 | unit | SharpAc (A903) |  |  |
| Sharp | AH-AxSAY | unit | SharpAc (A907) |  |  |
| Sharp | AH-PR13-GL | unit | SharpAc (A903) |  |  |
| Sharp | AH-XP10NRY | unit | SharpAc (A903) |  |  |
| Sharp | AY-ZP40KR | unit | SharpAc (A907) |  |  |
| Sharp | CRMC-820 JBEZ | remote | SharpAc (A903) |  |  |
| Sharp | CRMC-A705 JBEZ | remote | SharpAc (A705) |  |  |
| Sharp | CRMC-A863 JBEZ | remote | SharpAc (A903) |  |  |
| Sharp | CRMC-A903JBEZ | remote | SharpAc (A903) |  |  |
| Sharp | CRMC-A907 JBEZ | remote | SharpAc (A907) |  |  |
| Sharp | CRMC-A950 JBEZ | remote | SharpAc (A907) |  |  |
| Sharp | J-Tech | unit | JTech | ✅ | the maintainer's unit |
| Sharp | SHARP_AC A705 protocol | remote | SharpAc (A705) |  |  |
| Sharp | SHARP_AC A903 protocol | remote | SharpAc (A903) |  |  |
| Sharp | SHARP_AC A907 protocol | remote | SharpAc (A907) |  |  |
| Sharp | YB1FA | remote | Kelvinator |  |  |
| Soleus Air | TTWM1-10-01 | unit | Neoclima |  |  |
| Soleus Air | window | unit | Gree (YX1FSF) |  |  |
| Soleus Air | ZCF/TL-05 | remote | Neoclima |  |  |
| Subtropic | SUB-07HN1_18Y | unit | ElectraAc |  |  |
| Subtropic | YKR-H/102E | remote | ElectraAc |  |  |
| TCL | TAC-09CHSD/XA31I | unit | Tcl112Ac (TAC09CHSD) |  |  |
| TCL | TCL112AC GZ055BE1 protocol | remote | Tcl112Ac (GZ055BE1) |  |  |
| TCL | TCL112AC TAC09CHSD protocol | remote | Tcl112Ac (TAC09CHSD) |  |  |
| Technibel | IRO PLUS | unit | TechnibelAc |  |  |
| Technibel | TECHNIBEL_AC protocol | remote | TechnibelAc |  |  |
| Teco | TECHNIBEL_AC protocol | remote | TechnibelAc |  |  |
| Teknopoint | Allegro SSA-09H | unit | Tcl112Ac (GZ055BE1) |  |  |
| Teknopoint | GZ-055B-E1 | remote | Tcl112Ac (GZ055BE1) |  |  |
| Tokio | AATOEMF17-12CHR1SW | unit | Coolix |  |  |
| Tokio | RG51\|50/BGE | remote | Coolix |  |  |
| Toshiba | Akita EVO II | unit | ToshibaAc |  |  |
| Toshiba | RAS 18SKP-ES | unit | ToshibaAc |  |  |
| Toshiba | RAS-2558V | unit | ToshibaAc |  |  |
| Toshiba | RAS-25SKVP2-ND | unit | ToshibaAc |  |  |
| Toshiba | RAS-4M27YAV-E | unit | Coolix |  |  |
| Toshiba | RAS-B13N3KV2 | unit | ToshibaAc |  |  |
| Toshiba | RAS-B13N3KVP-E | unit | ToshibaAc |  |  |
| Toshiba | RAS-M10YKV-E | unit | Coolix |  |  |
| Toshiba | RAS-M13YKV-E | unit | Coolix |  |  |
| Toshiba | TOSHIBA_AC protocol | remote | ToshibaAc |  |  |
| Toshiba | WC-L03SE | remote | ToshibaAc |  |  |
| Toshiba | WH-E1YE | remote | Coolix |  |  |
| Toshiba | WH-TA01JE | remote | ToshibaAc |  |  |
| Toshiba | WH-TA04NE | remote | ToshibaAc |  |  |
| Toshiba | WH-UB03NJ | remote | ToshibaAc |  |  |
| Transcold | M1-F-NO-6 | unit | Transcold |  |  |
| Transcold | TRANSCOLD protocol | remote | Transcold |  |  |
| Tronitechnik | KKG29A-C1 | remote | Mirage (KKG29AC1) |  |  |
| Tronitechnik | Reykir 9000 | unit | Mirage (KKG29AC1) |  |  |
| Trotec | PAC 2100 X | unit | Midea |  |  |
| Trotec | PAC 3200 | unit | Trotec |  |  |
| Trotec | PAC 3550 Pro | unit | Trotec3550 |  |  |
| Trotec | PAC 3900 X | unit | Midea |  |  |
| Trotec | RG57H(B)/BGE | remote | Midea |  |  |
| Trotec | RG57H3(B)/BGCEF-M | remote | Midea |  |  |
| Trotec | TROTEC protocol | remote | Trotec |  |  |
| Trotec | TROTEC_3550 protocol | remote | Trotec3550 |  |  |
| Truma | 40091-86700 | remote | Truma |  |  |
| Truma | Aventa | unit | Truma |  |  |
| Truma | TRUMA protocol | remote | Truma |  |  |
| Ultimate | Heat Pump | unit | Gree (YAW1F) |  |  |
| Vaillant | VAI5-035WNI | unit | Gree (YAW1F) |  |  |
| Vaillant | YACIFB | remote | Gree (YAW1F) |  |  |
| Vestel | BIOX CXP-9 | unit | VestelAc |  |  |
| Vestel | VESTEL_AC protocol | remote | VestelAc |  |  |
| Voltas | 122LZF 4011252 | unit | Voltas (122LZF) |  |  |
| Voltas | VOLTAS kVoltas122LZF protocol | remote | Voltas (122LZF) |  |  |
| Voltas | VOLTAS kVoltasUnknown protocol | remote | Voltas (Unknown) |  |  |
| Whirlpool | DG11J1-04 | remote | WhirlpoolAc (DG11J13A) |  |  |
| Whirlpool | DG11J1-3A | remote | WhirlpoolAc (DG11J13A) |  |  |
| Whirlpool | DG11J1-91 | remote | WhirlpoolAc (DG11J191) |  |  |
| Whirlpool | SPIS409L | unit | WhirlpoolAc (DG11J13A) |  |  |
| Whirlpool | SPIS412L | unit | WhirlpoolAc (DG11J13A) |  |  |
| Whirlpool | SPIW409L | unit | WhirlpoolAc (DG11J13A) |  |  |
| Whirlpool | SPIW412L | unit | WhirlpoolAc (DG11J13A) |  |  |
| Whirlpool | SPIW418L | unit | WhirlpoolAc (DG11J13A) |  |  |
| Whirlpool | WHIRLPOOL_AC DG11J13A protocol | remote | WhirlpoolAc (DG11J13A) |  |  |
| Whirlpool | WHIRLPOOL_AC DG11J191 protocol | remote | WhirlpoolAc (DG11J191) |  |  |
| LG | W12TCM | unit | LgAc (GE6711AR2853M) |  |  |
| Actron | Actron | unit | Coolix |  |  |
| Electrolux | EACS/I-HAT/N3 | unit | Coolix |  |  |
| General Electric | ASHA09LCC | unit | FujitsuAc (ARRAH2E) |  |  |
| LG | R09AWN | unit | LgAc (GE6711AR2853M) |  |  |
| LG | R24AWN | unit | LgAc (GE6711AR2853M) |  |  |
| LG | E09EK | unit | LgAc (GE6711AR2853M) |  |  |
| LG | P12EP1 | unit | Lg2 (AKB74955603) |  |  |
| LG | LA090HYV | unit | Lg2 (AKB74955603) |  |  |
| LG | LA120HYV | unit | Lg2 (AKB74955603) |  |  |
| LG | LAN090HYV | unit | Lg2 (AKB74955603) |  |  |
| LG | LAN120HYV | unit | Lg2 (AKB74955603) |  |  |
| LG | AKB74295304 | unit | Lg2 (AKB74955603) |  |  |
| LG | PC09SQ NSJ | unit | Lg2 (AKB74955603) |  |  |
| Carrier | Carrier | unit | Coolix |  |  |
| Carrier | 42LUVH025N-1 | unit | Coolix |  |  |
| Fujitsu | AR-JE5 | unit | FujitsuAc (ARDB1) |  |  |
| Fujitsu | ASYG-LMCE | unit | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | AR-REM7E | unit | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | AR-REW2E | unit | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | ASYG07LM | unit | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | ASYG09LM | unit | FujitsuAc (ARRAH2E) |  |  |
| Springer | Split Hi Wall Maxiflex | unit | Coolix |  |  |
| Midea | MSY-12HRDN1 | unit | Coolix |  |  |
| Midea | KFR-35G | unit | Coolix |  |  |
| Midea | MSMACU-18HRFN1-QRD0GW | unit | Coolix |  |  |
| Midea | RG70E/BGEF | remote | Coolix |  |  |
| Midea | MAP05R1WWT | unit | Coolix |  |  |
| Midea | RG52C1/BGE | remote | Coolix |  |  |
| Midea | RG58E3/BGEF | unit | Coolix |  |  |
| Midea | RG70C/BGEF | remote | Coolix |  |  |
| Samsung | AR**TSHQBURN | unit | Coolix |  |  |
| Alliance | Alliance | unit | Coolix |  |  |
| Beko | BPEU 120 | unit | Coolix |  |  |
| Tornado | Super - Inverter A, i | unit | Coolix |  |  |
| Tornado | Inverter | unit | Coolix |  |  |
| Tornado | Inverter A | unit | Coolix |  |  |
| Tornado | Super Design | unit | Coolix |  |  |
| Tornado | Super Plasma | unit | Coolix |  |  |
| Tornado | Gold i | unit | Coolix |  |  |
| Tornado | Multi ON-OFF | unit | Coolix |  |  |
| Tornado | Multi Inverter | unit | Coolix |  |  |
| Tornado | Super Gold i | unit | Coolix |  |  |
| Tornado | Plasma Gold | unit | Coolix |  |  |
| Tornado | Super Legend 40 | unit | Kelon (16C) |  |  |
| Electrolux | EPI12LEIWI | unit | Coolix |  |  |
| Kelvinator | KSV25HRG | unit | Coolix (quiet) |  |  |
| Daitsu | DS12U-RV | unit | Coolix |  |  |
| Ballu | BSD/in-09HN1_20Y | unit | Coolix |  |  |
| Electra | Electra | unit | Coolix (16C) |  |  |
| Electra | Electra Platinum Plus Inverter | unit | Coolix |  |  |
| Ariston | A-IFWHxx-IGX | unit | Coolix |  |  |
| Lennox | LNMTE026V2 | unit | Coolix |  |  |
| Rotenso | Ukura | unit | Coolix |  |  |
| Rotenso | Maze | remote | Coolix |  |  |
| Komeco | Komeco | unit | Coolix |  |  |
| Fisher | FSOAI-SU-90AE2 | unit | Coolix |  |  |
| Kaden | KS09 | unit | Coolix |  |  |
| Kaden | KS12 | unit | Coolix |  |  |
| Kaden | KS18 | unit | Coolix |  |  |
| Kaden | KS24 | unit | Coolix |  |  |
| Kaden | KS28 | unit | Coolix |  |  |
| LG | P12RK | unit | LgAc (GE6711AR2853M) |  |  |
| Fujitsu | ASYG18LF | unit | FujitsuAc (ARRAH2E) |  |  |
| Fujitsu | AR-RY12 | unit | FujitsuAc (ARRAH2E) |  |  |
| Beko | BEVCA 120 | unit | ElectraAc (aux) |  |  |
| Electrolux | EXP26U758CW | unit | ElectraAc (aux) |  |  |
| Ballu | YKR-K/002E | unit | ElectraAc (aux) |  |  |
| AUX | AUX FREEDOM AUX-09FH | unit | ElectraAc (aux) |  |  |
| AUX | iClima ICI-09A | unit | ElectraAc (aux) |  |  |
| AUX | Kendal Split Inverter | unit | ElectraAc (aux) |  |  |
| Sendo | SND-18/IK | unit | ElectraAc (aux) |  |  |
| BAXI | BAXI | unit | ElectraAc (aux) |  |  |
| FanWorld | FW6-3000 | unit | ElectraAc (aux) |  |  |
| ELGIN | HVQI18B2IA | unit | ElectraAc (aux) |  |  |
| Mundoclima | MUPR-09-H9A | unit | ElectraAc (aux) |  |  |
| Mundoclima | MUPR-12-H9A | unit | ElectraAc (aux) |  |  |
| Mundoclima | MUPR-18-H9A | unit | ElectraAc (aux) |  |  |
| Mundoclima | MUPR-24-H9A | unit | ElectraAc (aux) |  |  |
| Mundoclima | MUPR-09-H5A | unit | ElectraAc (aux) |  |  |
| Mundoclima | MUPR-12-H5A | unit | ElectraAc (aux) |  |  |
| Mundoclima | MUPR-18-H5A | unit | ElectraAc (aux) |  |  |
| Mundoclima | MUPR-24-H5A | unit | ElectraAc (aux) |  |  |
| PARKAIR | DI-A | unit | ElectraAc (aux) |  |  |
| Zephir | DualSplit | unit | ElectraAc (aux) |  |  |
| Toyotomi | AKIRA GAN/GAG-A128 VL | unit | Gree (YX1FSF) |  |  |
| Panasonic | CS-CE7HKEW | unit | PanasonicAc (JKE-M13) |  |  |
| Panasonic | CS-CE9HKEW | unit | PanasonicAc (JKE-M13) |  |  |
| Panasonic | CS-CE12HKEW | unit | PanasonicAc (JKE-M13) |  |  |
| Panasonic | CS-PC24MKF | unit | PanasonicAc (JKE-M13) |  |  |
| Panasonic | CS-C24PKF | unit | PanasonicAc (JKE-M13) |  |  |
| Panasonic | CS-HE9JKE | unit | PanasonicAc (RKR-81) |  |  |
| Panasonic | CS-HE12JKE | unit | PanasonicAc (RKR-81) |  |  |
| Panasonic | CS-HE9LKE | unit | PanasonicAc (RKR-81) |  |  |
| Panasonic | CS-PC12QKT | unit | PanasonicAc (JKE-M13) |  |  |
| Panasonic | CS-U9RKR | unit | PanasonicAc (RKR-81) |  |  |
| Panasonic | CS-U12RKR | unit | PanasonicAc (RKR-81) |  |  |
| Panasonic | CS-E12JKDW | unit | PanasonicAc (JKE-M13) |  |  |
| Panasonic | SRK25ZMP-S, SRK35ZMP-S, SRK45ZMP-S | unit | MitsubishiHeavy88 |  |  |
| Hitachi | RAC-50HK1 | unit | Hitachi264 |  |  |
| Daikin | FTE09NV25 | unit | Daikin160 |  |  |
| Mitsubishi Electric | PAR-FL32MA | remote | Mitsubishi136 |  |  |
| Carrier | 40MAQB12B--3 | unit | Midea (RG57-F) |  |  |
| Carrier | 40MAQB18B--3 | unit | Midea (RG57-F) |  |  |
| Sungold | Sungold | unit | Midea (RG57-F) |  |  |
| Consul | CBV12CBBNA | unit | Kelon (dry-grade) |  |  |
| Consul | CBY12DBBNA | unit | Kelon (dry-grade) |  |  |
| Haier | Top-Tech 14 | unit | HaierYrw02 (A) |  |  |
| Midea | MPD-12CRN7 | unit | Midea (RG57) |  |  |
| Midea | MPPHB-09CRN7-QB6-N | unit | Midea (RG57) |  |  |
| Midea | RG10B(D1)/BGEFU1 | remote | Midea (RG57) |  |  |
| Hisense | DGR11R2 | unit | Kelon (dry-grade) |  |  |
| Beko | BXEU 090 | unit | HaierYrw02 (A) |  |  |
| Electrolux | EACS-HA | unit | Gree (YAW1F) |  |  |
| Trotec | YX1F | unit | Gree (YAW1F) |  |  |
| Pioneer | WYS018GMFI17RL | unit | Midea (RG57-F) |  |  |
| Pioneer | WYS009GMFI17RL | unit | Midea (RG57-F) |  |  |
| Pioneer | CB018GMFILCFHD | unit | Midea (RG57-F) |  |  |
| Pioneer | CB012GMFILCFHD | unit | Midea (RG57-F) |  |  |
| IGC | RAK-12NH | unit | Kelon (dry-grade) |  |  |
| IGC | RAK-18NH | unit | Kelon (dry-grade) |  |  |
| Blueridge | RG57A4 | unit | Midea (RG57-F) |  |  |
| Blueridge | BGEFU1 | unit | Midea (RG57-F) |  |  |
| Endesa | DGR11 | unit | Kelon (dry-grade) |  |  |
| Goodman | MSH123E21AXAA | unit | Midea (RG57) |  |  |
| Goodman | MST183E20ACAA | unit | Midea (RG57) |  |  |
| Goodman | RG57E1/BGEU1 | remote | Midea (RG57) |  |  |
| EcoAir | Split Type Wall Air Conditioner | unit | Midea (RG57-F) |  |  |
| Viessmann | Vitoclima 300-S | unit | Gree (YAW1F-wifi) |  |  |
| Hisense | AS-07UR4SYDD815G | unit | Kelon (dry-grade) |  |  |
| Panasonic | CS-SA9CKP | unit | PanasonicAc32 |  |  |
| General Electric | AE1PH09IWF | unit | Kelvinator |  |  |
| General Electric | AE0PH09IWO | unit | Kelvinator |  |  |
| General Electric | AE1PH12IWF | unit | Kelvinator |  |  |
| General Electric | AE0PH12IWO | unit | Kelvinator |  |  |
| General Electric | AE4PH18IWF | unit | Kelvinator |  |  |
| General Electric | AE5PH18IWO | unit | Kelvinator |  |  |
| Daikin | FTXS20LVMA | unit | Daikin312 |  |  |
| Daikin | FTXS25LVMA | unit | Daikin312 |  |  |
| Daikin | FTXS35LVMA | unit | Daikin312 |  |  |
| Daikin | FTXS46LVMA | unit | Daikin312 |  |  |
| Daikin | FTXS50LVMA | unit | Daikin312 |  |  |
| Daikin | FTXS60LVMA | unit | Daikin312 |  |  |
| Daikin | FTXS71LVMA | unit | Daikin312 |  |  |
| Daikin | FTXS85LVMA | unit | Daikin312 |  |  |
| Daikin | FTXS95LVMA | unit | Daikin312 |  |  |
| Daikin | FVXS50FV1B | unit | Daikin312 |  |  |
| Daikin | FTXL35J2V1B | unit | Daikin312 |  |  |
| Daikin | FTXM25UVMA | unit | Daikin312 |  |  |
| Daikin | FTXM35UVMA | unit | Daikin312 |  |  |
| Daikin | FTXD25DVMA | unit | Daikin312 |  |  |
| Daikin | FTXS35G2V1B | unit | Daikin312 |  |  |
| Daikin | FTXM71UVMA | unit | Daikin312 |  |  |
| Daikin | FTM09PV2S | unit | Daikin312 |  |  |
| Daikin | ATX20KV1B | unit | Daikin312 |  |  |
| Daikin | ATX25KV1B | unit | Daikin312 |  |  |
| Daikin | ATX35KV1B | unit | Daikin312 |  |  |
| Daikin | FTXG25EV1BS | unit | Daikin312 |  |  |
| Daikin | FTXG35EV1BS | unit | Daikin312 |  |  |
| Daikin | FTXG35EV1BW | unit | Daikin312 |  |  |
| Daikin | FTC15NV14 | unit | DaikinArc |  |  |
| Daikin | FTC20NV14 | unit | DaikinArc |  |  |
| Daikin | FTC25NV14 | unit | DaikinArc |  |  |
| Daikin | FTC35NV14 | unit | DaikinArc |  |  |
| Daikin | ATKC09TV2S | unit | DaikinArc |  |  |
| Daikin | FTKQ12TV2S | unit | DaikinArc |  |  |
| Daikin | FTXM35UVMZ | unit | Daikin312 |  |  |
| Daikin | DTXF35TVMA | unit | Daikin312 |  |  |
| Daikin | ARC452A21 | unit | Daikin312 |  |  |
| Daikin | FTXS09LVJU | unit | Daikin312 |  |  |
| Daikin | FTXS12LVJU | unit | Daikin312 |  |  |
| Daikin | FTXS15LVJU | unit | Daikin312 |  |  |
| Daikin | FTXS18LVJU | unit | Daikin312 |  |  |
| Daikin | FTXS24LVJU | unit | Daikin312 |  |  |
| Daikin | FTXS60FVMA | unit | Daikin216 |  |  |
| Gree | GWH18ACD-D3DNA 1M | unit | Gree (YAW1F-wifi) |  |  |
| Toshiba | RAS-13NKV-E / RAS-13NAV-E | unit | ToshibaAc |  |  |
| Toshiba | RAS-13NKV-A / RAS-13NAV-A | unit | ToshibaAc |  |  |
| Toshiba | RAS-16NKV-E / RAS-16NAV-E | unit | ToshibaAc |  |  |
| Toshiba | RAS-16NKV-A / RAS-16NAV-A | unit | ToshibaAc |  |  |
| Toshiba | RAS-M10SKV-E | unit | ToshibaAc |  |  |
| Toshiba | WH-TA05NE | unit | ToshibaAc |  |  |
| Toshiba | WH-TA11EJ | unit | ToshibaAc |  |  |
| Toshiba | RAC-PD0812CRRU | unit | Midea (RG57-F) |  |  |
| Toshiba | RAC-PD1013CWRU | unit | Midea (RG57-F) |  |  |
| Toshiba | RAC-PD1213CWRU | unit | Midea (RG57-F) |  |  |
| Toshiba | RAC-PD1414CWRU | unit | Midea (RG57-F) |  |  |
| Toshiba | RAS-13SKVR-A | unit | ToshibaAc |  |  |
| Haier | HSU-09HPL03/R03 | unit | Haier176 (A) |  |  |
| Tadiran | TAC 297H V3.2 | unit | Amcor |  |  |
| Midea | 42MAQA09S5 | unit | Coolix |  |  |
| Mitsubishi Heavy Industries | SRK25ZJ-S1 | unit | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | SRK13CRV-S1 | unit | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | SRK20ZSA-W | unit | MitsubishiHeavy152 |  |  |
| Mitsubishi Heavy Industries | SRK25ZSA-W | unit | MitsubishiHeavy152 |  |  |
| Mitsubishi Heavy Industries | SRK35ZSA-W | unit | MitsubishiHeavy152 |  |  |
| Mitsubishi Heavy Industries | SRK50ZSA-W | unit | MitsubishiHeavy152 |  |  |
| Mitsubishi Heavy Industries | SRK35ZJX-S | unit | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | SRK20ZJX-S | unit | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | SRK25ZSP-W | unit | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | SRK35ZSP-W | unit | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | SRK45ZSP-W | unit | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | DXK12Z3-S | unit | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | DXK09Z5-S | unit | MitsubishiHeavy88 |  |  |
| Mitsubishi Heavy Industries | DXK15Z5-S | unit | MitsubishiHeavy88 |  |  |
| Kelvinator | KCV70HRC | unit | Kelvinator |  |  |
| Electra | RC-3 | unit | Airwell |  |  |
| Mirage | Magnum Inverter 19 | unit | Coolix |  |  |
| Hyndai | H-ARI22-09H | unit | ElectraAc (aux) |  |  |
| ELGIN | HVQI12B2FB | unit | Coolix |  |  |
| Senville | SENA/12HF/IZ | unit | Midea (RG57) |  |  |
| Casper | SC-09FS32 | unit | ElectraAc |  |  |
| Panasonic | CS-E18FKR | unit | PanasonicAc (RKR-81) |  |  |
| Hisense | Hisense | unit | FujitsuAc (ARRAH2E) |  |  |
| HTW | HTWS035IX21D2-R32-I | unit | Coolix |  |  |
| Daikin | FTXS25CVMB | unit | Daikin216 |  |  |
| Daikin | FTXS35CVMB | unit | Daikin216 |  |  |
| Daikin | FTXS60BVMB | unit | Daikin216 |  |  |
| Daikin | FVXS25BVMB | unit | Daikin216 |  |  |
| Midea | MCD-24HRN1-Q1 | unit | Coolix |  |  |
| LG | RAS-32CNH2 | unit | Hitachi264 |  |  |
| Daikin | Daikin | unit | MitsubishiAc (remote) |  |  |
| Daikin | FTXV35AV1B | unit | Gree (YX1FSF) |  |  |
| Mitsubishi Electric | MSZ-GA35VA | unit | MitsubishiAc (remote) |  |  |
| Mitsubishi Electric | MSZ-HJ25VA | unit | MitsubishiAc (remote) |  |  |
| Mitsubishi Electric | MSZ-HJ35VA | unit | MitsubishiAc (remote) |  |  |
| Mitsubishi Electric | MSZ-GE22VA | unit | MitsubishiAc (remote) |  |  |
| Mitsubishi Electric | MS-SGD18VC | unit | MitsubishiAc (remote) |  |  |
| Mitsubishi Electric | MG-GN18VF | unit | MitsubishiAc (remote) |  |  |
| Mitsubishi Electric | MS-GN18VF | unit | MitsubishiAc (remote) |  |  |
| Mitsubishi Electric | MS-GN13VF | unit | MitsubishiAc (remote) |  |  |
| Mitsubishi Electric | MSXY-FP10VG | unit | MitsubishiAc (remote) |  |  |
| Mitsubishi Electric | MSXY-FP13VG | unit | MitsubishiAc (remote) |  |  |
| Mitsubishi Electric | MSXY-FP18VG | unit | MitsubishiAc (remote) |  |  |
| Mitsubishi Electric | MSZ-HR35VF | unit | MitsubishiAc (remote) |  |  |
| Tadiran | Tadiran-10i/15i/inv220a | unit | Gree (YAW1F) |  |  |
| Tadiran | Remote Control YB1FA | unit | Gree (YAW1F) |  |  |
| Tadiran | Tadiran Inverter | unit | Gree (YAW1F) |  |  |
| Beko | BPAK 120 | unit | Gree (YAW1F) |  |  |
| Daitsu | DOS12KIDB | unit | Gree (YAW1F-0) |  |  |
| Saunier Duval | 1 | unit | Gree (YAW1F) |  |  |
| Sigma | SGS32H13NE | unit | Gree (YAW1F) |  |  |
| Panasonic | CS-MRE7MKE | unit | PanasonicAc (JKE-M13) |  |  |
| LG | A06AWV | unit | LgAc (GE6711AR2853M) |  |  |
| LG | AKB74295303 | unit | Lg2 (AKB74955603) |  |  |
| Mitsubishi Electric | MSC-A12YV | unit | Tcl112Ac (GZ055BE1-R) |  |  |
| Akai | TEM-26CHSAAK5 | unit | Tcl112Ac (GZ055BE1-R) |  |  |
| Akai | TEM-70CHSAAK5 | unit | Tcl112Ac (GZ055BE1-R) |  |  |
| Akai | TEM-26CHSAKA5 | unit | Tcl112Ac (GZ055BE1-R) |  |  |
| Akai | TEM-35CHSAKA | unit | Tcl112Ac (GZ055BE1-R) |  |  |
| Akai | TEM-50CHSAKA | unit | Tcl112Ac (GZ055BE1-R) |  |  |
| Akai | TEM-35CHSABH | unit | Tcl112Ac (GZ055BE1-R) |  |  |
| Akai | TEM-35CHSF | unit | Tcl112Ac (GZ055BE1-R) |  |  |
| Erisson | EC-S07T2 | unit | Tcl112Ac (GZ055BE1-R) |  |  |
| Daitsu | DS-9KIDT | unit | Tcl112Ac (TAC09CHSD-R) |  |  |
| Hualing | KFR-45GW/JNV | unit | Tcl112Ac (GZ055BE1-R) |  |  |
| Hualing | KFR-45G/JNV | unit | Tcl112Ac (GZ055BE1-R) |  |  |
| TCL | TAC-12CHSD/XA21I | unit | Tcl112Ac (TAC09CHSD-RH) |  |  |
| Best | BSTS18CNE2 | unit | Tcl112Ac (TAC09CHSD-RH) |  |  |
| Devanti | WAC-05C-WH | unit | Tcl112Ac (TAC09CHSD-R) |  |  |
| Gree | Smart Inverter | unit | Gree (YAW1F-0) |  |  |
| Gree | KFR-50LW | unit | Gree (YX1FSF-H) |  |  |
| Gree | YAP1F2 | unit | Gree (YX1FSF-H) |  |  |
| ROYAL | RC-G25HN | unit | Tcl112Ac (TAC09CHSD-X03) |  |  |
| Trotec | YX1F6 | unit | Gree (YAW1F-0) |  |  |
| TCL | TAC-12CHSD/XA71IN | unit | Tcl112Ac (TAC09CHSD-X83) |  |  |
| Lennox | LNINVE052 | unit | Gree (YAW1F) |  |  |
| Lennox | LNINVC052 | unit | Gree (YAW1F) |  |  |
| HappyTree | TAC-12CHSD/XA81 | unit | Tcl112Ac (TAC09CHSD-X80) |  |  |
| Cecotec | EnergySilence 12000 AirClima (05290) | unit | Tcl112Ac (TAC09CHSD-X83) |  |  |
