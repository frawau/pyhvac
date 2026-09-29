# pyhvac

pyhvac generates infrared commands for air conditioners and heat pumps, in
pure Python. Give it a brand, a model and the state you want (power, mode,
setpoint, fan, swing, features); it returns the IR signal, ready for a
Broadlink (or any IR blaster that takes Pronto or raw timings). It decodes
those signals too.

It covers 416 models from 77 brands. Most protocols were ported from
[IRremoteESP8266](https://github.com/crankyoldgit/IRremoteESP8266) and checked
against recordings of what that library sent; the others are pyhvac's own.

Credits for the protocol work go to:
 - Scott Kyle https://gist.github.com/appden/42d5272bf128125b019c45bc2ed3311f
 - mat_fr https://www.instructables.com/id/Reverse-engineering-of-an-Air-Conditioning-control/
 - user two, mathieu, vincent https://www.analysir.com/blog/2014/12/27/reverse-engineering-panasonic-ac-infrared-protocol/
 - all the people who contributed to https://github.com/crankyoldgit/IRremoteESP8266

## Installation

    pip install pyhvac

pyhvac has no dependencies and no compiled code.

## Use

```python
from pyhvac import registry
from pyhvac.ir.formats import to_broadlink
from pyhvac.state import HvacState

device = registry.get_device("Daikin", registry.models("Daikin")[0])
command = device.encode(None, HvacState(True, "cool", 24.0))
packet = to_broadlink(command.signal)  # send it with a Broadlink RM
```

- `registry.brands()` lists the brands, `registry.models(brand)` a brand's
  models. Names are written as the manufacturers write them; lookups ignore
  case, spaces and punctuation (`"mitsubishi_heavy_industries"` finds
  "Mitsubishi Heavy Industries").
- `HvacState(power, mode, temperature, fan="auto", swing_v="off",
  swing_h="off", features={})` is what you want the unit to do. Temperatures
  are in °C.
- `device.encode(previous, target, actions=())` returns a `Command`: its
  `signal` is the IR signal, its `state` the target as the device can
  actually send it (setpoint snapped to the device's range and step, values
  the device lacks replaced by its defaults). Store `command.state` and pass
  it back as `previous` next time: some protocols send a toggle ("power",
  "swing", "light") only when the value changes. `previous=None` means "not
  known", as after a restart.

## Capabilities

`device.capabilities` says what a device can do:

```python
caps = device.capabilities
caps.modes                                   # ("auto", "cool", "dry", ...)
caps.temperature.min, caps.temperature.max   # the setpoint range, °C
caps.fan.values, caps.fan.labels             # canonical values and their labels
caps.swing_v, caps.swing_h                   # Choice or None
caps.features                                # {"powerful": Choice, ...}
```

Canonical values are the same for every device (`"auto"`, `"1"`..`"n"` for
fan speeds or vane positions, `"swing"`, `"off"`); labels are what the
remote calls them (`"lowest"`, `"90°"`, ...). Capabilities offer what the
protocol documents and pyhvac can send, nothing that would do nothing.

## Formats

`pyhvac.ir.formats` turns a signal into a Broadlink packet (`to_broadlink`),
Pronto hex (`to_pronto`) or raw signed microseconds (`to_raw`), and back
(`from_broadlink`, `from_pronto`). `pyhvac.ir.codec.decode(protocol, pulses)`
decodes a captured signal into frames of the device's `PROTOCOL`.

## Command line

    python -m pyhvac --list                      # brands
    python -m pyhvac --list-models Daikin        # a brand's models
    python -m pyhvac Daikin "ARC433**" --mode cool --temperature 24
    python -m pyhvac LG "AKB74955603" --mode heat --fan 2 --format pronto

## Adding a protocol

Protocol code lives in `pyhvac/protocols/`: a `Protocol` (timings, sections)
and a `Device` subclass whose `frames()` builds the frames with a `Layout`
(`pyhvac.fields`). `tools/portkit.py` helps derive timings, fields and
checksums from captures. Register the models in `pyhvac/brands.py`.

## Migrating from 0.1.x

| 0.1.x | 0.2.0 |
|---|---|
| `importlib.import_module(f"pyhvac.plugins.{brand}").PluginObject().get_device(model)` | `registry.get_device(brand, model)` |
| `dev.set_value("mode", "cool")`, `set_value("temperature", 24)`, ... | `HvacState(power=True, mode="cool", temperature=24.0, fan=..., swing_v=..., features={...})` |
| `frames = dev.build_ircode(); dev.to_broadlink(frames)` | `to_broadlink(device.encode(previous, state).signal)` |
| `dev.capabilities["temperature"]`, `dev.all_capabilities["fan"]` | `device.capabilities.temperature`, `device.capabilities.fan` (values and labels) |
| brand = plugin module name, e.g. `"mitsubishi_heavy_industries"` | brand as the maker writes it; lookups ignore case and punctuation |
| model strings of 0.1.x | the new names below; 0.1.x names still work for the former pure-Python devices (Daikin, LG and Panasonic "generic" and their variants, Airspool, Sharp "j-tech") |

The full old -> new name table is in
`docs/superpowers/plans/2026-09-29-phase4/tables/names.md`.

## Supported models

- **AEG**: Chillflex Pro AXP26U338CW
- **Airspool**: AIRSPOOL protocol (remote), Mini-split
- **Airton**: AIRTON protocol (remote), RD1A1 (remote), SMVH09B-2A2A3NH
- **Airwell**: AIRWELL protocol (remote), DC Series, RC04 (remote), RC08B (remote), RC08W (remote)
- **Alaska**: SAC9010QC
- **Amana**: PBC093G00CC, YX1FF (remote)
- **Amcor**: ADR-853H, AMCOR protocol (remote), TAC-444 (remote), TAC-495 (remote)
- **Argo**: ARGO SAC_WREM2 protocol (remote), ARGO SAC_WREM3 protocol (remote), Ulisse 13 DCI, Ulisse Eco, WREM2 (remote), WREM3 (remote)
- **AUX**: KFR-35GW/BpNFW=3, YKR-T/011 (remote)
- **Beko**: BINR 070/071, RG57K7(B)/BGEF (remote)
- **Bosch**: B1ZAI2441W, B1ZAO2441W, BOSCH144 protocol (remote), CL3000i-Set 26 E, RG10A(G2S)BGEF (remote), RG36B4/BGE (remote)
- **Carrier**: 42NQV025M2 / 38NYV025M2, 42NQV035M2 / 38NYV035M2, 42NQV050M2 / 38NYV050M2, 42NQV060M2 / 38NYV060M2, 42QG5A55970 (remote), 53NGK009/012, 619EGX0090E0, 619EGX0120E0, 619EGX0180E0, 619EGX0220E0, CARRIER_AC64 protocol (remote)
- **Centek**: SCT-65Q09, YKR-P/002E (remote)
- **Comfee**: MPD1-12CRN7
- **Cooper & Hunter**: CH-S09FTXG, YB1F2 (remote)
- **Corona**: AR-01 (remote), CORONA_AC protocol (remote), CSH-N2211, CSH-N2511, CSH-N2811, CSH-N4011
- **Daewoo**: DSB-F0934ELH-V, GYKQ-52E (remote)
- **Daichi**: D-H
- **Daikin**: 17 Series FTXB09AXVJU, 17 Series FTXB12AXVJU, 17 Series FTXB24AXVJU, ARC423A5 (remote), ARC433** (remote), ARC433B69 (remote), ARC466A12 (remote), ARC466A33 (remote), ARC466A67 (remote), ARC477A1 (remote), ARC480A5 (remote), ARC484A4 (remote), BRC4C151 (remote), BRC4C153 (remote), BRC52B63 (remote), DAIKIN protocol (remote), DAIKIN128 protocol (remote), DAIKIN152 protocol (remote), DAIKIN160 protocol (remote), DAIKIN176 protocol (remote), DAIKIN2 protocol (remote), DAIKIN216 protocol (remote), DAIKIN312 protocol (remote), DAIKIN64 protocol (remote), DAIKIN_NATIVE protocol (remote), DGS01 (remote), FFN-C/FCN-F Series, FFQ35B8V1B, FTE12HV2S, FTQ60TV16U2, FTWX35AXV1, FTXM-M, FTXM20R5V1B, FTXZ25NV1B, FTXZ35NV1B, FTXZ50NV1B, M Series, Smash II
- **Danby**: DAC080BGUWDB, DAC100BGUWDB, DAC120BGUWDB, R09C/BCGE (remote)
- **De'Longhi**: DELONGHI_AC protocol (remote), PAC A95, PAC EM90
- **Duux**: Blizzard Smart 10K / DXMA04
- **EcoClim**: ECOCLIM protocol (remote), HYSFR-P348 (remote), ZC200DPO
- **EKOKAI**: GREE YAW1F protocol (remote)
- **Electra**: AXW12DCS, Classic INV 17, ELECTRA_AC protocol (remote), YKR-M/003E (remote)
- **Electrolux**: YKR-H/531E
- **Eurom**: EUROM protocol (remote), Polar 16CH
- **Frigidaire**: FGPC102AB1
- **Fujitsu**: AGTV14LAC, AR-DB1 (remote), AR-DL10 (remote), AR-RAC1E (remote), AR-RAE1E (remote), AR-RAH1U (remote), AR-RAH2E (remote), AR-RAH2U (remote), AR-REB1E (remote), AR-REB4E (remote), AR-REG1U (remote), AR-REW1E (remote), AR-REW4E (remote), AR-RY4 (remote), AST9RSGCW, ASTB09LBC, ASTG09K, ASTG18K, ASU12RLF, ASU30C1, ASYG09KETA-B, ASYG30LFCA, ASYG7LMCA, FUJITSU_AC ARDB1 protocol (remote), FUJITSU_AC ARJW2 protocol (remote), FUJITSU_AC ARRAH2E protocol (remote), FUJITSU_AC ARREB1E protocol (remote), FUJITSU_AC ARREW4E protocol (remote), FUJITSU_AC ARRY4 protocol (remote)
- **Fujitsu General**: AOHG09LLC, AR-JW17 (remote), AR-JW2 (remote), AR-RCE1E (remote), ASHG09LLCA
- **GE**: 6711AR2853M (remote), AG1BH09AW101
- **Goodweather**: GOODWEATHER protocol (remote), ZH/JT-03 (remote)
- **Gree**: GREE YAW1F protocol (remote), VIR09HP115V1AH, VIR12HP230V1AH, YAA1FBF (remote), YAN1F1 (remote), YAP0F8 (remote), YAPOF3 (remote), YB1F2F (remote), YX1F2F (remote)
- **Green**: YBOFB (remote), YBOFB2 (remote)
- **Haier**: HAIER_AC protocol (remote), HAIER_AC160 protocol (remote), HAIER_AC176 V9014557_A protocol (remote), HAIER_AC176 V9014557_B protocol (remote), HAIER_AC_YRW02 V9014557_A protocol (remote), HAIER_AC_YRW02 V9014557_B protocol (remote), HSU-09HMC203, HSU07-HEA03 (remote), KFR-26GW/83@UI-Ge, V9014557 M47 8D (remote), YR-W02 (remote)
- **Hitachi**: HITACHI_AC protocol (remote), HITACHI_AC1 R_LT0541_HTA_A protocol (remote), HITACHI_AC1 R_LT0541_HTA_B protocol (remote), HITACHI_AC264 protocol (remote), HITACHI_AC296 protocol (remote), HITACHI_AC344 protocol (remote), HITACHI_AC424 protocol (remote), KAZE-312KSDP, LT0541-HTA (remote), R-LT0541-HTA/Y.K.1.1-1 V2.3 (remote), RAK-25NH5, RAR-2P2 (remote), RAR-3U3 (remote), RAR-8P2 (remote), RAS-22NK, RAS-35THA6 (remote), RAS-70YHA3, RAS-AJ25H, RF11T1 (remote), Series VI
- **Kastron**: RG57A7/BGEF (remote)
- **Kaysun**: Casual CF, Casual CF (COOLIX)
- **Kelon**: ON/OFF 9000-12000
- **Kelvinator**: KELVINATOR protocol (remote), KSV26CRC, KSV26HRC, KSV35CRC, KSV35HRC, KSV53HRC, KSV62HRC, KSV70CRC, KSV70HRC, KSV80HRC, YALIF (remote)
- **Keystone**: RG57H4(B)BGEF (remote)
- **Leberg**: LBS-TOR07
- **Lennox**: M22A, M33A, M33B, MCFA, MCFB, MMDA, MMDB, MWMA, MWMA009S4-3P, MWMA012S4-3P, MWMB, RG57A6/BGEFU1 (remote)
- **LG**: 6711A20083V (remote), A4UW30GFA2, AKB73315611 (remote), AKB73757604 (remote), AKB74395308 (remote), AKB74955603 (remote), AKB75215403 (remote), AMNW09GSJA0, AMNW24GTPA1, Dual Inverter, Inverter V, LG_NATIVE protocol (remote), MS05SQ NW0, S4-W12JA3AA, TS-H122ERM1 (remote)
- **Mabe**: MMI18HDBWCA6MI8, V12843 HJ200223 (remote)
- **Maxell**: KKG9A-C1 (remote), MX-CH18CF
- **Midea**: COOLIX protocol (remote), MIDEA protocol (remote), MS12FU-10HRDN1-QRD0GW(B), MSABAU-07HRFN1-QRD0GW, RG52D/BGE (remote)
- **Mirage**: MIRAGE KKG29AC1 protocol (remote), MIRAGE KKG9AC1 protocol (remote), VLU series
- **Mitsubishi Electric**: 001CP T7WE10714 (remote), KM14A 0179213 (remote), KPOA (remote), MITSUBISHI112 protocol (remote), MITSUBISHI136 protocol (remote), MITSUBISHI_AC protocol (remote), MLZ-RX5017AS, MS-GK24VA, MSH-A24WV, MSZ-FHnnVE, MSZ-GV2519, MSZ-SF25VE3, MSZ-ZW4017S, MUH-A24WV, PAR-FA32MA (remote), PEAD-RP71JAA, RH151 (remote), RH151/M21ED6426 (remote), SG153/M21EDF426 (remote), SG15D (remote)
- **Mitsubishi Heavy Industries**: MITSUBISHI_HEAVY_152 protocol (remote), MITSUBISHI_HEAVY_88 protocol (remote), RKX502A001C (remote), RLA502A700B (remote), SRKxxZJ-S, SRKxxZM-S, SRKxxZMXA-S
- **MRCOOL**: RG57A6/BGEFU1 (remote)
- **Neoclima**: NEOCLIMA protocol (remote), NS-09AHTI, ZH/TY-01 (remote)
- **O General**: AR-RCL1E (remote)
- **Panasonic**: 4-Way Cassette, A75C2295 (remote), A75C2311 (remote), A75C2616-1 (remote), A75C3704 (remote), A75C3747 (remote), A75C4762 (remote), CKP series, CS-E12QKEW, CS-E7PKR, CS-E9CKP series, CS-ME10CKPG, CS-ME12CKPG, CS-ME14CKPG, CS-YW9MKD, CS-Z24RKR, CS-Z9RKR, DKE series, DKW series, JKE series, NKE series, PANASONIC_AC32 protocol (remote), PANASONIC_NATIVE protocol (remote), PKR series, PN1122V (remote), RKR series
- **Pioneer System**: RG66B6(B)/BGEFU1 (remote), RUBO18GMFILCAD, RYBO12GMFILCAD, UB018GMFILCFHD, WS012GMFI22HLD, WS018GMFI22HLD
- **Rhoss**: Idrowall MPCV 20-30-35-40, RHOSS protocol (remote)
- **RusClimate**: EACS/I-09HAR_X/N3, YAW1F (remote)
- **Samsung**: AR09FSSDAWKNFA, AR09HSFSBWKN, AR12HSSDBWKNEU, AR12KSFPEWQNET, AR12NXCXAWKXEU, AR12TXEAAWKNEU, DB93-14195A (remote), DB96-24901C (remote), SAMSUNG_AC protocol (remote)
- **Sanyo**: RCS-2HS4E (remote), RCS-2S4E (remote), SANYO_AC protocol (remote), SANYO_AC88 protocol (remote), SAP-K121AHA, SAP-K242AH
- **Sharp**: A5VEY, AH-A12REVP-1, AH-AxSAY, AH-PR13-GL, AH-XP10NRY, AY-ZP40KR, CRMC-820 JBEZ (remote), CRMC-A705 JBEZ (remote), CRMC-A863 JBEZ (remote), CRMC-A903JBEZ (remote), CRMC-A907 JBEZ (remote), CRMC-A950 JBEZ (remote), J-Tech, SHARP_AC A705 protocol (remote), SHARP_AC A903 protocol (remote), SHARP_AC A907 protocol (remote), YB1FA (remote)
- **Soleus Air**: TTWM1-10-01, window, ZCF/TL-05 (remote)
- **Subtropic**: SUB-07HN1_18Y, YKR-H/102E (remote)
- **TCL**: TAC-09CHSD/XA31I, TCL112AC GZ055BE1 protocol (remote), TCL112AC TAC09CHSD protocol (remote)
- **Technibel**: IRO PLUS, TECHNIBEL_AC protocol (remote)
- **Teco**: TECHNIBEL_AC protocol (remote)
- **Teknopoint**: Allegro SSA-09H, GZ-055B-E1 (remote)
- **Tokio**: AATOEMF17-12CHR1SW, RG51|50/BGE (remote)
- **Toshiba**: Akita EVO II, RAS 18SKP-ES, RAS-2558V, RAS-25SKVP2-ND, RAS-4M27YAV-E, RAS-B13N3KV2, RAS-B13N3KVP-E, RAS-M10YKV-E, RAS-M13YKV-E, TOSHIBA_AC protocol (remote), WC-L03SE (remote), WH-E1YE (remote), WH-TA01JE (remote), WH-TA04NE (remote), WH-UB03NJ (remote)
- **Transcold**: M1-F-NO-6, TRANSCOLD protocol (remote)
- **Tronitechnik**: KKG29A-C1 (remote), Reykir 9000
- **Trotec**: PAC 2100 X, PAC 3200, PAC 3550 Pro, PAC 3900 X, RG57H(B)/BGE (remote), RG57H3(B)/BGCEF-M (remote), TROTEC protocol (remote), TROTEC_3550 protocol (remote)
- **Truma**: 40091-86700 (remote), Aventa, TRUMA protocol (remote)
- **Ultimate**: Heat Pump
- **Vaillant**: VAI5-035WNI, YACIFB (remote)
- **Vestel**: BIOX CXP-9, VESTEL_AC protocol (remote)
- **Voltas**: 122LZF 4011252, VOLTAS kVoltas122LZF protocol (remote), VOLTAS kVoltasUnknown protocol (remote)
- **Whirlpool**: DG11J1-04 (remote), DG11J1-3A (remote), DG11J1-91 (remote), SPIS409L, SPIS412L, SPIW409L, SPIW412L, SPIW418L, WHIRLPOOL_AC DG11J13A protocol (remote), WHIRLPOOL_AC DG11J191 protocol (remote)
