# pyhvac

THIS IS WORK IN PROGRESS

LG is not tested. "auto" mode for Sharp J-Tech is flaky

Although most of the devices associated with IRremoteESP8266 seems to produce reasonable
output, this has, obviously, not been checked.


pyhvac is a Python 3 library/utility to generate IR code for A/C device.


This library uses code/work from:
 - Scott Kyle https://gist.github.com/appden/42d5272bf128125b019c45bc2ed3311f
 - mat_fr     https://www.instructables.com/id/Reverse-engineering-of-an-Air-Conditioning-control/
 - user two, mathieu, vincent https://www.analysir.com/blog/2014/12/27/reverse-engineering-panasonic-ac-infrared-protocol/
 - all the people who contributed to https://github.com/crankyoldgit/IRremoteESP8266

# Installation

We are on PyPi so

     pip3 install pyhvac
     or
     python3 -m pip install pyhvac

     After installation, the utility

     gaccode, gcpanasonic, gcdaikin, gclg, gcsharp

     can be used to generate codes. Use the -h option for help.

     Note that the utilities cannot fully excercise all the capabilities of their respective plugin.
     For instance, the code for a Sharp A/C can depend on the state of the device. gcsharp does not keep track of the
     state of the device.

# Supported IR codes

With the inclusion of the library from IRremoteESP8266 there is a lot of supported A/C. :

- aeg
  - Chillflex Pro AXP26U338CW
- airton
  - SMVH09B-2A2A3NH
  - RD1A1
  - generic
- airwell
  - DC Series
  - RC08W remote
  - RC04 remote
  - generic
  - RC08B remote
- alaska
  - SAC9010QC
  - SAC9010QC remote
- amana
  - PBC093G00CC
  - YX1FF remote
- amcor
  - ADR-853H
  - TAC-495 remote
  - TAC-444 remote
  - generic
- argo
  - Ulisse 13 DCI
  - WREM2 remote
  - Ulisse Eco Mobile
  - WREM3 remote
  - generic
  - generic 2
- aux
  - KFR-35GW/BpNFW=3
  - YKR-T/011 remote
- beko
  - RG57K7(B)/BGEF Remote
  - BINR 070/071
- bosch
  - CL3000i-Set 26 E
  - RG10A(G2S)BGEF remote
  - generic
  - RG36B4/BGE remote
  - B1ZAI2441W
  - B1ZAO2441W
- carrier
  - 42QG5A55970 remote
  - 619EGX0090E0
  - 619EGX0120E0
  - 619EGX0180E0
  - 619EGX0220E0
  - 53NGK009/012
  - generic
  - 42NQV060M2 / 38NYV060M2
  - 42NQV050M2 / 38NYV050M2
  - 42NQV035M2 / 38NYV035M2
  - 42NQV025M2 / 38NYV025M2
- centek
  - SCT-65Q09
  - YKR-P/002E remote
- comfee
  - MPD1-12CRN7
- coolix
  - generic
- cooper & hunter: YB1F2 remote
  - CH-S09FTXG
- corona
  - CSH-N2211
  - CSH-N2511
  - CSH-N2811
  - CSH-N4011
  - AR-01 remote
  - generic
- daewoo
  - DSB-F0934ELH-V
  - GYKQ-52E remote
- daikin
  - generic
  - smash 2
  - ARC433 remote
  - ARC477A1 remote
  - FTXZ25NV1B
  - FTXZ35NV1B
  - FTXZ50NV1B
  - ARC433B69 remote
  - ARC423A5 remote
  - FTE12HV2S
  - BRC4C153 remote
  - FFQ35B8V1B
  - BRC4C151 remote
  - 17 Series FTXB09AXVJU
  - 17 Series FTXB12AXVJU
  - 17 Series FTXB24AXVJU
  - BRC52B63 remote
  - ARC480A5 remote
  - FFN-C/FCN-F Series
  - DGS01 remote
  - M Series
  - FTXM-M
  - ARC466A12 remote
  - ARC466A33 remote
  - FTWX35AXV1
  - ARC484A4 remote
  - FTQ60TV16U2
  - Daikin
  - Daikin2
  - Daikin64
  - Daikin128
  - Daikin152
  - Daikin160
  - Daikin176
  - Daikin216
- danby
  - DAC080BGUWDB
  - DAC100BGUWDB
  - DAC120BGUWDB
  - R09C/BCGE remote
- delonghi
  - PAC A95
  - generic
  - PAC EM90
- ecoclim
  - HYSFR-P348 remote
  - ZC200DPO
  - generic
- ekokai
  - generic
- electra
  - Classic INV 17
  - AXW12DCS
  - YKR-M/003E remote
  - generic
- electrolux
  - YKR-H/531E
- frigidaire
  - FGPC102AB1
- fujitsu
  - AR-RAH2E remote
  - ASYG30LFCA
  - General AR-RCE1E remote
  - General ASHG09LLCA
  - General AOHG09LLC
  - AR-DB1 remote
  - AST9RSGCW
  - AR-REB1E remote
  - ASYG7LMCA
  - AR-RAE1E remote
  - AGTV14LAC
  - AR-RAC1E remote
  - ASTB09LBC
  - AR-RY4 remote
  - General AR-JW2 remote
  - AR-DL10 remote
  - ASU30C1
  - AR-RAH1U remote
  - AR-RAH2U remote
  - ASU12RLF
  - AR-REW4E remote
  - ASYG09KETA-B
  - AR-REB4E remote
  - ASTG09K
  - ASTG18K
  - AR-REW1E remote
  - AR-REG1U remote
  - General AR-RCL1E remote
  - General AR-JW17 remote
  - generic
  - generic 2
  - generic 3
  - generic 4
  - generic 5
  - generic 6
- ge
  - AG1BH09AW101
  - 6711AR2853M Remote
- goodweather
  - ZH/JT-03 remote
  - generic
- gree
  - YAA1FBF remote
  - YB1F2F remote
  - YAN1F1 remote
  - YX1F2F remote
  - VIR09HP115V1AH
  - VIR12HP230V1AH
  - gemeric
  - YAPOF3 remote
  - YAP0F8 remote
- green
  - YBOFB remote
  - YBOFB2 remote
- haier
  - HSU07-HEA03 remote
  - YR-W02 remote
  - HSU-09HMC203
  - V9014557 M47 8D remote
  - Daichi D-H
  - KFR-26GW/83@UI-Ge
  - generic
  - YR-W02 Code A
  - YR-W02 Code B
  - generic 176 code a
  - generic 176 code b
  - generic 160
- hitachi
  - RAS-35THA6 remote
  - LT0541-HTA remote
  - Series VI
  - RAR-8P2 remote
  - RAS-AJ25H
  - PC-LH3B
  - KAZE-312KSDP
  - R-LT0541-HTA/Y.K.1.1-1 V2.3 remote
  - RAS-22NK
  - RF11T1
  - RAR-2P2 remote
  - RAK-25NH5
  - RAR-3U3 remote
  - RAS-70YHA3
  - generic
  - generic 1 code a
  - generic 1 code b
  - generic 424
  - generic 3
  - generic 344
  - generic 264
  - generic 296
- kastron
  - RG57A7/BGEF remote
- kaysun
  - Casual CF
  - Casual CF Alt
- kelon
  - remote
- kelvinator
  - YALIF remote
  - KSV26CRC
  - KSV26HRC
  - KSV35CRC
  - KSV35HRC
  - KSV53HRC
  - KSV62HRC
  - KSV70CRC
  - KSV70HRC
  - KSV80HRC
  - generic
- keystone
  - RG57H4(B)BGEF remote
- leberg
  - LBS-TOR07
- lennox
  - RG57A6/BGEFU1 remote
  - MWMA009S4-3P
  - MWMA012S4-3P
  - MCFA
  - MCFB
  - MMDA
  - MMDB
  - MWMA
  - MWMB
  - M22A
  - M33A
  - M33B
- lg
  - generic
  - inverter v
  - dual inverter
  - 6711A20083V  remote
  - TS-H122ERM1  remote
  - AKB74395308  remote
  - S4-W12JA3AA
  - AKB75215403  remote
  - AKB74955603  remote
  - A4UW30GFA2
  - AMNW09GSJA0
  - AMNW24GTPA1
  - AKB73757604  remote
  - AKB73315611  remote
  - MS05SQ NW0
- mabe
  - MMI18HDBWCA6MI8
  - V12843 HJ200223 remote
- maxell
  - Maxell MX-CH18CF
  - Maxell KKG9A-C1 remote
- midea
  - generic
  - RG52D/BGE Remote
  - MS12FU-10HRDN1-QRD0GW(B)
  - MSABAU-07HRFN1-QRD0GW
- mirage
  - VLU series
  - generic
  - generic 2
- mitsubishi electric
  - MS-GK24VA
  - KM14A 0179213 remote
  - PEAD-RP71JAA Ducted
  - 001CP T7WE10714 remote
  - MSH-A24WV
  - MUH-A24WV
  - KPOA remote
  - MLZ-RX5017AS
  - SG153/M21EDF426 remote
  - MSZ-GV2519
  - RH151/M21ED6426 remote
  - MSZ-SF25VE3
  - SG15D remote
  - MSZ-ZW4017S
  - MSZ-FHnnVE
  - RH151 remote
  - PAR-FA32MA remote
  - generic
  - generic 136
  - generic 112
- mitsubishi heavy industries
  - RLA502A700B remote
  - SRKxxZM-S A/C
  - SRKxxZMXA-S A/C
  - RKX502A001C remote
  - SRKxxZJ-S A/C
  - gemeric
  - gemeric 152
  - generic 88
- mr cool
  - RG57A6/BGEFU1 remote
- neoclima
  - NS-09AHTI
  - ZH/TY-01 remote
  - generic
- panasonic
  - generic
  - 4 way cassette
  - NKE series
  - DKE series
  - DKW series
  - PKR series
  - JKE series
  - CKP series
  - RKR series
  - CS-ME10CKPG
  - CS-ME12CKPG
  - CS-ME14CKPG
  - CS-E7PKR
  - CS-Z9RKR
  - CS-Z24RKR
  - CS-YW9MKD
  - CS-E12QKEW
  - A75C2311remote
  - A75C2616-1remote
  - A75C3704remote
  - PN1122Vremote
  - A75C3747remote
  - CS-E9CKP series
  - A75C2295remote
  - A75C4762remote
  - generic 32
- pioneer system: RYBO12GMFILCAD
  - RUBO18GMFILCAD
  - WS012GMFI22HLD
  - WS018GMFI22HLD
  - UB018GMFILCFHD
  - RG66B6(B)/BGEFU1 remote
- rhoss
  - Idrowall MPCV
  - generic
- rusclimate
  - EACS/I-09HAR_X/N3
  - YAW1F remote
- samsung
  - AR09FSSDAWKNFA
  - AR09HSFSBWKN
  - AR12KSFPEWQNET
  - AR12HSSDBWKNEU
  - AR12NXCXAWKXEU
  - AR12TXEAAWKNEU
  - DB93-14195A remote
  - DB96-24901C remote
  - generic
- sanyo
  - SAP-K121AHA
  - RCS-2HS4E remote
  - SAP-K242AH
  - RCS-2S4E remote
  - generic
  - generic 88
- sharp
  - generic
  - j-tech
  - YB1FA remote
  - A5VEY
  - Sharp AY-ZP40KR
  - AH-AxSAY
  - CRMC-A907 JBEZ remote
  - CRMC-A950 JBEZ
  - AH-PR13-GL
  - CRMC-A903JBEZ remote
  - AH-XP10NRY
  - CRMC-820 JBEZ remote
  - CRMC-A705 JBEZ remote
  - AH-A12REVP-1
  - CRMC-A863 JBEZ remote
  - generic A907
  - generic A903
  - generic A705
- soleus
  - Air window
  - Air TTWM1-10-01
  - Air ZCF/TL-05 remote
- subtropic
  - SUB-07HN1_18Y
  - YKR-H/102E remote
- tcl
  - TAC-09CHSD/XA31I
  - generic
  - generic v1
  - generic v2
- technibel
  - IRO PLUS
  - generic
- technopoint
  - Allegro SSA-09H
  - GZ-055B-E1 remote
- teco
  - generic
- tokio
  - AATOEMF17-12CHR1SW
  - RG51|50/BGE Remote
- toshiba
  - RAS-B13N3KV2
  - Akita EVO II
  - RAS-B13N3KVP-E
  - RAS 18SKP-ES
  - WH-TA04NE
  - WC-L03SE
  - WH-UB03NJ remote
  - RAS-2558V
  - WH-TA01JE remote
  - RAS-25SKVP2-ND
  - generic
  - RAS-M10YKV-E
  - RAS-M13YKV-E
  - RAS-4M27YAV-E
  - WH-E1YE remote
- transcold
  - M1-F-NO-6
  - generic
- tronitechnik
  - Reykir 9000
  - KKG29A-C1 remote
- trotech
  - PAC 2100 X
  - PAC 3900 X
  - RG57H(B)/BGE remote
  - RG57H3(B)/BGCEF-M remote
  - PAC 3200
  - PAC 3550 Pro
  - Duux Blizzard Smart 10K / DXMA04
  - generic
  - generic 3550
- truma
  - Aventa
  - 40091-86700 remote
  - generic
- ultimate
  - Heat Pump
- vailland
  - YACIFB remote
  - VAI5-035WNI
- vestel
  - BIOX CXP-9
  - generic
- voltas
  - 122LZF 4011252
  - generic
  - generic 2
- whirlpool
  - DG11J1-3A remote
  - DG11J1-04 remote
  - DG11J1-91 remote
  - SPIS409L
  - SPIS412L
  - SPIW409L
  - SPIW412L
  - SPIW418L
  - generic
  - generic 2

# Library

pyhvac uses plugin to add support.

Each plugin file must have a

       PluginObject

class that must have a "get_device" method to return HVAC objects, a 'brand' attribute
and a 'models' attribute containing a dictionary matching models to objects. Note that brand and models MUST BE lowercased.

Each HVAC object describes a specific way of generating codes for IR transmission.

The codes should be returned as a list of bytes in either lsb or msb format. The
HVAC object must have its "is_msb" attribute set to False or True accordingly.

All HVAC objects are required to have at the minimum 2 capabilities:

    mode   with at least "off" and another value ("auto", "cool", ....)
    temperature  with the accepted range

Other capabilities are expected.

To simplify things, it is requested that some sort of normalization
of function names occur. In most cases an AC unit will have the following

    mode: the operating mode. Values are expected to be amongst
          "off"   turned off (This is mandatory)
          "auto"  automatic mode sometines known as "feel", "ai", ...
          "cool"  Cooling
          "heat"  Heating
          "dry"   dehumidifying
          "fan"   fan mode only

    temperature:  The full range of temperatures. If there
                  are 2 distinct ranges for cooling or heating,
                  the union should be used here.

                  The attribute 'temperature_step' can be used to
                  specify fractioanl temperature e.g. 0.5, 0.1


    fan: The air flow power. Values are expecterd to be amongst
           "auto"   Automatic mode
           lowest   The lowest air flow setting
           low
           medium
           high
           highest

           When there are only 3 modes, highest, medium and lowest should be used if possible

    swing: The use of the vertical orientation of the air flow..
            It can be a switch on/off (values 'off' and 'on') or more complex

            auto  automatic (in many cases similar to the on/off switch function)
            ceiling up up up
            90°    Horizontal orientation
            60°
            45°
            30°
            0°     Vertical orientation

Many other functions are possible, but still some canonization is recommended.

For instance, many manufactures trademarked their air purifying technology: nanoe, nanoex (Panasonic),
plasmacluster (Sharp), plasma (LG).... In this case it is recommended to use the name "purifier" for that functionm


The HVAC object offers to convenience methods:
       to_lirs, to transform the frames into lirc codes
       to_broadlink, to trnaform the frames into Broadlink compatible codes

TO BE CONTINUED
