# Phase 4 brand/model name table

423 old rows; 417 new rows; 74 old brands -> 77 new brands; 4 merges; 2 dropped (HITACHI_AC3).

Generic names: `<PROTOCOL> protocol`, or `<PROTOCOL> <enumerator> protocol` where the Device has remote variants; PROTOCOL is IRremoteESP8266's decode_type_t name (or the pyhvac Protocol name for native/Airspool), enumerator the `*_remote_model_t` name as written in IRsend.h. Kind of generic rows: 'remote'. Device 'legacy:<class>' marks the 0.1.x legacy-served rows (their phase-4 Device is not named yet). Variant is the 0.1.x one (teco/alaska: 'teco', removed in phase 4).

## AEG

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| aeg | Chillflex Pro AXP26U338CW | Chillflex Pro AXP26U338CW | unit |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: AEG,  Model: Chillflex Pro AXP26U338CW A/C |

## Airspool

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| airspool | generic | AIRSPOOL protocol | remote | yes | airspool.AirspoolDevice / None | variant: none (AIRSPOOL) |
| airspool | airspool | AIRSPOOL protocol | remote | yes | airspool.AirspoolDevice / None | variant: none (AIRSPOOL) |
| airspool | airspool mini-split | Mini-split | unit | yes | airspool.AirspoolDevice / None | cleaned: 'airspool mini-split' -> 'Mini-split' (brand repeated in the model dropped) |

## Airton

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| airton | SMVH09B-2A2A3NH | SMVH09B-2A2A3NH | unit |  | airton.AirtonDevice / None | irremote: ir_Airton.h: Brand: Airton,  Model: SMVH09B-2A2A3NH ref. 409730 A/C |
| airton | RD1A1 | RD1A1 | remote |  | airton.AirtonDevice / None | irremote: ir_Airton.h: Brand: Airton,  Model: RD1A1 remote |
| airton | generic | AIRTON protocol | remote |  | airton.AirtonDevice / None | variant: none (AIRTON) |

## Airwell

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| airwell | DC Series | DC Series | unit |  | airwell.AirwellDevice / None | cleaned: unchanged; no header line (the AIRWELL header lists 'DLS 21 DCI R410 AW') |
| airwell | RC08W remote | RC08W | remote |  | airwell.AirwellDevice / None | irremote: ir_Airwell.h: Brand: Airwell,  Model: RC08W remote |
| airwell | RC04 remote | RC04 | remote |  | airwell.AirwellDevice / None | irremote: ir_Airwell.h: Brand: Airwell,  Model: RC04 remote |
| airwell | generic | AIRWELL protocol | remote |  | airwell.AirwellDevice / None | variant: none (AIRWELL) |
| airwell | RC08B remote | RC08B | remote |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Airwell, Model: RC08B remote |

## Alaska

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| alaska | SAC9010QC | SAC9010QC | unit |  | technibel.TechnibelAcDevice / teco | irremote: ir_Teco.h: Brand: Alaska,  Model: SAC9010QC A/C |
| alaska | SAC9010QC remote | SAC9010QC | unit |  | technibel.TechnibelAcDevice / teco | irremote: ir_Teco.h: Brand: Alaska,  Model: SAC9010QC remote |

## Amana

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| amana | PBC093G00CC | PBC093G00CC | unit |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Amana,  Model: PBC093G00CC A/C |
| amana | YX1FF remote | YX1FF | remote |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Amana,  Model: YX1FF remote |

## Amcor

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| amcor | ADR-853H | ADR-853H | unit |  | amcor.AmcorDevice / None | irremote: ir_Amcor.h: Brand: Amcor,  Model: ADR-853H A/C |
| amcor | TAC-495 remote | TAC-495 | remote |  | amcor.AmcorDevice / None | irremote: ir_Amcor.h: Brand: Amcor,  Model: TAC-495 remote |
| amcor | TAC-444 remote | TAC-444 | remote |  | amcor.AmcorDevice / None | irremote: ir_Amcor.h: Brand: Amcor,  Model: TAC-444 remote |
| amcor | generic | AMCOR protocol | remote |  | amcor.AmcorDevice / None | variant: none (AMCOR) |

## Argo

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| argo | Ulisse 13 DCI | Ulisse 13 DCI | unit |  | argo.ArgoDevice / WREM2 | irremote: ir_Argo.h: Brand: Argo,  Model: Ulisse 13 DCI Mobile Split A/C [WREM2 remote] |
| argo | WREM2 remote | WREM2 | remote |  | argo.ArgoDevice / WREM2 | cleaned: ' remote' suffix -> kind (named in the ir_Argo.h Ulisse 13 DCI line) |
| argo | Ulisse Eco Mobile | Ulisse Eco | unit |  | argo.ArgoDevice / WREM3 | irremote: ir_Argo.h: Brand: Argo,  Model: Ulisse Eco Mobile Split A/C (Wifi) [WREM3 remote] |
| argo | WREM3 remote | WREM3 | remote |  | argo.ArgoDevice / WREM3 | cleaned: ' remote' suffix -> kind (named in the ir_Argo.h Ulisse Eco line) |
| argo | generic | ARGO SAC_WREM2 protocol | remote |  | argo.ArgoDevice / WREM2 | variant: SAC_WREM2 |
| argo | generic 2 | ARGO SAC_WREM3 protocol | remote |  | argo.ArgoDevice / WREM3 | variant: SAC_WREM3 |

## AUX

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| aux | KFR-35GW/BpNFW=3 | KFR-35GW/BpNFW=3 | unit |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: AUX,  Model: KFR-35GW/BpNFW=3 A/C |
| aux | YKR-T/011 remote | YKR-T/011 | remote |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: AUX,  Model: YKR-T/011 remote |

## Beko

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| beko | RG57K7(B)/BGEF Remote | RG57K7(B)/BGEF | remote |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Beko, Model: RG57K7(B)/BGEF Remote |
| beko | BINR 070/071 | BINR 070/071 | unit |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Beko, Model: BINR 070/071 split-type A/C |

## Bosch

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| bosch | CL3000i-Set 26 E | CL3000i-Set 26 E | unit |  | bosch.Bosch144Device / None | irremote: ir_Bosch.h: Brand: Bosch,  Model: CL3000i-Set 26 E A/C |
| bosch | RG10A(G2S)BGEF remote | RG10A(G2S)BGEF | remote |  | bosch.Bosch144Device / None | irremote: ir_Bosch.h: Brand: Bosch,  Model: RG10A(G2S)BGEF remote |
| bosch | generic | BOSCH144 protocol | remote |  | bosch.Bosch144Device / None | variant: none (BOSCH144) |
| bosch | RG36B4/BGE remote | RG36B4/BGE | remote |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Bosch, Model: RG36B4/BGE remote |
| bosch | B1ZAI2441W | B1ZAI2441W | unit |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Bosch, Model: B1ZAI2441W/B1ZAO2441W A/C |
| bosch | B1ZAO2441W | B1ZAO2441W | unit |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Bosch, Model: B1ZAI2441W/B1ZAO2441W A/C |

## Carrier

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| carrier | 42QG5A55970 remote | 42QG5A55970 | remote |  | carrier.CarrierAc64Device / None | irremote: ir_Carrier.h: Brand: Carrier/Surrey,  Model: 42QG5A55970 remote |
| carrier | 619EGX0090E0 | 619EGX0090E0 | unit |  | carrier.CarrierAc64Device / None | irremote: ir_Carrier.h: Brand: Carrier/Surrey,  Model: 619EGX0090E0 A/C |
| carrier | 619EGX0120E0 | 619EGX0120E0 | unit |  | carrier.CarrierAc64Device / None | irremote: ir_Carrier.h: Brand: Carrier/Surrey,  Model: 619EGX0120E0 A/C |
| carrier | 619EGX0180E0 | 619EGX0180E0 | unit |  | carrier.CarrierAc64Device / None | irremote: ir_Carrier.h: Brand: Carrier/Surrey,  Model: 619EGX0180E0 A/C |
| carrier | 619EGX0220E0 | 619EGX0220E0 | unit |  | carrier.CarrierAc64Device / None | irremote: ir_Carrier.h: Brand: Carrier/Surrey,  Model: 619EGX0220E0 A/C |
| carrier | 53NGK009/012 | 53NGK009/012 | unit |  | carrier.CarrierAc64Device / None | irremote: ir_Carrier.h: Brand: Carrier/Surrey,  Model: 53NGK009/012 Inverter |
| carrier | generic | CARRIER_AC64 protocol | remote |  | carrier.CarrierAc64Device / None | variant: none (CARRIER_AC64) |
| carrier | 42NQV060M2 / 38NYV060M2 | 42NQV060M2 / 38NYV060M2 | unit |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Carrier,  Model: 42NQV060M2 / 38NYV060M2 A/C |
| carrier | 42NQV050M2 / 38NYV050M2 | 42NQV050M2 / 38NYV050M2 | unit |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Carrier,  Model: 42NQV050M2 / 38NYV050M2 A/C |
| carrier | 42NQV035M2 / 38NYV035M2 | 42NQV035M2 / 38NYV035M2 | unit |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Carrier,  Model: 42NQV035M2 / 38NYV035M2 A/C |
| carrier | 42NQV025M2 / 38NYV025M2 | 42NQV025M2 / 38NYV025M2 | unit |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Carrier,  Model: 42NQV025M2 / 38NYV025M2 A/C |

## Centek

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| centek | SCT-65Q09 | SCT-65Q09 | unit |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: Centek,  Model: SCT-65Q09 A/C |
| centek | YKR-P/002E remote | YKR-P/002E | remote |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: Centek,  Model: YKR-P/002E remote |

## Comfee

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| comfee | MPD1-12CRN7 | MPD1-12CRN7 | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Comfee, Model: MPD1-12CRN7 A/C (MIDEA) |

## Cooper & Hunter

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| cooper_hunter | YB1F2 remote | YB1F2 | remote |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Cooper & Hunter,  Model: YB1F2 remote |
| cooper_hunter | CH-S09FTXG | CH-S09FTXG | unit |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Cooper & Hunter,  Model: CH-S09FTXG A/C |

## Corona

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| corona | CSH-N2211 | CSH-N2211 | unit |  | corona.CoronaAcDevice / None | irremote: ir_Corona.h: Brand: Corona,  Model: CSH-N2211 A/C |
| corona | CSH-N2511 | CSH-N2511 | unit |  | corona.CoronaAcDevice / None | irremote: ir_Corona.h: Brand: Corona,  Model: CSH-N2511 A/C |
| corona | CSH-N2811 | CSH-N2811 | unit |  | corona.CoronaAcDevice / None | irremote: ir_Corona.h: Brand: Corona,  Model: CSH-N2811 A/C |
| corona | CSH-N4011 | CSH-N4011 | unit |  | corona.CoronaAcDevice / None | irremote: ir_Corona.h: Brand: Corona,  Model: CSH-N4011 A/C |
| corona | AR-01 remote | AR-01 | remote |  | corona.CoronaAcDevice / None | irremote: ir_Corona.h: Brand: Corona,  Model: AR-01 remote |
| corona | generic | CORONA_AC protocol | remote |  | corona.CoronaAcDevice / None | variant: none (CORONA_AC) |

## Daewoo

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| daewoo | DSB-F0934ELH-V | DSB-F0934ELH-V | unit |  | tcl.Tcl112AcDevice / GZ055BE1 | irremote: ir_Tcl.h: Brand: Daewoo,  Model: DSB-F0934ELH-V A/C |
| daewoo | GYKQ-52E remote | GYKQ-52E | remote |  | tcl.Tcl112AcDevice / GZ055BE1 | irremote: ir_Tcl.h: Brand: Daewoo,  Model: GYKQ-52E remote |

## Daichi

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| haier | Daichi D-H | D-H | unit |  | haier.Haier176Device / A | irremote: ir_Haier.h: Brand: Daichi, Model: D-H A/C (HAIER_AC176) |

## Daikin

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| daikin | generic | DAIKIN_NATIVE protocol | remote | yes | legacy:daikin.Daikinth / None | variant: none (DAIKIN_NATIVE) |
| daikin | smash 2 | Smash II | unit | yes | legacy:daikin.Smash2 / None | cleaned: 'smash 2' -> 'Smash II' (Daikin's SMASH II range) |
| daikin | ARC433 remote | ARC433** | remote |  | daikin.DaikinArcDevice / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: ARC433** remote (DAIKIN) |
| daikin | ARC477A1 remote | ARC477A1 | remote |  | daikin.Daikin2Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: ARC477A1 remote (DAIKIN2) |
| daikin | FTXZ25NV1B | FTXZ25NV1B | unit |  | daikin.Daikin2Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: FTXZ25NV1B A/C (DAIKIN2) |
| daikin | FTXZ35NV1B | FTXZ35NV1B | unit |  | daikin.Daikin2Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: FTXZ35NV1B A/C (DAIKIN2) |
| daikin | FTXZ50NV1B | FTXZ50NV1B | unit |  | daikin.Daikin2Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: FTXZ50NV1B A/C (DAIKIN2) |
| daikin | ARC433B69 remote | ARC433B69 | remote |  | daikin.Daikin216Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: ARC433B69 remote (DAIKIN216) |
| daikin | ARC423A5 remote | ARC423A5 | remote |  | daikin.Daikin160Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: ARC423A5 remote (DAIKIN160) |
| daikin | FTE12HV2S | FTE12HV2S | unit |  | daikin.Daikin160Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: FTE12HV2S A/C |
| daikin | BRC4C153 remote | BRC4C153 | remote |  | daikin.Daikin176Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: BRC4C153 remote (DAIKIN176) |
| daikin | FFQ35B8V1B | FFQ35B8V1B | unit |  | daikin.Daikin176Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: FFQ35B8V1B A/C (DAIKIN176) |
| daikin | BRC4C151 remote | BRC4C151 | remote |  | daikin.Daikin176Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: BRC4C151 remote (DAIKIN176) |
| daikin | 17 Series FTXB09AXVJU | 17 Series FTXB09AXVJU | unit |  | daikin.Daikin128Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: 17 Series FTXB09AXVJU A/C (DAIKIN128) |
| daikin | 17 Series FTXB12AXVJU | 17 Series FTXB12AXVJU | unit |  | daikin.Daikin128Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: 17 Series FTXB12AXVJU A/C (DAIKIN128) |
| daikin | 17 Series FTXB24AXVJU | 17 Series FTXB24AXVJU | unit |  | daikin.Daikin128Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: 17 Series FTXB24AXVJU A/C (DAIKIN128) |
| daikin | BRC52B63 remote | BRC52B63 | remote |  | daikin.Daikin128Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: BRC52B63 remote (DAIKIN128) |
| daikin | ARC480A5 remote | ARC480A5 | remote |  | daikin.Daikin152Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: ARC480A5 remote (DAIKIN152) |
| daikin | FFN-C/FCN-F Series | FFN-C/FCN-F Series | unit |  | daikin.Daikin64Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: FFN-C/FCN-F Series A/C (DAIKIN64) |
| daikin | DGS01 remote | DGS01 | remote |  | daikin.Daikin64Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: DGS01 remote (DAIKIN64) |
| daikin | M Series | M Series | unit |  | daikin.DaikinArcDevice / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: M Series A/C (DAIKIN) |
| daikin | FTXM-M | FTXM-M | unit |  | daikin.DaikinArcDevice / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: FTXM-M A/C (DAIKIN) |
| daikin | ARC466A12 remote | ARC466A12 | remote |  | daikin.DaikinArcDevice / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: ARC466A12 remote (DAIKIN) |
| daikin | ARC466A33 remote | ARC466A33 | remote |  | daikin.DaikinArcDevice / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: ARC466A33 remote (DAIKIN) |
| daikin | FTWX35AXV1 | FTWX35AXV1 | unit |  | daikin.Daikin64Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: FTWX35AXV1 A/C (DAIKIN64) |
| daikin | ARC484A4 remote | ARC484A4 | remote |  | daikin.Daikin216Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: ARC484A4 remote (DAIKIN216) |
| daikin | FTQ60TV16U2 | FTQ60TV16U2 | unit |  | daikin.Daikin216Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: FTQ60TV16U2 A/C (DAIKIN216) |
| daikin | FTXM20R5V1B | FTXM20R5V1B | unit |  | daikin.Daikin312Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: FTXM20R5V1B A/C (DAIKIN312) |
| daikin | ARC466A67 remote | ARC466A67 | remote |  | daikin.Daikin312Device / None | irremote: ir_Daikin.h: Brand: Daikin,  Model: ARC466A67 remote (DAIKIN312) |
| daikin | Daikin | DAIKIN protocol | remote |  | daikin.DaikinArcDevice / None | variant: none (DAIKIN) |
| daikin | Daikin2 | DAIKIN2 protocol | remote |  | daikin.Daikin2Device / None | variant: none (DAIKIN2) |
| daikin | Daikin64 | DAIKIN64 protocol | remote |  | daikin.Daikin64Device / None | variant: none (DAIKIN64) |
| daikin | Daikin128 | DAIKIN128 protocol | remote |  | daikin.Daikin128Device / None | variant: none (DAIKIN128) |
| daikin | Daikin152 | DAIKIN152 protocol | remote |  | daikin.Daikin152Device / None | variant: none (DAIKIN152) |
| daikin | Daikin160 | DAIKIN160 protocol | remote |  | daikin.Daikin160Device / None | variant: none (DAIKIN160) |
| daikin | Daikin176 | DAIKIN176 protocol | remote |  | daikin.Daikin176Device / None | variant: none (DAIKIN176) |
| daikin | Daikin216 | DAIKIN216 protocol | remote |  | daikin.Daikin216Device / None | variant: none (DAIKIN216) |
| daikin | Daikin312 | DAIKIN312 protocol | remote |  | daikin.Daikin312Device / None | variant: none (DAIKIN312) |

## Danby

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| danby | DAC080BGUWDB | DAC080BGUWDB | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Danby,  Model: DAC080BGUWDB (MIDEA) |
| danby | DAC100BGUWDB | DAC100BGUWDB | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Danby,  Model: DAC100BGUWDB (MIDEA) |
| danby | DAC120BGUWDB | DAC120BGUWDB | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Danby,  Model: DAC120BGUWDB (MIDEA) |
| danby | R09C/BCGE remote | R09C/BCGE | remote |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Danby,  Model: R09C/BCGE remote (MIDEA) |

## De'Longhi

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| delonghi | PAC A95 | PAC A95 | unit |  | delonghi.DelonghiAcDevice / None | irremote: ir_Delonghi.h: Brand: Delonghi,  Model: PAC A95 |
| delonghi | generic | DELONGHI_AC protocol | remote |  | delonghi.DelonghiAcDevice / None | variant: none (DELONGHI_AC) |
| delonghi | PAC EM90 | PAC EM90 | unit |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: Delonghi, Modell: PAC EM90 |

## Duux

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| trotech | Duux Blizzard Smart 10K / DXMA04 | Blizzard Smart 10K / DXMA04 | unit |  | trotech.TrotecDevice / None | irremote: ir_Trotec.h: Brand: Duux,  Model: Blizzard Smart 10K / DXMA04 A/C (TROTEC) |

## EcoClim

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| ecoclim | HYSFR-P348 remote | HYSFR-P348 | remote |  | ecoclim.EcoclimDevice / None | irremote: ir_Ecoclim.h: Brand: EcoClim,  Model: HYSFR-P348 remote |
| ecoclim | ZC200DPO | ZC200DPO | unit |  | ecoclim.EcoclimDevice / None | irremote: ir_Ecoclim.h: Brand: EcoClim,  Model: ZC200DPO A/C |
| ecoclim | generic | ECOCLIM protocol | remote |  | ecoclim.EcoclimDevice / None | variant: none (ECOCLIM) |

## EKOKAI

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| ekokai | generic | GREE YAW1F protocol | remote |  | gree.GreeDevice / YAW1F | variant: YAW1F |

## Electra

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| electra | Classic INV 17 | Classic INV 17 | unit |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: Electra,  Model: Classic INV 17 / AXW12DCS A/C |
| electra | AXW12DCS | AXW12DCS | unit |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: Electra,  Model: Classic INV 17 / AXW12DCS A/C |
| electra | YKR-M/003E remote | YKR-M/003E | remote |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: Electra,  Model: YKR-M/003E remote |
| electra | generic | ELECTRA_AC protocol | remote |  | electra.ElectraAcDevice / None | variant: none (ELECTRA_AC) |

## Electrolux

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| electrolux | YKR-H/531E | YKR-H/531E | unit |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: Electrolux,  Model: YKR-H/531E A/C |

## Eurom

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| eurom | Polar 16CH | Polar 16CH | unit |  | eurom.EuromDevice / None | irremote: ir_Eurom.h: Brand: Eurom,  Model: Polar 16CH |
| eurom | generic | EUROM protocol | remote |  | eurom.EuromDevice / None | variant: none (EUROM) |

## Frigidaire

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| frigidaire | FGPC102AB1 | FGPC102AB1 | unit |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: Frigidaire,  Model: FGPC102AB1 A/C |

## Fujitsu

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| fujitsu | AR-RAH2E remote | AR-RAH2E | remote |  | fujitsu.FujitsuAcDevice / ARRAH2E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-RAH2E remote (ARRAH2E) |
| fujitsu | ASYG30LFCA | ASYG30LFCA | unit |  | fujitsu.FujitsuAcDevice / ARRAH2E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: ASYG30LFCA A/C (ARRAH2E) |
| fujitsu | AR-DB1 remote | AR-DB1 | remote |  | fujitsu.FujitsuAcDevice / ARDB1 | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-DB1 remote (ARDB1) |
| fujitsu | AST9RSGCW | AST9RSGCW | unit |  | fujitsu.FujitsuAcDevice / ARDB1 | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AST9RSGCW A/C (ARDB1) |
| fujitsu | AR-REB1E remote | AR-REB1E | remote |  | fujitsu.FujitsuAcDevice / ARREB1E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-REB1E remote (ARREB1E) |
| fujitsu | ASYG7LMCA | ASYG7LMCA | unit |  | fujitsu.FujitsuAcDevice / ARREB1E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: ASYG7LMCA A/C (ARREB1E) |
| fujitsu | AR-RAE1E remote | AR-RAE1E | remote |  | fujitsu.FujitsuAcDevice / ARRAH2E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-RAE1E remote (ARRAH2E) |
| fujitsu | AGTV14LAC | AGTV14LAC | unit |  | fujitsu.FujitsuAcDevice / ARRAH2E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AGTV14LAC A/C (ARRAH2E) |
| fujitsu | AR-RAC1E remote | AR-RAC1E | remote |  | fujitsu.FujitsuAcDevice / ARRAH2E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-RAC1E remote (ARRAH2E) |
| fujitsu | ASTB09LBC | ASTB09LBC | unit |  | fujitsu.FujitsuAcDevice / ARRY4 | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: ASTB09LBC A/C (ARRY4) |
| fujitsu | AR-RY4 remote | AR-RY4 | remote |  | fujitsu.FujitsuAcDevice / ARRY4 | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-RY4 remote (ARRY4) |
| fujitsu | AR-DL10 remote | AR-DL10 | remote |  | fujitsu.FujitsuAcDevice / ARDB1 | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-DL10 remote (ARDB1) |
| fujitsu | ASU30C1 | ASU30C1 | unit |  | fujitsu.FujitsuAcDevice / ARDB1 | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: ASU30C1 A/C (ARDB1) |
| fujitsu | AR-RAH1U remote | AR-RAH1U | remote |  | fujitsu.FujitsuAcDevice / ARREB1E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-RAH1U remote (ARREB1E) |
| fujitsu | AR-RAH2U remote | AR-RAH2U | remote |  | fujitsu.FujitsuAcDevice / ARRAH2E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-RAH2U remote (ARRAH2E) |
| fujitsu | ASU12RLF | ASU12RLF | unit |  | fujitsu.FujitsuAcDevice / ARREB1E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: ASU12RLF A/C (ARREB1E) |
| fujitsu | AR-REW4E remote | AR-REW4E | remote |  | fujitsu.FujitsuAcDevice / ARREW4E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-REW4E remote (ARREW4E) |
| fujitsu | ASYG09KETA-B | ASYG09KETA-B | unit |  | fujitsu.FujitsuAcDevice / ARREW4E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: ASYG09KETA-B A/C (ARREW4E) |
| fujitsu | AR-REB4E remote | AR-REB4E | remote |  | fujitsu.FujitsuAcDevice / ARREB1E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-REB4E remote (ARREB1E) |
| fujitsu | ASTG09K | ASTG09K | unit |  | fujitsu.FujitsuAcDevice / ARREW4E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: ASTG09K A/C (ARREW4E) |
| fujitsu | ASTG18K | ASTG18K | unit |  | fujitsu.FujitsuAcDevice / ARREW4E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: ASTG18K A/C (ARREW4E) |
| fujitsu | AR-REW1E remote | AR-REW1E | remote |  | fujitsu.FujitsuAcDevice / ARREW4E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-REW1E remote (ARREW4E) |
| fujitsu | AR-REG1U remote | AR-REG1U | remote |  | fujitsu.FujitsuAcDevice / ARRAH2E | irremote: ir_Fujitsu.h: Brand: Fujitsu,  Model: AR-REG1U remote (ARRAH2E) |
| fujitsu | generic | FUJITSU_AC ARRAH2E protocol | remote |  | fujitsu.FujitsuAcDevice / ARRAH2E | variant: ARRAH2E |
| fujitsu | generic 2 | FUJITSU_AC ARDB1 protocol | remote |  | fujitsu.FujitsuAcDevice / ARDB1 | variant: ARDB1 |
| fujitsu | generic 3 | FUJITSU_AC ARREB1E protocol | remote |  | fujitsu.FujitsuAcDevice / ARREB1E | variant: ARREB1E |
| fujitsu | generic 4 | FUJITSU_AC ARJW2 protocol | remote |  | fujitsu.FujitsuAcDevice / ARJW2 | variant: ARJW2 |
| fujitsu | generic 5 | FUJITSU_AC ARRY4 protocol | remote |  | fujitsu.FujitsuAcDevice / ARRY4 | variant: ARRY4 |
| fujitsu | generic 6 | FUJITSU_AC ARREW4E protocol | remote |  | fujitsu.FujitsuAcDevice / ARREW4E | variant: ARREW4E |

## Fujitsu General

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| fujitsu | General AR-RCE1E remote | AR-RCE1E | remote |  | fujitsu.FujitsuAcDevice / ARRAH2E | irremote: ir_Fujitsu.h: Brand: Fujitsu General,  Model: AR-RCE1E remote (ARRAH2E) |
| fujitsu | General ASHG09LLCA | ASHG09LLCA | unit |  | fujitsu.FujitsuAcDevice / ARRAH2E | irremote: ir_Fujitsu.h: Brand: Fujitsu General,  Model: ASHG09LLCA A/C (ARRAH2E) |
| fujitsu | General AOHG09LLC | AOHG09LLC | unit |  | fujitsu.FujitsuAcDevice / ARRAH2E | irremote: ir_Fujitsu.h: Brand: Fujitsu General,  Model: AOHG09LLC A/C (ARRAH2E) |
| fujitsu | General AR-JW2 remote | AR-JW2 | remote |  | fujitsu.FujitsuAcDevice / ARJW2 | irremote: ir_Fujitsu.h: Brand: Fujitsu General,  Model: AR-JW2 remote (ARJW2) |
| fujitsu | General AR-JW17 remote | AR-JW17 | remote |  | fujitsu.FujitsuAcDevice / ARDB1 | irremote: ir_Fujitsu.h: Brand: Fujitsu General,  Model: AR-JW17 remote (ARDB1) |

## GE

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| ge | AG1BH09AW101 | AG1BH09AW101 | unit |  | lg.LgAcDevice / GE6711AR2853M | irremote: ir_LG.h: Brand: General Electric,  Model: AG1BH09AW101 A/C (LG - GE6711AR2853M) |
| ge | 6711AR2853M Remote | 6711AR2853M | remote |  | lg.LgAcDevice / GE6711AR2853M | irremote: ir_LG.h: Brand: General Electric,  Model: 6711AR2853M Remote (LG - GE6711AR2853M) |

## Goodweather

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| goodweather | ZH/JT-03 remote | ZH/JT-03 | remote |  | goodweather.GoodweatherDevice / None | irremote: ir_Goodweather.h: Brand: Goodweather,  Model: ZH/JT-03 remote |
| goodweather | generic | GOODWEATHER protocol | remote |  | goodweather.GoodweatherDevice / None | variant: none (GOODWEATHER) |

## Gree

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| gree | YAA1FBF remote | YAA1FBF | remote |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Gree,  Model: YAA1FBF remote |
| gree | YB1F2F remote | YB1F2F | remote |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Gree,  Model: YB1F2F remote |
| gree | YAN1F1 remote | YAN1F1 | remote |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Gree,  Model: YAN1F1 remote |
| gree | YX1F2F remote | YX1F2F | remote |  | gree.GreeDevice / YX1FSF | irremote: ir_Gree.h: Brand: Gree,  Model: YX1F2F remote (YX1FSF) |
| gree | VIR09HP115V1AH | VIR09HP115V1AH | unit |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Gree,  Model: VIR09HP115V1AH A/C |
| gree | VIR12HP230V1AH | VIR12HP230V1AH | unit |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Gree,  Model: VIR12HP230V1AH A/C |
| gree | gemeric | GREE YAW1F protocol | remote |  | gree.GreeDevice / YAW1F | variant: YAW1F |
| gree | YAPOF3 remote | YAPOF3 | remote |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Gree,  Model: YAPOF3 remote |
| gree | YAP0F8 remote | YAP0F8 | remote |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Gree,  Model: YAP0F8 remote |

## Green

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| green | YBOFB remote | YBOFB | remote |  | gree.GreeDevice / YBOFB | irremote: ir_Gree.h: Brand: Green,  Model: YBOFB remote |
| green | YBOFB2 remote | YBOFB2 | remote |  | gree.GreeDevice / YBOFB | irremote: ir_Gree.h: Brand: Green,  Model: YBOFB2 remote |

## Haier

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| haier | HSU07-HEA03 remote | HSU07-HEA03 | remote |  | haier.HaierAcDevice / None | irremote: ir_Haier.h: Brand: Haier,  Model: HSU07-HEA03 remote (HAIER_AC) |
| haier | YR-W02 remote | YR-W02 | remote |  | haier.HaierYrw02Device / A | irremote: ir_Haier.h: Brand: Haier,  Model: YR-W02 remote (HAIER_AC_YRW02) |
| haier | HSU-09HMC203 | HSU-09HMC203 | unit |  | haier.HaierYrw02Device / A | irremote: ir_Haier.h: Brand: Haier,  Model: HSU-09HMC203 A/C (HAIER_AC_YRW02) |
| haier | V9014557 M47 8D remote | V9014557 M47 8D | remote |  | haier.Haier176Device / A | irremote: ir_Haier.h: Brand: Haier,  Model: V9014557 M47 8D remote (HAIER_AC176) |
| haier | KFR-26GW/83@UI-Ge | KFR-26GW/83@UI-Ge | unit |  | haier.Haier160Device / None | irremote: ir_Haier.h: Brand: Haier,  Model: KFR-26GW/83@UI-Ge A/C (HAIER_AC160) |
| haier | generic | HAIER_AC protocol | remote |  | haier.HaierAcDevice / None | variant: none (HAIER_AC) |
| haier | YR-W02 Code A | HAIER_AC_YRW02 V9014557_A protocol | remote |  | haier.HaierYrw02Device / A | variant: V9014557_A |
| haier | YR-W02 Code B | HAIER_AC_YRW02 V9014557_B protocol | remote |  | haier.HaierYrw02Device / B | variant: V9014557_B |
| haier | generic 176 code a | HAIER_AC176 V9014557_A protocol | remote |  | haier.Haier176Device / A | variant: V9014557_A |
| haier | generic 176 code b | HAIER_AC176 V9014557_B protocol | remote |  | haier.Haier176Device / B | variant: V9014557_B |
| haier | generic 160 | HAIER_AC160 protocol | remote |  | haier.Haier160Device / None | variant: none (HAIER_AC160) |

## Hitachi

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| hitachi | RAS-35THA6 remote | RAS-35THA6 | remote |  | hitachi.HitachiAcDevice / None | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: RAS-35THA6 remote |
| hitachi | LT0541-HTA remote | LT0541-HTA | remote |  | hitachi.Hitachi1Device / A | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: LT0541-HTA remote  (HITACHI_AC1) |
| hitachi | Series VI | Series VI | unit |  | hitachi.Hitachi1Device / A | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: Series VI A/C (Circa 2007) (HITACHI_AC1) |
| hitachi | RAR-8P2 remote | RAR-8P2 | remote |  | hitachi.Hitachi424Device / None | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: RAR-8P2 remote (HITACHI_AC424) |
| hitachi | RAS-AJ25H | RAS-AJ25H | unit |  | hitachi.Hitachi424Device / None | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: RAS-AJ25H A/C (HITACHI_AC424) |
| hitachi | KAZE-312KSDP | KAZE-312KSDP | unit |  | hitachi.Hitachi1Device / A | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: KAZE-312KSDP A/C (HITACHI_AC1) |
| hitachi | R-LT0541-HTA/Y.K.1.1-1 V2.3 remote | R-LT0541-HTA/Y.K.1.1-1 V2.3 | remote |  | hitachi.Hitachi1Device / A | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: R-LT0541-HTA/Y.K.1.1-1 V2.3 remote (HITACHI_AC1) |
| hitachi | RAS-22NK | RAS-22NK | unit |  | hitachi.Hitachi344Device / None | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: RAS-22NK A/C (HITACHI_AC344) |
| hitachi | RF11T1 | RF11T1 | remote |  | hitachi.Hitachi344Device / None | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: RF11T1 remote (HITACHI_AC344) |
| hitachi | RAR-2P2 remote | RAR-2P2 | remote |  | hitachi.Hitachi264Device / None | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: RAR-2P2 remote (HITACHI_AC264) |
| hitachi | RAK-25NH5 | RAK-25NH5 | unit |  | hitachi.Hitachi264Device / None | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: RAK-25NH5 A/C (HITACHI_AC264) |
| hitachi | RAR-3U3 remote | RAR-3U3 | remote |  | hitachi.Hitachi296Device / None | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: RAR-3U3 remote (HITACHI_AC296) |
| hitachi | RAS-70YHA3 | RAS-70YHA3 | unit |  | hitachi.Hitachi296Device / None | irremote: ir_Hitachi.h: Brand: Hitachi,  Model: RAS-70YHA3 A/C (HITACHI_AC296) |
| hitachi | generic | HITACHI_AC protocol | remote |  | hitachi.HitachiAcDevice / None | variant: none (HITACHI_AC) |
| hitachi | generic 1 code a | HITACHI_AC1 R_LT0541_HTA_A protocol | remote |  | hitachi.Hitachi1Device / A | variant: R_LT0541_HTA_A |
| hitachi | generic 1 code b | HITACHI_AC1 R_LT0541_HTA_B protocol | remote |  | hitachi.Hitachi1Device / B | variant: R_LT0541_HTA_B |
| hitachi | generic 424 | HITACHI_AC424 protocol | remote |  | hitachi.Hitachi424Device / None | variant: none (HITACHI_AC424) |
| hitachi | generic 344 | HITACHI_AC344 protocol | remote |  | hitachi.Hitachi344Device / None | variant: none (HITACHI_AC344) |
| hitachi | generic 264 | HITACHI_AC264 protocol | remote |  | hitachi.Hitachi264Device / None | variant: none (HITACHI_AC264) |
| hitachi | generic 296 | HITACHI_AC296 protocol | remote |  | hitachi.Hitachi296Device / None | variant: none (HITACHI_AC296) |

## Kastron

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| kastron | RG57A7/BGEF remote | RG57A7/BGEF | remote |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Kastron, Model: RG57A7/BGEF Inverter remote |

## Kaysun

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| kaysun | Casual CF | Casual CF | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Kaysun, Model: Casual CF A/C (MIDEA) |
| kaysun | Casual CF Alt | Casual CF (COOLIX) | unit |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Kaysun, Model: Casual CF A/C |

## Kelon

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| kelon | remote | ON/OFF 9000-12000 | unit |  | kelon.KelonDevice / None | irremote: ir_Kelon.h: Brand: Kelon,  Model: ON/OFF 9000-12000 (KELON) |

## Kelvinator

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| kelvinator | YALIF remote | YALIF | remote |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Kelvinator,  Model: YALIF Remote |
| kelvinator | KSV26CRC | KSV26CRC | unit |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Kelvinator,  Model: KSV26CRC A/C |
| kelvinator | KSV26HRC | KSV26HRC | unit |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Kelvinator,  Model: KSV26HRC A/C |
| kelvinator | KSV35CRC | KSV35CRC | unit |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Kelvinator,  Model: KSV35CRC A/C |
| kelvinator | KSV35HRC | KSV35HRC | unit |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Kelvinator,  Model: KSV35HRC A/C |
| kelvinator | KSV53HRC | KSV53HRC | unit |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Kelvinator,  Model: KSV53HRC A/C |
| kelvinator | KSV62HRC | KSV62HRC | unit |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Kelvinator,  Model: KSV62HRC A/C |
| kelvinator | KSV70CRC | KSV70CRC | unit |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Kelvinator,  Model: KSV70CRC A/C |
| kelvinator | KSV70HRC | KSV70HRC | unit |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Kelvinator,  Model: KSV70HRC A/C |
| kelvinator | KSV80HRC | KSV80HRC | unit |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Kelvinator,  Model: KSV80HRC A/C |
| kelvinator | generic | KELVINATOR protocol | remote |  | kelvinator.KelvinatorDevice / None | variant: none (KELVINATOR) |

## Keystone

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| keystone | RG57H4(B)BGEF remote | RG57H4(B)BGEF | remote |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Keystone, Model: RG57H4(B)BGEF remote (MIDEA) |

## Leberg

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| leberg | LBS-TOR07 | LBS-TOR07 | unit |  | tcl.Tcl112AcDevice / TAC09CHSD | irremote: ir_Tcl.h: Brand: Leberg,  Model: LBS-TOR07 A/C (TAC09CHSD) |

## Lennox

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| lennox | RG57A6/BGEFU1 remote | RG57A6/BGEFU1 | remote |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: RG57A6/BGEFU1 remote (MIDEA) |
| lennox | MWMA009S4-3P | MWMA009S4-3P | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: MWMA009S4-3P A/C (MIDEA) |
| lennox | MWMA012S4-3P | MWMA012S4-3P | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: MWMA012S4-3P A/C (MIDEA) |
| lennox | MCFA | MCFA | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: MCFA indoor split A/C (MIDEA) |
| lennox | MCFB | MCFB | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: MCFB indoor split A/C (MIDEA) |
| lennox | MMDA | MMDA | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: MMDA indoor split A/C (MIDEA) |
| lennox | MMDB | MMDB | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: MMDB indoor split A/C (MIDEA) |
| lennox | MWMA | MWMA | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: MWMA indoor split A/C (MIDEA) |
| lennox | MWMB | MWMB | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: MWMB indoor split A/C (MIDEA) |
| lennox | M22A | M22A | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: M22A indoor split A/C (MIDEA) |
| lennox | M33A | M33A | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: M33A indoor split A/C (MIDEA) |
| lennox | M33B | M33B | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Lennox,  Model: M33B indoor split A/C (MIDEA) |

## LG

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| lg | generic | LG_NATIVE protocol | remote | yes | legacy:lg.LG / None | variant: none (LG_NATIVE) |
| lg | inverter v | Inverter V | unit | yes | legacy:lg.InverterV / None | cleaned: capitalised as LG writes it ('Inverter V' range) |
| lg | dual inverter | Dual Inverter | unit | yes | legacy:lg.DualInverter / None | cleaned: capitalised as LG writes it ('Dual Inverter' range) |
| lg | 6711A20083V  remote | 6711A20083V | remote |  | lg.LgAcDevice / LG6711A20083V | irremote: ir_LG.h: Brand: LG,  Model: 6711A20083V remote (LG - LG6711A20083V) |
| lg | TS-H122ERM1  remote | TS-H122ERM1 | remote |  | lg.LgAcDevice / LG6711A20083V | irremote: ir_LG.h: Brand: LG,  Model: TS-H122ERM1 remote (LG - LG6711A20083V) |
| lg | AKB74395308  remote | AKB74395308 | remote |  | lg.Lg2Device / AKB75215403 | irremote: ir_LG.h: Brand: LG,  Model: AKB74395308 remote (LG2) |
| lg | S4-W12JA3AA | S4-W12JA3AA | unit |  | lg.Lg2Device / AKB75215403 | irremote: ir_LG.h: Brand: LG,  Model: S4-W12JA3AA A/C (LG2) |
| lg | AKB75215403  remote | AKB75215403 | remote |  | lg.Lg2Device / AKB75215403 | irremote: ir_LG.h: Brand: LG,  Model: AKB75215403 remote (LG2) |
| lg | AKB74955603  remote | AKB74955603 | remote |  | lg.Lg2Device / AKB74955603 | irremote: ir_LG.h: Brand: LG,  Model: AKB74955603 remote (LG2 - AKB74955603) |
| lg | A4UW30GFA2 | A4UW30GFA2 | unit |  | lg.Lg2Device / AKB74955603 | irremote: ir_LG.h: Brand: LG,  Model: A4UW30GFA2 A/C (LG2 - AKB74955603 & AKB73757604) |
| lg | AMNW09GSJA0 | AMNW09GSJA0 | unit |  | lg.Lg2Device / AKB74955603 | irremote: ir_LG.h: Brand: LG,  Model: AMNW09GSJA0 A/C (LG2 - AKB74955603) |
| lg | AMNW24GTPA1 | AMNW24GTPA1 | unit |  | lg.Lg2Device / AKB73757604 | irremote: ir_LG.h: Brand: LG,  Model: AMNW24GTPA1 A/C (LG2 - AKB73757604) |
| lg | AKB73757604  remote | AKB73757604 | remote |  | lg.Lg2Device / AKB73757604 | irremote: ir_LG.h: Brand: LG,  Model: AKB73757604 remote (LG2 - AKB73757604) |
| lg | AKB73315611  remote | AKB73315611 | remote |  | lg.Lg2Device / AKB74955603 | irremote: ir_LG.h: Brand: LG,  Model: AKB73315611 remote (LG2 - AKB74955603) |
| lg | MS05SQ NW0 | MS05SQ NW0 | unit |  | lg.Lg2Device / AKB74955603 | irremote: ir_LG.h: Brand: LG,  Model: MS05SQ NW0 A/C (LG2 - AKB74955603) |

## Mabe

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| mabe | MMI18HDBWCA6MI8 | MMI18HDBWCA6MI8 | unit |  | haier.Haier176Device / A | irremote: ir_Haier.h: Brand: Mabe,   Model: MMI18HDBWCA6MI8 A/C (HAIER_AC176) |
| mabe | V12843 HJ200223 remote | V12843 HJ200223 | remote |  | haier.Haier176Device / A | irremote: ir_Haier.h: Brand: Mabe,   Model: V12843 HJ200223 remote (HAIER_AC176) |

## Maxell

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| maxell | Maxell MX-CH18CF | MX-CH18CF | unit |  | mirage.MirageDevice / KKG9AC1 | irremote: ir_Mirage.h: Brand: Maxell,  Model: MX-CH18CF A/C |
| maxell | Maxell KKG9A-C1 remote | KKG9A-C1 | remote |  | mirage.MirageDevice / KKG9AC1 | irremote: ir_Mirage.h: Brand: Maxell,  Model: KKG9A-C1 remote |

## Midea

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| coolix | generic | COOLIX protocol | remote |  | coolix.CoolixDevice / None | variant: none (COOLIX) |
| midea | generic | MIDEA protocol | remote |  | midea.MideaDevice / None | variant: none (MIDEA) |
| midea | RG52D/BGE Remote | RG52D/BGE | remote |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Midea, Model: RG52D/BGE Remote |
| midea | MS12FU-10HRDN1-QRD0GW(B) | MS12FU-10HRDN1-QRD0GW(B) | unit |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Midea, Model: MS12FU-10HRDN1-QRD0GW(B) A/C |
| midea | MSABAU-07HRFN1-QRD0GW | MSABAU-07HRFN1-QRD0GW | unit |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Midea, Model: MSABAU-07HRFN1-QRD0GW A/C (circa 2016) |

## Mirage

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| mirage | VLU series | VLU series | unit |  | mirage.MirageDevice / KKG9AC1 | irremote: ir_Mirage.h: Brand: Mirage,  Model: VLU series A/C |
| mirage | generic | MIRAGE KKG9AC1 protocol | remote |  | mirage.MirageDevice / KKG9AC1 | variant: KKG9AC1 |
| mirage | generic 2 | MIRAGE KKG29AC1 protocol | remote |  | mirage.MirageDevice / KKG29AC1 | variant: KKG29AC1 |

## Mitsubishi Electric

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| mitsubishi_electric | MS-GK24VA | MS-GK24VA | unit |  | mitsubishi_electric.MitsubishiAcDevice / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi,  Model: MS-GK24VA A/C |
| mitsubishi_electric | KM14A 0179213 remote | KM14A 0179213 | remote |  | mitsubishi_electric.MitsubishiAcDevice / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi,  Model: KM14A 0179213 remote |
| mitsubishi_electric | PEAD-RP71JAA Ducted | PEAD-RP71JAA | unit |  | mitsubishi_electric.Mitsubishi136Device / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: PEAD-RP71JAA Ducted A/C (MITSUBISHI136) |
| mitsubishi_electric | 001CP T7WE10714 remote | 001CP T7WE10714 | remote |  | mitsubishi_electric.Mitsubishi136Device / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: 001CP T7WE10714 remote (MITSUBISHI136) |
| mitsubishi_electric | MSH-A24WV | MSH-A24WV | unit |  | mitsubishi_electric.Mitsubishi112Device / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: MSH-A24WV A/C (MITSUBISHI112) |
| mitsubishi_electric | MUH-A24WV | MUH-A24WV | unit |  | mitsubishi_electric.Mitsubishi112Device / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: MUH-A24WV A/C (MITSUBISHI112) |
| mitsubishi_electric | KPOA remote | KPOA | remote |  | mitsubishi_electric.Mitsubishi112Device / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: KPOA remote (MITSUBISHI112) |
| mitsubishi_electric | MLZ-RX5017AS | MLZ-RX5017AS | unit |  | mitsubishi_electric.MitsubishiAcDevice / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: MLZ-RX5017AS A/C (MITSUBISHI_AC) |
| mitsubishi_electric | SG153/M21EDF426 remote | SG153/M21EDF426 | remote |  | mitsubishi_electric.MitsubishiAcDevice / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: SG153/M21EDF426 remote (MITSUBISHI_AC) |
| mitsubishi_electric | MSZ-GV2519 | MSZ-GV2519 | unit |  | mitsubishi_electric.MitsubishiAcDevice / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: MSZ-GV2519 A/C (MITSUBISHI_AC) |
| mitsubishi_electric | RH151/M21ED6426 remote | RH151/M21ED6426 | remote |  | mitsubishi_electric.MitsubishiAcDevice / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: RH151/M21ED6426 remote (MITSUBISHI_AC) |
| mitsubishi_electric | MSZ-SF25VE3 | MSZ-SF25VE3 | unit |  | mitsubishi_electric.MitsubishiAcDevice / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: MSZ-SF25VE3 A/C (MITSUBISHI_AC) |
| mitsubishi_electric | SG15D remote | SG15D | remote |  | mitsubishi_electric.MitsubishiAcDevice / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: SG15D remote (MITSUBISHI_AC) |
| mitsubishi_electric | MSZ-ZW4017S | MSZ-ZW4017S | unit |  | mitsubishi_electric.MitsubishiAcDevice / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: MSZ-ZW4017S A/C (MITSUBISHI_AC) |
| mitsubishi_electric | MSZ-FHnnVE | MSZ-FHnnVE | unit |  | mitsubishi_electric.MitsubishiAcDevice / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: MSZ-FHnnVE A/C (MITSUBISHI_AC) |
| mitsubishi_electric | RH151 remote | RH151 | remote |  | mitsubishi_electric.MitsubishiAcDevice / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: RH151 remote (MITSUBISHI_AC) |
| mitsubishi_electric | PAR-FA32MA remote | PAR-FA32MA | remote |  | mitsubishi_electric.Mitsubishi136Device / None | irremote: ir_Mitsubishi.h: Brand: Mitsubishi Electric,  Model: PAR-FA32MA remote (MITSUBISHI136) |
| mitsubishi_electric | generic | MITSUBISHI_AC protocol | remote |  | mitsubishi_electric.MitsubishiAcDevice / None | variant: none (MITSUBISHI_AC) |
| mitsubishi_electric | generic 136 | MITSUBISHI136 protocol | remote |  | mitsubishi_electric.Mitsubishi136Device / None | variant: none (MITSUBISHI136) |
| mitsubishi_electric | generic 112 | MITSUBISHI112 protocol | remote |  | mitsubishi_electric.Mitsubishi112Device / None | variant: none (MITSUBISHI112) |

## Mitsubishi Heavy Industries

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| mitsubishi_heavy_industries | RLA502A700B remote | RLA502A700B | remote |  | mitsubishi_heavy_industries.MitsubishiHeavy152Device / None | irremote: ir_MitsubishiHeavy.h: Brand: Mitsubishi Heavy Industries,  Model: RLA502A700B remote (152 bit) |
| mitsubishi_heavy_industries | SRKxxZM-S A/C | SRKxxZM-S | unit |  | mitsubishi_heavy_industries.MitsubishiHeavy152Device / None | irremote: ir_MitsubishiHeavy.h: Brand: Mitsubishi Heavy Industries,  Model: SRKxxZM-S A/C (152 bit) |
| mitsubishi_heavy_industries | SRKxxZMXA-S A/C | SRKxxZMXA-S | unit |  | mitsubishi_heavy_industries.MitsubishiHeavy152Device / None | irremote: ir_MitsubishiHeavy.h: Brand: Mitsubishi Heavy Industries,  Model: SRKxxZMXA-S A/C (152 bit) |
| mitsubishi_heavy_industries | RKX502A001C remote | RKX502A001C | remote |  | mitsubishi_heavy_industries.MitsubishiHeavy88Device / None | irremote: ir_MitsubishiHeavy.h: Brand: Mitsubishi Heavy Industries,  Model: RKX502A001C remote (88 bit) |
| mitsubishi_heavy_industries | SRKxxZJ-S A/C | SRKxxZJ-S | unit |  | mitsubishi_heavy_industries.MitsubishiHeavy88Device / None | irremote: ir_MitsubishiHeavy.h: Brand: Mitsubishi Heavy Industries,  Model: SRKxxZJ-S A/C (88 bit) |
| mitsubishi_heavy_industries | gemeric | MITSUBISHI_HEAVY_152 protocol | remote |  | mitsubishi_heavy_industries.MitsubishiHeavy152Device / None | variant: none (MITSUBISHI_HEAVY_152) |
| mitsubishi_heavy_industries | gemeric 152 | MITSUBISHI_HEAVY_152 protocol | remote |  | mitsubishi_heavy_industries.MitsubishiHeavy152Device / None | variant: none (MITSUBISHI_HEAVY_152) |
| mitsubishi_heavy_industries | generic 88 | MITSUBISHI_HEAVY_88 protocol | remote |  | mitsubishi_heavy_industries.MitsubishiHeavy88Device / None | variant: none (MITSUBISHI_HEAVY_88) |

## MRCOOL

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| mrcool | RG57A6/BGEFU1 remote | RG57A6/BGEFU1 | remote |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: MrCool,  Model: RG57A6/BGEFU1 remote (MIDEA) |

## Neoclima

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| neoclima | NS-09AHTI | NS-09AHTI | unit |  | neoclima.NeoclimaDevice / None | irremote: ir_Neoclima.h: Brand: Neoclima,  Model: NS-09AHTI A/C |
| neoclima | ZH/TY-01 remote | ZH/TY-01 | remote |  | neoclima.NeoclimaDevice / None | irremote: ir_Neoclima.h: Brand: Neoclima,  Model: ZH/TY-01 remote |
| neoclima | generic | NEOCLIMA protocol | remote |  | neoclima.NeoclimaDevice / None | variant: none (NEOCLIMA) |

## O General

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| fujitsu | General AR-RCL1E remote | AR-RCL1E | remote |  | fujitsu.FujitsuAcDevice / ARRAH2E | irremote: ir_Fujitsu.h: Brand: OGeneral,  Model: AR-RCL1E remote (ARRAH2E) |

## Panasonic

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| panasonic | generic | PANASONIC_NATIVE protocol | remote | yes | legacy:panasonic.Panasonic / None | variant: none (PANASONIC_NATIVE) |
| panasonic | 4 way cassette | 4-Way Cassette | unit | yes | legacy:panasonic.PanaCassette / None | cleaned: '4 way cassette' -> '4-Way Cassette' as Panasonic writes it |
| panasonic | NKE series | NKE series | unit |  | panasonic.PanasonicAcDevice / NKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: NKE series A/C (PANASONIC_AC NKE/2) |
| panasonic | DKE series | DKE series | unit |  | panasonic.PanasonicAcDevice / DKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: DKE series A/C (PANASONIC_AC DKE/3) |
| panasonic | DKW series | DKW series | unit |  | panasonic.PanasonicAcDevice / DKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: DKW series A/C (PANASONIC_AC DKE/3) |
| panasonic | PKR series | PKR series | unit |  | panasonic.PanasonicAcDevice / DKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: PKR series A/C (PANASONIC_AC DKE/3) |
| panasonic | JKE series | JKE series | unit |  | panasonic.PanasonicAcDevice / JKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: JKE series A/C (PANASONIC_AC JKE/4) |
| panasonic | CKP series | CKP series | unit |  | panasonic.PanasonicAcDevice / CKP | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: CKP series A/C (PANASONIC_AC CKP/5) |
| panasonic | RKR series | RKR series | unit |  | panasonic.PanasonicAcDevice / RKR | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: RKR series A/C (PANASONIC_AC RKR/6) |
| panasonic | CS-ME10CKPG | CS-ME10CKPG | unit |  | panasonic.PanasonicAcDevice / CKP | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: CS-ME10CKPG A/C (PANASONIC_AC CKP/5) |
| panasonic | CS-ME12CKPG | CS-ME12CKPG | unit |  | panasonic.PanasonicAcDevice / CKP | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: CS-ME12CKPG A/C (PANASONIC_AC CKP/5) |
| panasonic | CS-ME14CKPG | CS-ME14CKPG | unit |  | panasonic.PanasonicAcDevice / CKP | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: CS-ME14CKPG A/C (PANASONIC_AC CKP/5) |
| panasonic | CS-E7PKR | CS-E7PKR | unit |  | panasonic.PanasonicAcDevice / DKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: CS-E7PKR A/C (PANASONIC_AC DKE/2) |
| panasonic | CS-Z9RKR | CS-Z9RKR | unit |  | panasonic.PanasonicAcDevice / RKR | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: CS-Z9RKR A/C (PANASONIC_AC RKR/6) |
| panasonic | CS-Z24RKR | CS-Z24RKR | unit |  | panasonic.PanasonicAcDevice / RKR | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: CS-Z24RKR A/C (PANASONIC_AC RKR/6) |
| panasonic | CS-YW9MKD | CS-YW9MKD | unit |  | panasonic.PanasonicAcDevice / JKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: CS-YW9MKD A/C (PANASONIC_AC JKE/4) |
| panasonic | CS-E12QKEW | CS-E12QKEW | unit |  | panasonic.PanasonicAcDevice / DKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: CS-E12QKEW A/C (PANASONIC_AC DKE/3) |
| panasonic | A75C2311remote | A75C2311 | remote |  | panasonic.PanasonicAcDevice / CKP | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: A75C2311 remote (PANASONIC_AC CKP/5) |
| panasonic | A75C2616-1remote | A75C2616-1 | remote |  | panasonic.PanasonicAcDevice / DKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: A75C2616-1 remote (PANASONIC_AC DKE/3) |
| panasonic | A75C3704remote | A75C3704 | remote |  | panasonic.PanasonicAcDevice / DKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: A75C3704 remote (PANASONIC_AC DKE/3) |
| panasonic | PN1122Vremote | PN1122V | remote |  | panasonic.PanasonicAcDevice / DKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: PN1122V remote (PANASONIC_AC DKE/3) |
| panasonic | A75C3747remote | A75C3747 | remote |  | panasonic.PanasonicAcDevice / JKE | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: A75C3747 remote (PANASONIC_AC JKE/4) |
| panasonic | CS-E9CKP series | CS-E9CKP series | unit |  | panasonic.PanasonicAc32Device / None | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: CS-E9CKP series A/C (PANASONIC_AC32) |
| panasonic | A75C2295remote | A75C2295 | remote |  | panasonic.PanasonicAc32Device / None | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: A75C2295 remote (PANASONIC_AC32) |
| panasonic | A75C4762remote | A75C4762 | remote |  | panasonic.PanasonicAcDevice / RKR | irremote: ir_Panasonic.h: Brand: Panasonic,  Model: A75C4762 remote (PANASONIC_AC RKR/6) |
| panasonic | generic 32 | PANASONIC_AC32 protocol | remote |  | panasonic.PanasonicAc32Device / None | variant: none (PANASONIC_AC32) |

## Pioneer System

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| pioneer_system | RYBO12GMFILCAD | RYBO12GMFILCAD | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Pioneer System,  Model: RYBO12GMFILCAD A/C (12K BTU) (MIDEA) |
| pioneer_system | RUBO18GMFILCAD | RUBO18GMFILCAD | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Pioneer System,  Model: RUBO18GMFILCAD A/C (18K BTU) (MIDEA) |
| pioneer_system | WS012GMFI22HLD | WS012GMFI22HLD | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Pioneer System,  Model: WS012GMFI22HLD A/C (12K BTU) (MIDEA) |
| pioneer_system | WS018GMFI22HLD | WS018GMFI22HLD | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Pioneer System,  Model: WS018GMFI22HLD A/C (12K BTU) (MIDEA) |
| pioneer_system | UB018GMFILCFHD | UB018GMFILCFHD | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Pioneer System,  Model: UB018GMFILCFHD A/C (12K BTU) (MIDEA) |
| pioneer_system | RG66B6(B)/BGEFU1 remote | RG66B6(B)/BGEFU1 | remote |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Pioneer System,  Model: RG66B6(B)/BGEFU1 remote (MIDEA) |

## Rhoss

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| rhoss | Idrowall MPCV | Idrowall MPCV 20-30-35-40 | unit |  | rhoss.RhossDevice / None | irremote: ir_Rhoss.h: Brand: Rhoss, Model: Idrowall MPCV 20-30-35-40 |
| rhoss | generic | RHOSS protocol | remote |  | rhoss.RhossDevice / None | variant: none (RHOSS) |

## RusClimate

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| rusclimate | EACS/I-09HAR_X/N3 | EACS/I-09HAR_X/N3 | unit |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: RusClimate,  Model: EACS/I-09HAR_X/N3 A/C |
| rusclimate | YAW1F remote | YAW1F | remote |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: RusClimate,  Model: YAW1F remote |

## Samsung

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| samsung | AR09FSSDAWKNFA | AR09FSSDAWKNFA | unit |  | samsung.SamsungAcDevice / None | irremote: ir_Samsung.h: Brand: Samsung,  Model: AR09FSSDAWKNFA A/C (SAMSUNG_AC) |
| samsung | AR09HSFSBWKN | AR09HSFSBWKN | unit |  | samsung.SamsungAcDevice / None | irremote: ir_Samsung.h: Brand: Samsung,  Model: AR09HSFSBWKN A/C (SAMSUNG_AC) |
| samsung | AR12KSFPEWQNET | AR12KSFPEWQNET | unit |  | samsung.SamsungAcDevice / None | irremote: ir_Samsung.h: Brand: Samsung,  Model: AR12KSFPEWQNET A/C (SAMSUNG_AC) |
| samsung | AR12HSSDBWKNEU | AR12HSSDBWKNEU | unit |  | samsung.SamsungAcDevice / None | irremote: ir_Samsung.h: Brand: Samsung,  Model: AR12HSSDBWKNEU A/C (SAMSUNG_AC) |
| samsung | AR12NXCXAWKXEU | AR12NXCXAWKXEU | unit |  | samsung.SamsungAcDevice / None | irremote: ir_Samsung.h: Brand: Samsung,  Model: AR12NXCXAWKXEU A/C (SAMSUNG_AC) |
| samsung | AR12TXEAAWKNEU | AR12TXEAAWKNEU | unit |  | samsung.SamsungAcDevice / None | irremote: ir_Samsung.h: Brand: Samsung,  Model: AR12TXEAAWKNEU A/C (SAMSUNG_AC) |
| samsung | DB93-14195A remote | DB93-14195A | remote |  | samsung.SamsungAcDevice / None | irremote: ir_Samsung.h: Brand: Samsung,  Model: DB93-14195A remote (SAMSUNG_AC) |
| samsung | DB96-24901C remote | DB96-24901C | remote |  | samsung.SamsungAcDevice / None | irremote: ir_Samsung.h: Brand: Samsung,  Model: DB96-24901C remote (SAMSUNG_AC) |
| samsung | generic | SAMSUNG_AC protocol | remote |  | samsung.SamsungAcDevice / None | variant: none (SAMSUNG_AC) |

## Sanyo

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| sanyo | SAP-K121AHA | SAP-K121AHA | unit |  | sanyo.SanyoAcDevice / None | irremote: ir_Sanyo.h: Brand: Sanyo,  Model: SAP-K121AHA A/C (SANYO_AC) |
| sanyo | RCS-2HS4E remote | RCS-2HS4E | remote |  | sanyo.SanyoAcDevice / None | irremote: ir_Sanyo.h: Brand: Sanyo,  Model: RCS-2HS4E remote (SANYO_AC) |
| sanyo | SAP-K242AH | SAP-K242AH | unit |  | sanyo.SanyoAcDevice / None | irremote: ir_Sanyo.h: Brand: Sanyo,  Model: SAP-K242AH A/C (SANYO_AC) |
| sanyo | RCS-2S4E remote | RCS-2S4E | remote |  | sanyo.SanyoAcDevice / None | irremote: ir_Sanyo.h: Brand: Sanyo,  Model: RCS-2S4E remote (SANYO_AC) |
| sanyo | generic | SANYO_AC protocol | remote |  | sanyo.SanyoAcDevice / None | variant: none (SANYO_AC) |
| sanyo | generic 88 | SANYO_AC88 protocol | remote |  | sanyo.SanyoAc88Device / None | variant: none (SANYO_AC88) |

## Sharp

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| sharp | generic | SHARP_NATIVE protocol | remote | yes | legacy:sharp.Sharp / None | variant: none (SHARP_NATIVE) |
| sharp | j-tech | J-Tech | unit | yes | sharp.JTechDevice / None | cleaned: capitalised as Sharp writes it (J-Tech inverter line); the legacy class calls the model 'FTM-PV2S' |
| sharp | YB1FA remote | YB1FA | remote |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Sharp,  Model: YB1FA remote |
| sharp | A5VEY | A5VEY | unit |  | kelvinator.KelvinatorDevice / None | irremote: ir_Kelvinator.h: Brand: Sharp,  Model: A5VEY A/C |
| sharp | Sharp AY-ZP40KR | AY-ZP40KR | unit |  | sharp.SharpAcDevice / A907 | irremote: ir_Sharp.h: Brand: Sharp,  Model: AY-ZP40KR A/C (A907) |
| sharp | AH-AxSAY | AH-AxSAY | unit |  | sharp.SharpAcDevice / A907 | irremote: ir_Sharp.h: Brand: Sharp,  Model: AH-AxSAY A/C (A907) |
| sharp | CRMC-A907 JBEZ remote | CRMC-A907 JBEZ | remote |  | sharp.SharpAcDevice / A907 | irremote: ir_Sharp.h: Brand: Sharp,  Model: CRMC-A907 JBEZ remote (A907) |
| sharp | CRMC-A950 JBEZ | CRMC-A950 JBEZ | remote |  | sharp.SharpAcDevice / A907 | irremote: ir_Sharp.h: Brand: Sharp,  Model: CRMC-A950 JBEZ (A907) |
| sharp | AH-PR13-GL | AH-PR13-GL | unit |  | sharp.SharpAcDevice / A903 | irremote: ir_Sharp.h: Brand: Sharp,  Model: AH-PR13-GL A/C (A903) |
| sharp | CRMC-A903JBEZ remote | CRMC-A903JBEZ | remote |  | sharp.SharpAcDevice / A903 | irremote: ir_Sharp.h: Brand: Sharp,  Model: CRMC-A903JBEZ remote (A903) |
| sharp | AH-XP10NRY | AH-XP10NRY | unit |  | sharp.SharpAcDevice / A903 | irremote: ir_Sharp.h: Brand: Sharp,  Model: AH-XP10NRY A/C (A903) |
| sharp | CRMC-820 JBEZ remote | CRMC-820 JBEZ | remote |  | sharp.SharpAcDevice / A903 | irremote: ir_Sharp.h: Brand: Sharp,  Model: CRMC-820 JBEZ remote (A903) |
| sharp | CRMC-A705 JBEZ remote | CRMC-A705 JBEZ | remote |  | sharp.SharpAcDevice / A705 | irremote: ir_Sharp.h: Brand: Sharp,  Model: CRMC-A705 JBEZ remote (A705) |
| sharp | AH-A12REVP-1 | AH-A12REVP-1 | unit |  | sharp.SharpAcDevice / A903 | irremote: ir_Sharp.h: Brand: Sharp,  Model: AH-A12REVP-1 A/C (A903) |
| sharp | CRMC-A863 JBEZ remote | CRMC-A863 JBEZ | remote |  | sharp.SharpAcDevice / A903 | irremote: ir_Sharp.h: Brand: Sharp,  Model: CRMC-A863 JBEZ remote (A903) |
| sharp | generic A907 | SHARP_AC A907 protocol | remote |  | sharp.SharpAcDevice / A907 | variant: A907 |
| sharp | generic A903 | SHARP_AC A903 protocol | remote |  | sharp.SharpAcDevice / A903 | variant: A903 |
| sharp | generic A705 | SHARP_AC A705 protocol | remote |  | sharp.SharpAcDevice / A705 | variant: A705 |

## Soleus Air

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| soleus | Air window | window | unit |  | gree.GreeDevice / YX1FSF | irremote: ir_Gree.h: Brand: Soleus Air,  Model: window A/C (YX1FSF) |
| soleus | Air TTWM1-10-01 | TTWM1-10-01 | unit |  | neoclima.NeoclimaDevice / None | irremote: ir_Neoclima.h: Brand: Soleus Air,  Model: TTWM1-10-01 A/C |
| soleus | Air ZCF/TL-05 remote | ZCF/TL-05 | remote |  | neoclima.NeoclimaDevice / None | irremote: ir_Neoclima.h: Brand: Soleus Air,  Model: ZCF/TL-05 remote |

## Subtropic

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| subtropic | SUB-07HN1_18Y | SUB-07HN1_18Y | unit |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: Subtropic,  Model: SUB-07HN1_18Y A/C |
| subtropic | YKR-H/102E remote | YKR-H/102E | remote |  | electra.ElectraAcDevice / None | irremote: ir_Electra.h: Brand: Subtropic,  Model: YKR-H/102E remote |

## TCL

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| tcl | TAC-09CHSD/XA31I | TAC-09CHSD/XA31I | unit |  | tcl.Tcl112AcDevice / TAC09CHSD | irremote: ir_Tcl.h: Brand: TCL,  Model: TAC-09CHSD/XA31I A/C (TAC09CHSD) |
| tcl | generic | TCL112AC TAC09CHSD protocol | remote |  | tcl.Tcl112AcDevice / TAC09CHSD | variant: TAC09CHSD |
| tcl | generic v1 | TCL112AC TAC09CHSD protocol | remote |  | tcl.Tcl112AcDevice / TAC09CHSD | variant: TAC09CHSD |
| tcl | generic v2 | TCL112AC GZ055BE1 protocol | remote |  | tcl.Tcl112AcDevice / GZ055BE1 | variant: GZ055BE1 |

## Technibel

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| technibel | IRO PLUS | IRO PLUS | unit |  | technibel.TechnibelAcDevice / technibel | irremote: ir_Technibel.h: Brand: Technibel,  Model: IRO PLUS |
| technibel | generic | TECHNIBEL_AC protocol | remote |  | technibel.TechnibelAcDevice / technibel | variant: none (TECHNIBEL_AC) |

## Teco

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| teco | generic | TECHNIBEL_AC protocol | remote |  | technibel.TechnibelAcDevice / teco | variant: none (TECHNIBEL_AC) |

## Teknopoint

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| technopoint | Allegro SSA-09H | Allegro SSA-09H | unit |  | tcl.Tcl112AcDevice / GZ055BE1 | irremote: ir_Tcl.h: Brand: Teknopoint,  Model: Allegro SSA-09H A/C (GZ055BE1) |
| technopoint | GZ-055B-E1 remote | GZ-055B-E1 | remote |  | tcl.Tcl112AcDevice / GZ055BE1 | irremote: ir_Tcl.h: Brand: Teknopoint,  Model: GZ-055B-E1 remote (GZ055BE1) |

## Tokio

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| tokio | AATOEMF17-12CHR1SW | AATOEMF17-12CHR1SW | unit |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Tokio, Model: AATOEMF17-12CHR1SW split-type RG51\|50/BGE Remote |
| tokio | RG51\|50/BGE Remote | RG51\|50/BGE | remote |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Tokio, Model: AATOEMF17-12CHR1SW split-type RG51\|50/BGE Remote |

## Toshiba

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| toshiba | RAS-B13N3KV2 | RAS-B13N3KV2 | unit |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Toshiba,  Model: RAS-B13N3KV2 |
| toshiba | Akita EVO II | Akita EVO II | unit |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Toshiba,  Model: Akita EVO II |
| toshiba | RAS-B13N3KVP-E | RAS-B13N3KVP-E | unit |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Toshiba,  Model: RAS-B13N3KVP-E |
| toshiba | RAS 18SKP-ES | RAS 18SKP-ES | unit |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Toshiba,  Model: RAS 18SKP-ES |
| toshiba | WH-TA04NE | WH-TA04NE | remote |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Toshiba,  Model: WH-TA04NE |
| toshiba | WC-L03SE | WC-L03SE | remote |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Toshiba,  Model: WC-L03SE |
| toshiba | WH-UB03NJ remote | WH-UB03NJ | remote |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Toshiba,  Model: WH-UB03NJ remote |
| toshiba | RAS-2558V | RAS-2558V | unit |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Toshiba,  Model: RAS-2558V A/C |
| toshiba | WH-TA01JE remote | WH-TA01JE | remote |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Toshiba,  Model: WH-TA01JE remote |
| toshiba | RAS-25SKVP2-ND | RAS-25SKVP2-ND | unit |  | toshiba.ToshibaAcDevice / None | irremote: ir_Toshiba.h: Brand: Toshiba,  Model: RAS-25SKVP2-ND A/C |
| toshiba | generic | TOSHIBA_AC protocol | remote |  | toshiba.ToshibaAcDevice / None | variant: none (TOSHIBA_AC) |
| toshiba | RAS-M10YKV-E | RAS-M10YKV-E | unit |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Toshiba, Model: RAS-M10YKV-E A/C |
| toshiba | RAS-M13YKV-E | RAS-M13YKV-E | unit |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Toshiba, Model: RAS-M13YKV-E A/C |
| toshiba | RAS-4M27YAV-E | RAS-4M27YAV-E | unit |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Toshiba, Model: RAS-4M27YAV-E A/C |
| toshiba | WH-E1YE remote | WH-E1YE | remote |  | coolix.CoolixDevice / None | irremote: ir_Coolix.h: Brand: Toshiba, Model: WH-E1YE remote |

## Transcold

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| transcold | M1-F-NO-6 | M1-F-NO-6 | unit |  | transcold.TranscoldDevice / None | irremote: ir_Transcold.h: Brand: Transcold,  Model: M1-F-NO-6 A/C |
| transcold | generic | TRANSCOLD protocol | remote |  | transcold.TranscoldDevice / None | variant: none (TRANSCOLD) |

## Tronitechnik

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| tronitechnik | Reykir 9000 | Reykir 9000 | unit |  | mirage.MirageDevice / KKG29AC1 | irremote: ir_Mirage.h: Brand: Tronitechnik,  Model: Reykir 9000 A/C |
| tronitechnik | KKG29A-C1 remote | KKG29A-C1 | remote |  | mirage.MirageDevice / KKG29AC1 | irremote: ir_Mirage.h: Brand: Tronitechnik,  Model: KKG29A-C1 remote |

## Trotec

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| trotech | PAC 2100 X | PAC 2100 X | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Trotec,  Model: TROTEC PAC 2100 X (MIDEA) |
| trotech | PAC 3900 X | PAC 3900 X | unit |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Trotec,  Model: TROTEC PAC 3900 X (MIDEA) |
| trotech | RG57H(B)/BGE remote | RG57H(B)/BGE | remote |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Trotec,  Model: RG57H(B)/BGE remote (MIDEA) |
| trotech | RG57H3(B)/BGCEF-M remote | RG57H3(B)/BGCEF-M | remote |  | midea.MideaDevice / None | irremote: ir_Midea.h: Brand: Trotec,  Model: RG57H3(B)/BGCEF-M remote (MIDEA) |
| trotech | PAC 3200 | PAC 3200 | unit |  | trotech.TrotecDevice / None | irremote: ir_Trotec.h: Brand: Trotec,  Model: PAC 3200 A/C (TROTEC) |
| trotech | PAC 3550 Pro | PAC 3550 Pro | unit |  | trotech.Trotec3550Device / None | irremote: ir_Trotec.h: Brand: Trotec,  Model: PAC 3550 Pro A/C (TROTEC_3550) |
| trotech | generic | TROTEC protocol | remote |  | trotech.TrotecDevice / None | variant: none (TROTEC) |
| trotech | generic 3550 | TROTEC_3550 protocol | remote |  | trotech.Trotec3550Device / None | variant: none (TROTEC_3550) |

## Truma

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| truma | Aventa | Aventa | unit |  | truma.TrumaDevice / None | irremote: ir_Truma.h: Brand: Truma,  Model: Aventa A/C |
| truma | 40091-86700 remote | 40091-86700 | remote |  | truma.TrumaDevice / None | irremote: ir_Truma.h: Brand: Truma,  Model: 40091-86700 remote |
| truma | generic | TRUMA protocol | remote |  | truma.TrumaDevice / None | variant: none (TRUMA) |

## Ultimate

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| ultimate | Heat Pump | Heat Pump | unit |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Ultimate,  Model: Heat Pump |

## Vaillant

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| vailland | YACIFB remote | YACIFB | remote |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Vailland,  Model: YACIFB remote |
| vailland | VAI5-035WNI | VAI5-035WNI | unit |  | gree.GreeDevice / YAW1F | irremote: ir_Gree.h: Brand: Vailland,  Model: VAI5-035WNI A/C |

## Vestel

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| vestel | BIOX CXP-9 | BIOX CXP-9 | unit |  | vestel.VestelAcDevice / None | irremote: ir_Vestel.h: Brand: Vestel,  Model: BIOX CXP-9 A/C (9K BTU) |
| vestel | generic | VESTEL_AC protocol | remote |  | vestel.VestelAcDevice / None | variant: none (VESTEL_AC) |

## Voltas

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| voltas | 122LZF 4011252 | 122LZF 4011252 | unit |  | voltas.VoltasDevice / 122LZF | irremote: ir_Voltas.h: Brand: Voltas,  Model: 122LZF 4011252 Window A/C |
| voltas | generic | VOLTAS kVoltasUnknown protocol | remote |  | voltas.VoltasDevice / Unknown | variant: kVoltasUnknown |
| voltas | generic 2 | VOLTAS kVoltas122LZF protocol | remote |  | voltas.VoltasDevice / 122LZF | variant: kVoltas122LZF |

## Whirlpool

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| whirlpool | DG11J1-3A remote | DG11J1-3A | remote |  | whirlpool.WhirlpoolAcDevice / DG11J13A | irremote: ir_Whirlpool.h: Brand: Whirlpool,  Model: DG11J1-3A remote |
| whirlpool | DG11J1-04 remote | DG11J1-04 | remote |  | whirlpool.WhirlpoolAcDevice / DG11J13A | irremote: ir_Whirlpool.h: Brand: Whirlpool,  Model: DG11J1-04 remote |
| whirlpool | DG11J1-91 remote | DG11J1-91 | remote |  | whirlpool.WhirlpoolAcDevice / DG11J191 | irremote: ir_Whirlpool.h: Brand: Whirlpool,  Model: DG11J1-91 remote |
| whirlpool | SPIS409L | SPIS409L | unit |  | whirlpool.WhirlpoolAcDevice / DG11J13A | irremote: ir_Whirlpool.h: Brand: Whirlpool,  Model: SPIS409L A/C |
| whirlpool | SPIS412L | SPIS412L | unit |  | whirlpool.WhirlpoolAcDevice / DG11J13A | irremote: ir_Whirlpool.h: Brand: Whirlpool,  Model: SPIS412L A/C |
| whirlpool | SPIW409L | SPIW409L | unit |  | whirlpool.WhirlpoolAcDevice / DG11J13A | irremote: ir_Whirlpool.h: Brand: Whirlpool,  Model: SPIW409L A/C |
| whirlpool | SPIW412L | SPIW412L | unit |  | whirlpool.WhirlpoolAcDevice / DG11J13A | irremote: ir_Whirlpool.h: Brand: Whirlpool,  Model: SPIW412L A/C |
| whirlpool | SPIW418L | SPIW418L | unit |  | whirlpool.WhirlpoolAcDevice / DG11J13A | irremote: ir_Whirlpool.h: Brand: Whirlpool,  Model: SPIW418L A/C |
| whirlpool | generic | WHIRLPOOL_AC DG11J13A protocol | remote |  | whirlpool.WhirlpoolAcDevice / DG11J13A | variant: DG11J13A |
| whirlpool | generic 2 | WHIRLPOOL_AC DG11J191 protocol | remote |  | whirlpool.WhirlpoolAcDevice / DG11J191 | variant: DG11J191 |

## (dropped)

| old brand | old model | new model | kind | alias | device / variant | source |
|---|---|---|---|---|---|---|
| hitachi | PC-LH3B | - | - |  | legacy:hitachi.Hitachi3 / None | dropped: HITACHI_AC3 (spec section 4) |
| hitachi | generic 3 | - | - |  | legacy:hitachi.Hitachi3 / None | dropped: HITACHI_AC3 (spec section 4) |

# Flags

## Brand corrections (27)

- coolix: 'coolix' is Midea's COOLIX protocol, not a company: its only row ('generic') moves to 'Midea' as 'COOLIX protocol'
- trotech: misspelling: 'trotech' -> 'Trotec' (ir_Trotec.h, ir_Midea.h)
- vailland: 'vailland' (copied from ir_Gree.h 'Vailland') -> 'Vaillant': VAI5-035WNI is Vaillant's climaVAIR VAI 5-035 WN
- technopoint: misspelling: 'technopoint' -> 'Teknopoint' (ir_Tcl.h, TEKNOPOINT protocol name)
- delonghi: 'Delonghi' in the headers -> "De'Longhi" as the company writes it
- ge: header says 'General Electric'; brand written 'GE' as the company brands it
- mrcool: header 'MrCool' -> 'MRCOOL' as the company writes it
- pioneer_system: kept as the header writes it, 'Pioneer System' (the company markets 'Pioneer' mini-splits); alternative 'Pioneer'
- soleus: 'soleus' -> 'Soleus Air' (headers; the old models began with 'Air ')
- fujitsu: rows with a 'General ' model prefix move to brand 'Fujitsu General' (header), AR-RCL1E to 'O General' (header 'OGeneral')
- haier: 'Daichi D-H' moves to brand 'Daichi' (header)
- trotech: 'Duux Blizzard Smart 10K / DXMA04' moves to brand 'Duux' (header)
- carrier: CARRIER_AC64 header lines say 'Carrier/Surrey'; brand kept 'Carrier'
- mitsubishi_electric: MS-GK24VA / KM14A 0179213 header lines say 'Mitsubishi'; brand kept 'Mitsubishi Electric'
- teco: 'Teco' kept as brand; its rows now drive plain TECHNIBEL_AC (spec section 4: 'teco' variant removed, so the variant column's 'teco' becomes None in brands.py)
- alaska: Alaska rows drive plain TECHNIBEL_AC (the 'teco' variant is removed; brands.py variant None)
- green: 'Green' kept (header 'Brand: Green'), distinct from 'Gree'
- ekokai: 'EKOKAI' kept as the header writes it
- fujitsu 'General AR-RCE1E remote': brand from header 'Fujitsu General' (old model carried a 'General ' prefix). Alternative: keep brand 'Fujitsu', strip the prefix
- fujitsu 'General ASHG09LLCA': brand from header 'Fujitsu General' (old model carried a 'General ' prefix). Alternative: keep brand 'Fujitsu', strip the prefix
- fujitsu 'General AOHG09LLC': brand from header 'Fujitsu General' (old model carried a 'General ' prefix). Alternative: keep brand 'Fujitsu', strip the prefix
- fujitsu 'General AR-JW2 remote': brand from header 'Fujitsu General' (old model carried a 'General ' prefix). Alternative: keep brand 'Fujitsu', strip the prefix
- fujitsu 'General AR-RCL1E remote': brand from header 'OGeneral' -> 'O General' (Fujitsu General's brand, written O General). Alternative: 'Fujitsu General'
- fujitsu 'General AR-JW17 remote': brand from header 'Fujitsu General' (old model carried a 'General ' prefix). Alternative: keep brand 'Fujitsu', strip the prefix
- haier 'Daichi D-H': brand corrected: header 'Brand: Daichi, Model: D-H' (was haier 'Daichi D-H')
- soleus 'Air window': brand is 'Soleus Air' (the old models carried 'Air'); header model text is just 'window' (a window unit, not a model code)
- trotech 'Duux Blizzard Smart 10K / DXMA04': brand corrected: header 'Brand: Duux' (was trotech)

## Generic renames (85)

- ALL generic rows get kind 'remote' (they name the protocol/variant a remote sends) and the form '<PROTOCOL> protocol' / '<PROTOCOL> <enumerator> protocol'; daikin 'Daikin', 'Daikin2' ... 'Daikin312' are protocol-named selectors and are treated as generics; legacy rows use the pyhvac *_NATIVE Protocol name
- airspool 'generic' -> 'AIRSPOOL protocol'
- airspool 'airspool' -> 'AIRSPOOL protocol'; the model string repeated the brand; merged with 'generic' (see Merges)
- airton 'generic' -> 'AIRTON protocol'
- airwell 'generic' -> 'AIRWELL protocol'
- amcor 'generic' -> 'AMCOR protocol'
- argo 'generic' -> 'ARGO SAC_WREM2 protocol'
- argo 'generic 2' -> 'ARGO SAC_WREM3 protocol'
- bosch 'generic' -> 'BOSCH144 protocol'
- carrier 'generic' -> 'CARRIER_AC64 protocol'
- coolix 'generic' -> 'COOLIX protocol'; brand 'coolix' is Midea's COOLIX protocol, not a company: the row moves to brand 'Midea'
- corona 'generic' -> 'CORONA_AC protocol'
- daikin 'generic' -> 'DAIKIN_NATIVE protocol'
- daikin 'Daikin' -> 'DAIKIN protocol'
- daikin 'Daikin2' -> 'DAIKIN2 protocol'
- daikin 'Daikin64' -> 'DAIKIN64 protocol'
- daikin 'Daikin128' -> 'DAIKIN128 protocol'
- daikin 'Daikin152' -> 'DAIKIN152 protocol'
- daikin 'Daikin160' -> 'DAIKIN160 protocol'
- daikin 'Daikin176' -> 'DAIKIN176 protocol'
- daikin 'Daikin216' -> 'DAIKIN216 protocol'
- daikin 'Daikin312' -> 'DAIKIN312 protocol'
- delonghi 'generic' -> 'DELONGHI_AC protocol'
- ecoclim 'generic' -> 'ECOCLIM protocol'
- ekokai 'generic' -> 'GREE YAW1F protocol'; header 'EKOKAI, Model: A/C' gives no model text
- electra 'generic' -> 'ELECTRA_AC protocol'
- eurom 'generic' -> 'EUROM protocol'
- fujitsu 'generic' -> 'FUJITSU_AC ARRAH2E protocol'
- fujitsu 'generic 2' -> 'FUJITSU_AC ARDB1 protocol'
- fujitsu 'generic 3' -> 'FUJITSU_AC ARREB1E protocol'
- fujitsu 'generic 4' -> 'FUJITSU_AC ARJW2 protocol'
- fujitsu 'generic 5' -> 'FUJITSU_AC ARRY4 protocol'
- fujitsu 'generic 6' -> 'FUJITSU_AC ARREW4E protocol'
- goodweather 'generic' -> 'GOODWEATHER protocol'
- gree 'gemeric' -> 'GREE YAW1F protocol'
- haier 'generic' -> 'HAIER_AC protocol'
- haier 'YR-W02 Code A' -> 'HAIER_AC_YRW02 V9014557_A protocol'
- haier 'YR-W02 Code B' -> 'HAIER_AC_YRW02 V9014557_B protocol'
- haier 'generic 176 code a' -> 'HAIER_AC176 V9014557_A protocol'
- haier 'generic 176 code b' -> 'HAIER_AC176 V9014557_B protocol'
- haier 'generic 160' -> 'HAIER_AC160 protocol'
- hitachi 'generic' -> 'HITACHI_AC protocol'
- hitachi 'generic 1 code a' -> 'HITACHI_AC1 R_LT0541_HTA_A protocol'
- hitachi 'generic 1 code b' -> 'HITACHI_AC1 R_LT0541_HTA_B protocol'
- hitachi 'generic 424' -> 'HITACHI_AC424 protocol'
- hitachi 'generic 344' -> 'HITACHI_AC344 protocol'
- hitachi 'generic 264' -> 'HITACHI_AC264 protocol'
- hitachi 'generic 296' -> 'HITACHI_AC296 protocol'
- kelvinator 'generic' -> 'KELVINATOR protocol'
- lg 'generic' -> 'LG_NATIVE protocol'
- midea 'generic' -> 'MIDEA protocol'
- mirage 'generic' -> 'MIRAGE KKG9AC1 protocol'
- mirage 'generic 2' -> 'MIRAGE KKG29AC1 protocol'
- mitsubishi_electric 'generic' -> 'MITSUBISHI_AC protocol'
- mitsubishi_electric 'generic 136' -> 'MITSUBISHI136 protocol'
- mitsubishi_electric 'generic 112' -> 'MITSUBISHI112 protocol'
- mitsubishi_heavy_industries 'gemeric' -> 'MITSUBISHI_HEAVY_152 protocol'
- mitsubishi_heavy_industries 'gemeric 152' -> 'MITSUBISHI_HEAVY_152 protocol'
- mitsubishi_heavy_industries 'generic 88' -> 'MITSUBISHI_HEAVY_88 protocol'
- neoclima 'generic' -> 'NEOCLIMA protocol'
- panasonic 'generic' -> 'PANASONIC_NATIVE protocol'
- panasonic 'generic 32' -> 'PANASONIC_AC32 protocol'
- rhoss 'generic' -> 'RHOSS protocol'
- samsung 'generic' -> 'SAMSUNG_AC protocol'
- sanyo 'generic' -> 'SANYO_AC protocol'
- sanyo 'generic 88' -> 'SANYO_AC88 protocol'
- sharp 'generic' -> 'SHARP_NATIVE protocol'
- sharp 'generic A907' -> 'SHARP_AC A907 protocol'
- sharp 'generic A903' -> 'SHARP_AC A903 protocol'
- sharp 'generic A705' -> 'SHARP_AC A705 protocol'
- tcl 'generic' -> 'TCL112AC TAC09CHSD protocol'
- tcl 'generic v1' -> 'TCL112AC TAC09CHSD protocol'
- tcl 'generic v2' -> 'TCL112AC GZ055BE1 protocol'
- technibel 'generic' -> 'TECHNIBEL_AC protocol'
- teco 'generic' -> 'TECHNIBEL_AC protocol'; teco variant is removed by the spec (plain TECHNIBEL_AC): named after TECHNIBEL_AC; brand 'Teco' kept (TECO sells it)
- toshiba 'generic' -> 'TOSHIBA_AC protocol'
- transcold 'generic' -> 'TRANSCOLD protocol'
- trotech 'generic' -> 'TROTEC protocol'
- trotech 'generic 3550' -> 'TROTEC_3550 protocol'
- truma 'generic' -> 'TRUMA protocol'
- vestel 'generic' -> 'VESTEL_AC protocol'
- voltas 'generic' -> 'VOLTAS kVoltasUnknown protocol'
- voltas 'generic 2' -> 'VOLTAS kVoltas122LZF protocol'
- whirlpool 'generic' -> 'WHIRLPOOL_AC DG11J13A protocol'
- whirlpool 'generic 2' -> 'WHIRLPOOL_AC DG11J191 protocol'

## Merges (4)

- airspool 'generic' + airspool 'airspool' -> Airspool 'AIRSPOOL protocol' (same Device airspool.AirspoolDevice, variant None)
- alaska 'SAC9010QC' + alaska 'SAC9010QC remote' -> Alaska 'SAC9010QC' (same Device technibel.TechnibelAcDevice, variant teco)
- mitsubishi_heavy_industries 'gemeric' + mitsubishi_heavy_industries 'gemeric 152' -> Mitsubishi Heavy Industries 'MITSUBISHI_HEAVY_152 protocol' (same Device mitsubishi_heavy_industries.MitsubishiHeavy152Device, variant None)
- tcl 'generic' + tcl 'generic v1' -> TCL 'TCL112AC TAC09CHSD protocol' (same Device tcl.Tcl112AcDevice, variant TAC09CHSD)

## Unknown kinds (26)

- airwell 'DC Series': kind unknown (no header line, no ' remote' suffix): 'unit'
- carrier '53NGK009/012': kind 'unit' (defaulted or inferred; see Model judgement calls)
- daikin 'smash 2': kind 'unit' (defaulted or inferred; see Model judgement calls)
- danby 'DAC080BGUWDB': header line has no A/C/remote word: kind 'unit'
- danby 'DAC100BGUWDB': header line has no A/C/remote word: kind 'unit'
- danby 'DAC120BGUWDB': header line has no A/C/remote word: kind 'unit'
- delonghi 'PAC A95': header line has no A/C/remote word: kind 'unit' (a portable unit)
- delonghi 'PAC EM90': header line has no A/C/remote word (it reads 'Modell:'): kind 'unit' (a portable unit)
- eurom 'Polar 16CH': header line has no A/C/remote word: kind 'unit' (a mobile unit)
- kelon 'remote': kind 'unit' (defaulted or inferred; see Model judgement calls)
- lg 'inverter v': kind 'unit' (defaulted or inferred; see Model judgement calls)
- lg 'dual inverter': kind 'unit' (defaulted or inferred; see Model judgement calls)
- panasonic '4 way cassette': kind 'unit' (defaulted or inferred; see Model judgement calls)
- rhoss 'Idrowall MPCV': kind 'unit' (defaulted or inferred; see Model judgement calls)
- sharp 'j-tech': kind 'unit' (defaulted or inferred; see Model judgement calls)
- sharp 'CRMC-A950 JBEZ': header line has no A/C/remote word; 'remote' inferred from the CRMC-... JBEZ remote code family; the strict rule would give 'unit'
- technibel 'IRO PLUS': header line has no A/C/remote word: kind 'unit'
- toshiba 'RAS-B13N3KV2': header line has no A/C/remote word: kind 'unit'
- toshiba 'Akita EVO II': header line has no A/C/remote word: kind 'unit'
- toshiba 'RAS-B13N3KVP-E': header line has no A/C/remote word: kind 'unit'
- toshiba 'RAS 18SKP-ES': header line has no A/C/remote word: kind 'unit'
- toshiba 'WH-TA04NE': header line has no A/C/remote word; 'remote' inferred from the Toshiba remote code family (WH-/WC-, like WH-UB03NJ remote); the strict rule would give 'unit'
- toshiba 'WC-L03SE': header line has no A/C/remote word; 'remote' inferred from the Toshiba remote code family (WH-/WC-, like WH-UB03NJ remote); the strict rule would give 'unit'
- trotech 'PAC 2100 X': kind 'unit' (defaulted or inferred; see Model judgement calls)
- trotech 'PAC 3900 X': kind 'unit' (defaulted or inferred; see Model judgement calls)
- ultimate 'Heat Pump': kind 'unit' (defaulted or inferred; see Model judgement calls)

## Header descriptors dropped (16)

- argo 'Ulisse 13 DCI': 'Mobile Split' dropped from 'Brand: Argo,  Model: Ulisse 13 DCI Mobile Split A/C [WREM2 remote]'
- argo 'Ulisse Eco Mobile': 'Mobile Split' dropped from 'Brand: Argo,  Model: Ulisse Eco Mobile Split A/C (Wifi) [WREM3 remote]'
- beko 'BINR 070/071': 'split-type' dropped from 'Brand: Beko, Model: BINR 070/071 split-type A/C'
- carrier '53NGK009/012': 'Inverter' dropped from 'Brand: Carrier/Surrey,  Model: 53NGK009/012 Inverter'
- kastron 'RG57A7/BGEF remote': 'Inverter' dropped from 'Brand: Kastron, Model: RG57A7/BGEF Inverter remote'
- lennox 'MCFA': 'indoor split' dropped from 'Brand: Lennox,  Model: MCFA indoor split A/C (MIDEA)'
- lennox 'MCFB': 'indoor split' dropped from 'Brand: Lennox,  Model: MCFB indoor split A/C (MIDEA)'
- lennox 'MMDA': 'indoor split' dropped from 'Brand: Lennox,  Model: MMDA indoor split A/C (MIDEA)'
- lennox 'MMDB': 'indoor split' dropped from 'Brand: Lennox,  Model: MMDB indoor split A/C (MIDEA)'
- lennox 'MWMA': 'indoor split' dropped from 'Brand: Lennox,  Model: MWMA indoor split A/C (MIDEA)'
- lennox 'MWMB': 'indoor split' dropped from 'Brand: Lennox,  Model: MWMB indoor split A/C (MIDEA)'
- lennox 'M22A': 'indoor split' dropped from 'Brand: Lennox,  Model: M22A indoor split A/C (MIDEA)'
- lennox 'M33A': 'indoor split' dropped from 'Brand: Lennox,  Model: M33A indoor split A/C (MIDEA)'
- lennox 'M33B': 'indoor split' dropped from 'Brand: Lennox,  Model: M33B indoor split A/C (MIDEA)'
- mitsubishi_electric 'PEAD-RP71JAA Ducted': 'Ducted' dropped from 'Brand: Mitsubishi Electric,  Model: PEAD-RP71JAA Ducted A/C (MITSUBISHI136)'
- voltas '122LZF 4011252': 'Window' dropped from 'Brand: Voltas,  Model: 122LZF 4011252 Window A/C'

## Model judgement calls (21)

- airspool 'airspool mini-split': airspool 'airspool mini-split' -> 'Mini-split': a product type, no model code known
- airton 'SMVH09B-2A2A3NH': header text 'SMVH09B-2A2A3NH ref. 409730': Airton's article ref 'ref. 409730' dropped, model code kept
- alaska 'SAC9010QC': the unit and remote rows share the model code SAC9010QC (merged, see Merges); merged row kind 'unit'
- argo 'Ulisse Eco Mobile': header 'Ulisse Eco Mobile Split A/C (Wifi) [WREM3 remote]': product name 'Ulisse Eco'; the old string's 'Mobile' goes with the dropped descriptor 'Mobile Split'
- bosch 'B1ZAI2441W': one header line 'B1ZAI2441W/B1ZAO2441W A/C' serves two rows (indoor and outdoor unit); kept as two rows
- carrier '53NGK009/012': header line ends in 'Inverter', not 'A/C': kind 'unit' inferred
- daikin 'smash 2': daikin 'smash 2' -> 'Smash II': Daikin (Malaysia) writes SMASH II; unverified against a remote. Kind 'unit' by default
- daikin 'ARC433 remote': header writes 'ARC433**' (wildcard for the ARC433 family): kept; lookup ignoring punctuation still finds 'ARC433'
- electra 'Classic INV 17': one header line 'Classic INV 17 / AXW12DCS A/C' serves two rows; kept as two
- hitachi 'RF11T1': header says 'RF11T1 remote': kind 'remote' (the old string had no ' remote' suffix)
- kaysun 'Casual CF Alt': 'Casual CF' is listed under both MIDEA and COOLIX; the COOLIX row becomes 'Casual CF (COOLIX)' to keep the two (brand, model) keys apart (old 'Casual CF Alt')
- kelon 'remote': old model string 'remote' is no model; the header's KELON line 'ON/OFF 9000-12000 (KELON)' names the only KELON model: used, kind 'unit' (no A/C/remote word; 9000-12000 BTU units). Alternative: 'KELON protocol'
- lg 'inverter v': lg 'inverter v' -> 'Inverter V' (LG range name, not a model code); kind 'unit' by default
- lg 'dual inverter': lg 'dual inverter' -> 'Dual Inverter' (LG range name, not a model code); kind 'unit' by default
- panasonic '4 way cassette': panasonic '4 way cassette' -> '4-Way Cassette' (a product type; the legacy class says 'PX2T5 and similar'); kind 'unit' by default
- rhoss 'Idrowall MPCV': header 'Idrowall MPCV 20-30-35-40' (no A/C/remote word): model from the header, kind 'unit'
- sharp 'j-tech': sharp 'j-tech': model 'J-Tech' (Sharp's inverter line name); the 0.1.x class names it 'FTM-PV2S', unverified. Kind 'unit' by default
- tokio 'AATOEMF17-12CHR1SW': one header line 'AATOEMF17-12CHR1SW split-type RG51\|50/BGE Remote' names unit and remote; split into a unit row and a remote row
- trotech 'PAC 2100 X': header 'TROTEC PAC 2100 X (MIDEA)': brand prefix dropped; no A/C/remote word: kind 'unit'
- trotech 'PAC 3900 X': header 'TROTEC PAC 3900 X (MIDEA)': brand prefix dropped; no A/C/remote word: kind 'unit'
- ultimate 'Heat Pump': header 'Ultimate, Model: Heat Pump' (no A/C/remote word, not a model code): kept, kind 'unit'
