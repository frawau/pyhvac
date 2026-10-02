"""The brand/model table: which brand sells which model on which
protocol. Generated once from the phase-4 name table; edit by hand
from now on. Rows: (brand, model, kind, Device class, variant)."""

from .protocols.airspool import AirspoolDevice
from .protocols.airton import AirtonDevice
from .protocols.airwell import AirwellDevice
from .protocols.amcor import AmcorDevice
from .protocols.argo import ArgoDevice
from .protocols.bosch import Bosch144Device
from .protocols.carrier import CarrierAc64Device
from .protocols.coolix import CoolixDevice
from .protocols.corona import CoronaAcDevice
from .protocols.daikin import (
    Daikin128Device,
    Daikin152Device,
    Daikin160Device,
    Daikin176Device,
    Daikin216Device,
    Daikin2Device,
    Daikin312Device,
    Daikin64Device,
    DaikinArcDevice,
    DaikinNativeDevice,
)
from .protocols.delonghi import DelonghiAcDevice
from .protocols.ecoclim import EcoclimDevice
from .protocols.electra import ElectraAcDevice
from .protocols.eurom import EuromDevice
from .protocols.fujitsu import FujitsuAcDevice
from .protocols.goodweather import GoodweatherDevice
from .protocols.gree import GreeDevice
from .protocols.haier import (
    Haier160Device,
    Haier176Device,
    HaierAcDevice,
    HaierYrw02Device,
)
from .protocols.hitachi import (
    Hitachi1Device,
    Hitachi264Device,
    Hitachi296Device,
    Hitachi344Device,
    Hitachi424Device,
    HitachiAcDevice,
)
from .protocols.kelon import KelonDevice
from .protocols.kelvinator import KelvinatorDevice
from .protocols.lg import Lg2Device, LgAcDevice, LgNativeDevice
from .protocols.midea import MideaDevice
from .protocols.mirage import MirageDevice
from .protocols.mitsubishi_electric import (
    Mitsubishi112Device,
    Mitsubishi136Device,
    MitsubishiAcDevice,
)
from .protocols.mitsubishi_heavy import (
    MitsubishiHeavy152Device,
    MitsubishiHeavy88Device,
)
from .protocols.neoclima import NeoclimaDevice
from .protocols.panasonic import (
    PanasonicAc32Device,
    PanasonicAcDevice,
    PanasonicNativeDevice,
)
from .protocols.rhoss import RhossDevice
from .protocols.samsung import SamsungAcDevice
from .protocols.sanyo import SanyoAc88Device, SanyoAcDevice
from .protocols.sharp import JTechDevice, SharpAcDevice
from .protocols.tcl import Tcl112AcDevice
from .protocols.technibel import TechnibelAcDevice
from .protocols.toshiba import ToshibaAcDevice
from .protocols.transcold import TranscoldDevice
from .protocols.trotec import Trotec3550Device, TrotecDevice
from .protocols.truma import TrumaDevice
from .protocols.vestel import VestelAcDevice
from .protocols.voltas import VoltasDevice
from .protocols.whirlpool import WhirlpoolAcDevice

MODELS = (
    ("AEG", "Chillflex Pro AXP26U338CW", "unit", ElectraAcDevice, None),
    ("Airspool", "AIRSPOOL protocol", "remote", AirspoolDevice, None),
    ("Airspool", "Mini-split", "unit", AirspoolDevice, None),
    ("Airton", "AIRTON protocol", "remote", AirtonDevice, None),
    ("Airton", "RD1A1", "remote", AirtonDevice, None),
    ("Airton", "SMVH09B-2A2A3NH", "unit", AirtonDevice, None),
    ("Airwell", "AIRWELL protocol", "remote", AirwellDevice, None),
    ("Airwell", "DC Series", "unit", AirwellDevice, None),
    ("Airwell", "RC04", "remote", AirwellDevice, None),
    ("Airwell", "RC08B", "remote", CoolixDevice, None),
    ("Airwell", "RC08W", "remote", AirwellDevice, None),
    ("Alaska", "SAC9010QC", "unit", TechnibelAcDevice, None),
    ("Amana", "PBC093G00CC", "unit", GreeDevice, "YAW1F"),
    ("Amana", "YX1FF", "remote", GreeDevice, "YAW1F"),
    ("Amcor", "ADR-853H", "unit", AmcorDevice, None),
    ("Amcor", "AMCOR protocol", "remote", AmcorDevice, None),
    ("Amcor", "TAC-444", "remote", AmcorDevice, None),
    ("Amcor", "TAC-495", "remote", AmcorDevice, None),
    ("Argo", "ARGO SAC_WREM2 protocol", "remote", ArgoDevice, "WREM2"),
    ("Argo", "ARGO SAC_WREM3 protocol", "remote", ArgoDevice, "WREM3"),
    ("Argo", "Ulisse 13 DCI", "unit", ArgoDevice, "WREM2"),
    ("Argo", "Ulisse Eco", "unit", ArgoDevice, "WREM3"),
    ("Argo", "WREM2", "remote", ArgoDevice, "WREM2"),
    ("Argo", "WREM3", "remote", ArgoDevice, "WREM3"),
    ("AUX", "KFR-35GW/BpNFW=3", "unit", ElectraAcDevice, None),
    ("AUX", "YKR-T/011", "remote", ElectraAcDevice, None),
    ("Beko", "BINR 070/071", "unit", CoolixDevice, None),
    ("Beko", "RG57K7(B)/BGEF", "remote", CoolixDevice, None),
    ("Bosch", "B1ZAI2441W", "unit", CoolixDevice, None),
    ("Bosch", "B1ZAO2441W", "unit", CoolixDevice, None),
    ("Bosch", "BOSCH144 protocol", "remote", Bosch144Device, None),
    ("Bosch", "CL3000i-Set 26 E", "unit", Bosch144Device, None),
    ("Bosch", "RG10A(G2S)BGEF", "remote", Bosch144Device, None),
    ("Bosch", "RG36B4/BGE", "remote", CoolixDevice, None),
    ("Carrier", "42NQV025M2 / 38NYV025M2", "unit", ToshibaAcDevice, None),
    ("Carrier", "42NQV035M2 / 38NYV035M2", "unit", ToshibaAcDevice, None),
    ("Carrier", "42NQV050M2 / 38NYV050M2", "unit", ToshibaAcDevice, None),
    ("Carrier", "42NQV060M2 / 38NYV060M2", "unit", ToshibaAcDevice, None),
    ("Carrier", "42QG5A55970", "remote", CarrierAc64Device, None),
    ("Carrier", "53NGK009/012", "unit", CarrierAc64Device, None),
    ("Carrier", "619EGX0090E0", "unit", CarrierAc64Device, None),
    ("Carrier", "619EGX0120E0", "unit", CarrierAc64Device, None),
    ("Carrier", "619EGX0180E0", "unit", CarrierAc64Device, None),
    ("Carrier", "619EGX0220E0", "unit", CarrierAc64Device, None),
    ("Carrier", "CARRIER_AC64 protocol", "remote", CarrierAc64Device, None),
    ("Centek", "SCT-65Q09", "unit", ElectraAcDevice, None),
    ("Centek", "YKR-P/002E", "remote", ElectraAcDevice, None),
    ("Comfee", "MPD1-12CRN7", "unit", MideaDevice, None),
    ("Cooper & Hunter", "CH-S09FTXG", "unit", GreeDevice, "YAW1F"),
    ("Cooper & Hunter", "YB1F2", "remote", GreeDevice, "YAW1F"),
    ("Corona", "AR-01", "remote", CoronaAcDevice, None),
    ("Corona", "CORONA_AC protocol", "remote", CoronaAcDevice, None),
    ("Corona", "CSH-N2211", "unit", CoronaAcDevice, None),
    ("Corona", "CSH-N2511", "unit", CoronaAcDevice, None),
    ("Corona", "CSH-N2811", "unit", CoronaAcDevice, None),
    ("Corona", "CSH-N4011", "unit", CoronaAcDevice, None),
    ("Daewoo", "DSB-F0934ELH-V", "unit", Tcl112AcDevice, "GZ055BE1"),
    ("Daewoo", "GYKQ-52E", "remote", Tcl112AcDevice, "GZ055BE1"),
    ("Daichi", "D-H", "unit", Haier176Device, "A"),
    ("Daikin", "17 Series FTXB09AXVJU", "unit", Daikin128Device, None),
    ("Daikin", "17 Series FTXB12AXVJU", "unit", Daikin128Device, None),
    ("Daikin", "17 Series FTXB24AXVJU", "unit", Daikin128Device, None),
    ("Daikin", "ARC423A5", "remote", Daikin160Device, None),
    ("Daikin", "ARC433**", "remote", DaikinArcDevice, None),
    ("Daikin", "ARC433B69", "remote", Daikin216Device, None),
    ("Daikin", "ARC466A12", "remote", DaikinArcDevice, None),
    ("Daikin", "ARC466A33", "remote", DaikinArcDevice, None),
    ("Daikin", "ARC466A67", "remote", Daikin312Device, None),
    ("Daikin", "ARC477A1", "remote", Daikin2Device, None),
    ("Daikin", "ARC480A5", "remote", Daikin152Device, None),
    ("Daikin", "ARC484A4", "remote", Daikin216Device, None),
    ("Daikin", "BRC4C151", "remote", Daikin176Device, None),
    ("Daikin", "BRC4C153", "remote", Daikin176Device, None),
    ("Daikin", "BRC52B63", "remote", Daikin128Device, None),
    ("Daikin", "DAIKIN protocol", "remote", DaikinArcDevice, None),
    ("Daikin", "DAIKIN128 protocol", "remote", Daikin128Device, None),
    ("Daikin", "DAIKIN152 protocol", "remote", Daikin152Device, None),
    ("Daikin", "DAIKIN160 protocol", "remote", Daikin160Device, None),
    ("Daikin", "DAIKIN176 protocol", "remote", Daikin176Device, None),
    ("Daikin", "DAIKIN2 protocol", "remote", Daikin2Device, None),
    ("Daikin", "DAIKIN216 protocol", "remote", Daikin216Device, None),
    ("Daikin", "DAIKIN312 protocol", "remote", Daikin312Device, None),
    ("Daikin", "DAIKIN64 protocol", "remote", Daikin64Device, None),
    ("Daikin", "DAIKIN_NATIVE protocol", "remote", DaikinNativeDevice, None),
    ("Daikin", "DGS01", "remote", Daikin64Device, None),
    ("Daikin", "FFN-C/FCN-F Series", "unit", Daikin64Device, None),
    ("Daikin", "FFQ35B8V1B", "unit", Daikin176Device, None),
    ("Daikin", "FTE12HV2S", "unit", Daikin160Device, None),
    ("Daikin", "FTQ60TV16U2", "unit", Daikin216Device, None),
    ("Daikin", "FTWX35AXV1", "unit", Daikin64Device, None),
    ("Daikin", "FTXM-M", "unit", DaikinArcDevice, None),
    ("Daikin", "FTXM20R5V1B", "unit", Daikin312Device, None),
    ("Daikin", "FTXZ25NV1B", "unit", Daikin2Device, None),
    ("Daikin", "FTXZ35NV1B", "unit", Daikin2Device, None),
    ("Daikin", "FTXZ50NV1B", "unit", Daikin2Device, None),
    ("Daikin", "M Series", "unit", DaikinArcDevice, None),
    ("Daikin", "Smash II", "unit", DaikinNativeDevice, None),
    ("Danby", "DAC080BGUWDB", "unit", MideaDevice, None),
    ("Danby", "DAC100BGUWDB", "unit", MideaDevice, None),
    ("Danby", "DAC120BGUWDB", "unit", MideaDevice, None),
    ("Danby", "R09C/BCGE", "remote", MideaDevice, None),
    ("De'Longhi", "DELONGHI_AC protocol", "remote", DelonghiAcDevice, None),
    ("De'Longhi", "PAC A95", "unit", DelonghiAcDevice, None),
    ("De'Longhi", "PAC EM90", "unit", ElectraAcDevice, None),
    ("Duux", "Blizzard Smart 10K / DXMA04", "unit", TrotecDevice, None),
    ("EcoClim", "ECOCLIM protocol", "remote", EcoclimDevice, None),
    ("EcoClim", "HYSFR-P348", "remote", EcoclimDevice, None),
    ("EcoClim", "ZC200DPO", "unit", EcoclimDevice, None),
    ("EKOKAI", "GREE YAW1F protocol", "remote", GreeDevice, "YAW1F"),
    ("Electra", "AXW12DCS", "unit", ElectraAcDevice, None),
    ("Electra", "Classic INV 17", "unit", ElectraAcDevice, None),
    ("Electra", "ELECTRA_AC protocol", "remote", ElectraAcDevice, None),
    ("Electra", "YKR-M/003E", "remote", ElectraAcDevice, None),
    ("Electrolux", "YKR-H/531E", "unit", ElectraAcDevice, None),
    ("Eurom", "EUROM protocol", "remote", EuromDevice, None),
    ("Eurom", "Polar 16CH", "unit", EuromDevice, None),
    ("Frigidaire", "FGPC102AB1", "unit", ElectraAcDevice, None),
    ("Fujitsu", "AGTV14LAC", "unit", FujitsuAcDevice, "ARRAH2E"),
    ("Fujitsu", "AR-DB1", "remote", FujitsuAcDevice, "ARDB1"),
    ("Fujitsu", "AR-DL10", "remote", FujitsuAcDevice, "ARDB1"),
    ("Fujitsu", "AR-RAC1E", "remote", FujitsuAcDevice, "ARRAH2E"),
    ("Fujitsu", "AR-RAE1E", "remote", FujitsuAcDevice, "ARRAH2E"),
    ("Fujitsu", "AR-RAH1U", "remote", FujitsuAcDevice, "ARREB1E"),
    ("Fujitsu", "AR-RAH2E", "remote", FujitsuAcDevice, "ARRAH2E"),
    ("Fujitsu", "AR-RAH2U", "remote", FujitsuAcDevice, "ARRAH2E"),
    ("Fujitsu", "AR-REB1E", "remote", FujitsuAcDevice, "ARREB1E"),
    ("Fujitsu", "AR-REB4E", "remote", FujitsuAcDevice, "ARREB1E"),
    ("Fujitsu", "AR-REG1U", "remote", FujitsuAcDevice, "ARRAH2E"),
    ("Fujitsu", "AR-REW1E", "remote", FujitsuAcDevice, "ARREW4E"),
    ("Fujitsu", "AR-REW4E", "remote", FujitsuAcDevice, "ARREW4E"),
    ("Fujitsu", "AR-RY4", "remote", FujitsuAcDevice, "ARRY4"),
    ("Fujitsu", "AST9RSGCW", "unit", FujitsuAcDevice, "ARDB1"),
    ("Fujitsu", "ASTB09LBC", "unit", FujitsuAcDevice, "ARRY4"),
    ("Fujitsu", "ASTG09K", "unit", FujitsuAcDevice, "ARREW4E"),
    ("Fujitsu", "ASTG18K", "unit", FujitsuAcDevice, "ARREW4E"),
    ("Fujitsu", "ASU12RLF", "unit", FujitsuAcDevice, "ARREB1E"),
    ("Fujitsu", "ASU30C1", "unit", FujitsuAcDevice, "ARDB1"),
    ("Fujitsu", "ASYG09KETA-B", "unit", FujitsuAcDevice, "ARREW4E"),
    ("Fujitsu", "ASYG30LFCA", "unit", FujitsuAcDevice, "ARRAH2E"),
    ("Fujitsu", "ASYG7LMCA", "unit", FujitsuAcDevice, "ARREB1E"),
    ("Fujitsu", "FUJITSU_AC ARDB1 protocol", "remote", FujitsuAcDevice, "ARDB1"),
    ("Fujitsu", "FUJITSU_AC ARJW2 protocol", "remote", FujitsuAcDevice, "ARJW2"),
    ("Fujitsu", "FUJITSU_AC ARRAH2E protocol", "remote", FujitsuAcDevice, "ARRAH2E"),
    ("Fujitsu", "FUJITSU_AC ARREB1E protocol", "remote", FujitsuAcDevice, "ARREB1E"),
    ("Fujitsu", "FUJITSU_AC ARREW4E protocol", "remote", FujitsuAcDevice, "ARREW4E"),
    ("Fujitsu", "FUJITSU_AC ARRY4 protocol", "remote", FujitsuAcDevice, "ARRY4"),
    ("Fujitsu General", "AOHG09LLC", "unit", FujitsuAcDevice, "ARRAH2E"),
    ("Fujitsu General", "AR-JW17", "remote", FujitsuAcDevice, "ARDB1"),
    ("Fujitsu General", "AR-JW2", "remote", FujitsuAcDevice, "ARJW2"),
    ("Fujitsu General", "AR-RCE1E", "remote", FujitsuAcDevice, "ARRAH2E"),
    ("Fujitsu General", "ASHG09LLCA", "unit", FujitsuAcDevice, "ARRAH2E"),
    ("GE", "6711AR2853M", "remote", LgAcDevice, "GE6711AR2853M"),
    ("GE", "AG1BH09AW101", "unit", LgAcDevice, "GE6711AR2853M"),
    ("Goodweather", "GOODWEATHER protocol", "remote", GoodweatherDevice, None),
    ("Goodweather", "ZH/JT-03", "remote", GoodweatherDevice, None),
    ("Gree", "GREE YAW1F protocol", "remote", GreeDevice, "YAW1F"),
    ("Gree", "VIR09HP115V1AH", "unit", GreeDevice, "YAW1F"),
    ("Gree", "VIR12HP230V1AH", "unit", GreeDevice, "YAW1F"),
    ("Gree", "YAA1FBF", "remote", GreeDevice, "YAW1F"),
    ("Gree", "YAN1F1", "remote", GreeDevice, "YAW1F"),
    ("Gree", "YAP0F8", "remote", KelvinatorDevice, None),
    ("Gree", "YAPOF3", "remote", KelvinatorDevice, None),
    ("Gree", "YB1F2F", "remote", GreeDevice, "YAW1F"),
    ("Gree", "YX1F2F", "remote", GreeDevice, "YX1FSF"),
    ("Green", "YBOFB", "remote", GreeDevice, "YBOFB"),
    ("Green", "YBOFB2", "remote", GreeDevice, "YBOFB"),
    ("Haier", "HAIER_AC protocol", "remote", HaierAcDevice, None),
    ("Haier", "HAIER_AC160 protocol", "remote", Haier160Device, None),
    ("Haier", "HAIER_AC176 V9014557_A protocol", "remote", Haier176Device, "A"),
    ("Haier", "HAIER_AC176 V9014557_B protocol", "remote", Haier176Device, "B"),
    ("Haier", "HAIER_AC_YRW02 V9014557_A protocol", "remote", HaierYrw02Device, "A"),
    ("Haier", "HAIER_AC_YRW02 V9014557_B protocol", "remote", HaierYrw02Device, "B"),
    ("Haier", "HSU-09HMC203", "unit", HaierYrw02Device, "A"),
    ("Haier", "HSU07-HEA03", "remote", HaierAcDevice, None),
    ("Haier", "KFR-26GW/83@UI-Ge", "unit", Haier160Device, None),
    ("Haier", "V9014557 M47 8D", "remote", Haier176Device, "A"),
    ("Haier", "YR-W02", "remote", HaierYrw02Device, "A"),
    ("Hitachi", "HITACHI_AC protocol", "remote", HitachiAcDevice, None),
    ("Hitachi", "HITACHI_AC1 R_LT0541_HTA_A protocol", "remote", Hitachi1Device, "A"),
    ("Hitachi", "HITACHI_AC1 R_LT0541_HTA_B protocol", "remote", Hitachi1Device, "B"),
    ("Hitachi", "HITACHI_AC264 protocol", "remote", Hitachi264Device, None),
    ("Hitachi", "HITACHI_AC296 protocol", "remote", Hitachi296Device, None),
    ("Hitachi", "HITACHI_AC344 protocol", "remote", Hitachi344Device, None),
    ("Hitachi", "HITACHI_AC424 protocol", "remote", Hitachi424Device, None),
    ("Hitachi", "KAZE-312KSDP", "unit", Hitachi1Device, "A"),
    ("Hitachi", "LT0541-HTA", "remote", Hitachi1Device, "A"),
    ("Hitachi", "R-LT0541-HTA/Y.K.1.1-1 V2.3", "remote", Hitachi1Device, "A"),
    ("Hitachi", "RAK-25NH5", "unit", Hitachi264Device, None),
    ("Hitachi", "RAR-2P2", "remote", Hitachi264Device, None),
    ("Hitachi", "RAR-3U3", "remote", Hitachi296Device, None),
    ("Hitachi", "RAR-8P2", "remote", Hitachi424Device, None),
    ("Hitachi", "RAS-22NK", "unit", Hitachi344Device, None),
    ("Hitachi", "RAS-35THA6", "remote", HitachiAcDevice, None),
    ("Hitachi", "RAS-70YHA3", "unit", Hitachi296Device, None),
    ("Hitachi", "RAS-AJ25H", "unit", Hitachi424Device, None),
    ("Hitachi", "RF11T1", "remote", Hitachi344Device, None),
    ("Hitachi", "Series VI", "unit", Hitachi1Device, "A"),
    ("Kastron", "RG57A7/BGEF", "remote", CoolixDevice, None),
    ("Kaysun", "Casual CF", "unit", MideaDevice, None),
    ("Kaysun", "Casual CF (COOLIX)", "unit", CoolixDevice, None),
    ("Kelon", "ON/OFF 9000-12000", "unit", KelonDevice, None),
    ("Kelvinator", "KELVINATOR protocol", "remote", KelvinatorDevice, None),
    ("Kelvinator", "KSV26CRC", "unit", KelvinatorDevice, None),
    ("Kelvinator", "KSV26HRC", "unit", KelvinatorDevice, None),
    ("Kelvinator", "KSV35CRC", "unit", KelvinatorDevice, None),
    ("Kelvinator", "KSV35HRC", "unit", KelvinatorDevice, None),
    ("Kelvinator", "KSV53HRC", "unit", KelvinatorDevice, None),
    ("Kelvinator", "KSV62HRC", "unit", KelvinatorDevice, None),
    ("Kelvinator", "KSV70CRC", "unit", KelvinatorDevice, None),
    ("Kelvinator", "KSV70HRC", "unit", KelvinatorDevice, None),
    ("Kelvinator", "KSV80HRC", "unit", KelvinatorDevice, None),
    ("Kelvinator", "YALIF", "remote", KelvinatorDevice, None),
    ("Keystone", "RG57H4(B)BGEF", "remote", MideaDevice, None),
    ("Leberg", "LBS-TOR07", "unit", Tcl112AcDevice, "TAC09CHSD"),
    ("Lennox", "M22A", "unit", MideaDevice, None),
    ("Lennox", "M33A", "unit", MideaDevice, None),
    ("Lennox", "M33B", "unit", MideaDevice, None),
    ("Lennox", "MCFA", "unit", MideaDevice, None),
    ("Lennox", "MCFB", "unit", MideaDevice, None),
    ("Lennox", "MMDA", "unit", MideaDevice, None),
    ("Lennox", "MMDB", "unit", MideaDevice, None),
    ("Lennox", "MWMA", "unit", MideaDevice, None),
    ("Lennox", "MWMA009S4-3P", "unit", MideaDevice, None),
    ("Lennox", "MWMA012S4-3P", "unit", MideaDevice, None),
    ("Lennox", "MWMB", "unit", MideaDevice, None),
    ("Lennox", "RG57A6/BGEFU1", "remote", MideaDevice, None),
    ("LG", "6711A20083V", "remote", LgAcDevice, "LG6711A20083V"),
    ("LG", "A4UW30GFA2", "unit", Lg2Device, "AKB74955603"),
    ("LG", "AKB73315611", "remote", Lg2Device, "AKB74955603"),
    ("LG", "AKB73757604", "remote", Lg2Device, "AKB73757604"),
    ("LG", "AKB74395308", "remote", Lg2Device, "AKB75215403"),
    ("LG", "AKB74955603", "remote", Lg2Device, "AKB74955603"),
    ("LG", "AKB75215403", "remote", Lg2Device, "AKB75215403"),
    ("LG", "AMNW09GSJA0", "unit", Lg2Device, "AKB74955603"),
    ("LG", "AMNW24GTPA1", "unit", Lg2Device, "AKB73757604"),
    ("LG", "Dual Inverter", "unit", LgNativeDevice, "dual inverter"),
    ("LG", "Inverter V", "unit", LgNativeDevice, "inverter v"),
    ("LG", "LG_NATIVE protocol", "remote", LgNativeDevice, "generic"),
    ("LG", "MS05SQ NW0", "unit", Lg2Device, "AKB74955603"),
    ("LG", "S4-W12JA3AA", "unit", Lg2Device, "AKB75215403"),
    ("LG", "TS-H122ERM1", "remote", LgAcDevice, "LG6711A20083V"),
    ("Mabe", "MMI18HDBWCA6MI8", "unit", Haier176Device, "A"),
    ("Mabe", "V12843 HJ200223", "remote", Haier176Device, "A"),
    ("Maxell", "KKG9A-C1", "remote", MirageDevice, "KKG9AC1"),
    ("Maxell", "MX-CH18CF", "unit", MirageDevice, "KKG9AC1"),
    ("Midea", "COOLIX protocol", "remote", CoolixDevice, None),
    ("Midea", "MIDEA protocol", "remote", MideaDevice, None),
    ("Midea", "MS12FU-10HRDN1-QRD0GW(B)", "unit", CoolixDevice, None),
    ("Midea", "MSABAU-07HRFN1-QRD0GW", "unit", CoolixDevice, None),
    ("Midea", "RG52D/BGE", "remote", CoolixDevice, None),
    ("Mirage", "MIRAGE KKG29AC1 protocol", "remote", MirageDevice, "KKG29AC1"),
    ("Mirage", "MIRAGE KKG9AC1 protocol", "remote", MirageDevice, "KKG9AC1"),
    ("Mirage", "VLU series", "unit", MirageDevice, "KKG9AC1"),
    ("Mitsubishi Electric", "001CP T7WE10714", "remote", Mitsubishi136Device, None),
    ("Mitsubishi Electric", "KM14A 0179213", "remote", MitsubishiAcDevice, None),
    ("Mitsubishi Electric", "KPOA", "remote", Mitsubishi112Device, None),
    (
        "Mitsubishi Electric",
        "MITSUBISHI112 protocol",
        "remote",
        Mitsubishi112Device,
        None,
    ),
    (
        "Mitsubishi Electric",
        "MITSUBISHI136 protocol",
        "remote",
        Mitsubishi136Device,
        None,
    ),
    (
        "Mitsubishi Electric",
        "MITSUBISHI_AC protocol",
        "remote",
        MitsubishiAcDevice,
        None,
    ),
    ("Mitsubishi Electric", "MLZ-RX5017AS", "unit", MitsubishiAcDevice, None),
    ("Mitsubishi Electric", "MS-GK24VA", "unit", MitsubishiAcDevice, None),
    ("Mitsubishi Electric", "MSH-A24WV", "unit", Mitsubishi112Device, None),
    ("Mitsubishi Electric", "MSZ-FHnnVE", "unit", MitsubishiAcDevice, None),
    ("Mitsubishi Electric", "MSZ-GV2519", "unit", MitsubishiAcDevice, None),
    ("Mitsubishi Electric", "MSZ-SF25VE3", "unit", MitsubishiAcDevice, None),
    ("Mitsubishi Electric", "MSZ-ZW4017S", "unit", MitsubishiAcDevice, None),
    ("Mitsubishi Electric", "MUH-A24WV", "unit", Mitsubishi112Device, None),
    ("Mitsubishi Electric", "PAR-FA32MA", "remote", Mitsubishi136Device, None),
    ("Mitsubishi Electric", "PEAD-RP71JAA", "unit", Mitsubishi136Device, None),
    ("Mitsubishi Electric", "RH151", "remote", MitsubishiAcDevice, None),
    ("Mitsubishi Electric", "RH151/M21ED6426", "remote", MitsubishiAcDevice, None),
    ("Mitsubishi Electric", "SG153/M21EDF426", "remote", MitsubishiAcDevice, None),
    ("Mitsubishi Electric", "SG15D", "remote", MitsubishiAcDevice, None),
    (
        "Mitsubishi Heavy Industries",
        "MITSUBISHI_HEAVY_152 protocol",
        "remote",
        MitsubishiHeavy152Device,
        None,
    ),
    (
        "Mitsubishi Heavy Industries",
        "MITSUBISHI_HEAVY_88 protocol",
        "remote",
        MitsubishiHeavy88Device,
        None,
    ),
    (
        "Mitsubishi Heavy Industries",
        "RKX502A001C",
        "remote",
        MitsubishiHeavy88Device,
        None,
    ),
    (
        "Mitsubishi Heavy Industries",
        "RLA502A700B",
        "remote",
        MitsubishiHeavy152Device,
        None,
    ),
    ("Mitsubishi Heavy Industries", "SRKxxZJ-S", "unit", MitsubishiHeavy88Device, None),
    (
        "Mitsubishi Heavy Industries",
        "SRKxxZM-S",
        "unit",
        MitsubishiHeavy152Device,
        None,
    ),
    (
        "Mitsubishi Heavy Industries",
        "SRKxxZMXA-S",
        "unit",
        MitsubishiHeavy152Device,
        None,
    ),
    ("MRCOOL", "RG57A6/BGEFU1", "remote", MideaDevice, None),
    ("Neoclima", "NEOCLIMA protocol", "remote", NeoclimaDevice, None),
    ("Neoclima", "NS-09AHTI", "unit", NeoclimaDevice, None),
    ("Neoclima", "ZH/TY-01", "remote", NeoclimaDevice, None),
    ("O General", "AR-RCL1E", "remote", FujitsuAcDevice, "ARRAH2E"),
    ("Panasonic", "4-Way Cassette", "unit", PanasonicNativeDevice, "4 way cassette"),
    ("Panasonic", "A75C2295", "remote", PanasonicAc32Device, None),
    ("Panasonic", "A75C2311", "remote", PanasonicAcDevice, "CKP"),
    ("Panasonic", "A75C2616-1", "remote", PanasonicAcDevice, "DKE"),
    ("Panasonic", "A75C3704", "remote", PanasonicAcDevice, "DKE"),
    ("Panasonic", "A75C3747", "remote", PanasonicAcDevice, "JKE"),
    ("Panasonic", "A75C4762", "remote", PanasonicAcDevice, "RKR"),
    ("Panasonic", "CKP series", "unit", PanasonicAcDevice, "CKP"),
    ("Panasonic", "CS-E12QKEW", "unit", PanasonicAcDevice, "DKE"),
    ("Panasonic", "CS-E7PKR", "unit", PanasonicAcDevice, "DKE"),
    ("Panasonic", "CS-E9CKP series", "unit", PanasonicAc32Device, None),
    ("Panasonic", "CS-ME10CKPG", "unit", PanasonicAcDevice, "CKP"),
    ("Panasonic", "CS-ME12CKPG", "unit", PanasonicAcDevice, "CKP"),
    ("Panasonic", "CS-ME14CKPG", "unit", PanasonicAcDevice, "CKP"),
    ("Panasonic", "CS-YW9MKD", "unit", PanasonicAcDevice, "JKE"),
    ("Panasonic", "CS-Z24RKR", "unit", PanasonicAcDevice, "RKR"),
    ("Panasonic", "CS-Z9RKR", "unit", PanasonicAcDevice, "RKR"),
    ("Panasonic", "DKE series", "unit", PanasonicAcDevice, "DKE"),
    ("Panasonic", "DKW series", "unit", PanasonicAcDevice, "DKE"),
    ("Panasonic", "JKE series", "unit", PanasonicAcDevice, "JKE"),
    ("Panasonic", "NKE series", "unit", PanasonicAcDevice, "NKE"),
    ("Panasonic", "PANASONIC_AC32 protocol", "remote", PanasonicAc32Device, None),
    (
        "Panasonic",
        "PANASONIC_NATIVE protocol",
        "remote",
        PanasonicNativeDevice,
        "generic",
    ),
    ("Panasonic", "PKR series", "unit", PanasonicAcDevice, "DKE"),
    ("Panasonic", "PN1122V", "remote", PanasonicAcDevice, "DKE"),
    ("Panasonic", "RKR series", "unit", PanasonicAcDevice, "RKR"),
    ("Pioneer System", "RG66B6(B)/BGEFU1", "remote", MideaDevice, None),
    ("Pioneer System", "RUBO18GMFILCAD", "unit", MideaDevice, None),
    ("Pioneer System", "RYBO12GMFILCAD", "unit", MideaDevice, None),
    ("Pioneer System", "UB018GMFILCFHD", "unit", MideaDevice, None),
    ("Pioneer System", "WS012GMFI22HLD", "unit", MideaDevice, None),
    ("Pioneer System", "WS018GMFI22HLD", "unit", MideaDevice, None),
    ("Rhoss", "Idrowall MPCV 20-30-35-40", "unit", RhossDevice, None),
    ("Rhoss", "RHOSS protocol", "remote", RhossDevice, None),
    ("RusClimate", "EACS/I-09HAR_X/N3", "unit", GreeDevice, "YAW1F"),
    ("RusClimate", "YAW1F", "remote", GreeDevice, "YAW1F"),
    ("Samsung", "AR09FSSDAWKNFA", "unit", SamsungAcDevice, None),
    ("Samsung", "AR09HSFSBWKN", "unit", SamsungAcDevice, None),
    ("Samsung", "AR12HSSDBWKNEU", "unit", SamsungAcDevice, None),
    ("Samsung", "AR12KSFPEWQNET", "unit", SamsungAcDevice, None),
    ("Samsung", "AR12NXCXAWKXEU", "unit", SamsungAcDevice, None),
    ("Samsung", "AR12TXEAAWKNEU", "unit", SamsungAcDevice, None),
    ("Samsung", "DB93-14195A", "remote", SamsungAcDevice, None),
    ("Samsung", "DB96-24901C", "remote", SamsungAcDevice, None),
    ("Samsung", "SAMSUNG_AC protocol", "remote", SamsungAcDevice, None),
    ("Sanyo", "RCS-2HS4E", "remote", SanyoAcDevice, None),
    ("Sanyo", "RCS-2S4E", "remote", SanyoAcDevice, None),
    ("Sanyo", "SANYO_AC protocol", "remote", SanyoAcDevice, None),
    ("Sanyo", "SANYO_AC88 protocol", "remote", SanyoAc88Device, None),
    ("Sanyo", "SAP-K121AHA", "unit", SanyoAcDevice, None),
    ("Sanyo", "SAP-K242AH", "unit", SanyoAcDevice, None),
    ("Sharp", "A5VEY", "unit", KelvinatorDevice, None),
    ("Sharp", "AH-A12REVP-1", "unit", SharpAcDevice, "A903"),
    ("Sharp", "AH-AxSAY", "unit", SharpAcDevice, "A907"),
    ("Sharp", "AH-PR13-GL", "unit", SharpAcDevice, "A903"),
    ("Sharp", "AH-XP10NRY", "unit", SharpAcDevice, "A903"),
    ("Sharp", "AY-ZP40KR", "unit", SharpAcDevice, "A907"),
    ("Sharp", "CRMC-820 JBEZ", "remote", SharpAcDevice, "A903"),
    ("Sharp", "CRMC-A705 JBEZ", "remote", SharpAcDevice, "A705"),
    ("Sharp", "CRMC-A863 JBEZ", "remote", SharpAcDevice, "A903"),
    ("Sharp", "CRMC-A903JBEZ", "remote", SharpAcDevice, "A903"),
    ("Sharp", "CRMC-A907 JBEZ", "remote", SharpAcDevice, "A907"),
    ("Sharp", "CRMC-A950 JBEZ", "remote", SharpAcDevice, "A907"),
    ("Sharp", "J-Tech", "unit", JTechDevice, None),
    ("Sharp", "SHARP_AC A705 protocol", "remote", SharpAcDevice, "A705"),
    ("Sharp", "SHARP_AC A903 protocol", "remote", SharpAcDevice, "A903"),
    ("Sharp", "SHARP_AC A907 protocol", "remote", SharpAcDevice, "A907"),
    ("Sharp", "YB1FA", "remote", KelvinatorDevice, None),
    ("Soleus Air", "TTWM1-10-01", "unit", NeoclimaDevice, None),
    ("Soleus Air", "window", "unit", GreeDevice, "YX1FSF"),
    ("Soleus Air", "ZCF/TL-05", "remote", NeoclimaDevice, None),
    ("Subtropic", "SUB-07HN1_18Y", "unit", ElectraAcDevice, None),
    ("Subtropic", "YKR-H/102E", "remote", ElectraAcDevice, None),
    ("TCL", "TAC-09CHSD/XA31I", "unit", Tcl112AcDevice, "TAC09CHSD"),
    ("TCL", "TCL112AC GZ055BE1 protocol", "remote", Tcl112AcDevice, "GZ055BE1"),
    ("TCL", "TCL112AC TAC09CHSD protocol", "remote", Tcl112AcDevice, "TAC09CHSD"),
    ("Technibel", "IRO PLUS", "unit", TechnibelAcDevice, None),
    ("Technibel", "TECHNIBEL_AC protocol", "remote", TechnibelAcDevice, None),
    ("Teco", "TECHNIBEL_AC protocol", "remote", TechnibelAcDevice, None),
    ("Teknopoint", "Allegro SSA-09H", "unit", Tcl112AcDevice, "GZ055BE1"),
    ("Teknopoint", "GZ-055B-E1", "remote", Tcl112AcDevice, "GZ055BE1"),
    ("Tokio", "AATOEMF17-12CHR1SW", "unit", CoolixDevice, None),
    ("Tokio", "RG51|50/BGE", "remote", CoolixDevice, None),
    ("Toshiba", "Akita EVO II", "unit", ToshibaAcDevice, None),
    ("Toshiba", "RAS 18SKP-ES", "unit", ToshibaAcDevice, None),
    ("Toshiba", "RAS-2558V", "unit", ToshibaAcDevice, None),
    ("Toshiba", "RAS-25SKVP2-ND", "unit", ToshibaAcDevice, None),
    ("Toshiba", "RAS-4M27YAV-E", "unit", CoolixDevice, None),
    ("Toshiba", "RAS-B13N3KV2", "unit", ToshibaAcDevice, None),
    ("Toshiba", "RAS-B13N3KVP-E", "unit", ToshibaAcDevice, None),
    ("Toshiba", "RAS-M10YKV-E", "unit", CoolixDevice, None),
    ("Toshiba", "RAS-M13YKV-E", "unit", CoolixDevice, None),
    ("Toshiba", "TOSHIBA_AC protocol", "remote", ToshibaAcDevice, None),
    ("Toshiba", "WC-L03SE", "remote", ToshibaAcDevice, None),
    ("Toshiba", "WH-E1YE", "remote", CoolixDevice, None),
    ("Toshiba", "WH-TA01JE", "remote", ToshibaAcDevice, None),
    ("Toshiba", "WH-TA04NE", "remote", ToshibaAcDevice, None),
    ("Toshiba", "WH-UB03NJ", "remote", ToshibaAcDevice, None),
    ("Transcold", "M1-F-NO-6", "unit", TranscoldDevice, None),
    ("Transcold", "TRANSCOLD protocol", "remote", TranscoldDevice, None),
    ("Tronitechnik", "KKG29A-C1", "remote", MirageDevice, "KKG29AC1"),
    ("Tronitechnik", "Reykir 9000", "unit", MirageDevice, "KKG29AC1"),
    ("Trotec", "PAC 2100 X", "unit", MideaDevice, None),
    ("Trotec", "PAC 3200", "unit", TrotecDevice, None),
    ("Trotec", "PAC 3550 Pro", "unit", Trotec3550Device, None),
    ("Trotec", "PAC 3900 X", "unit", MideaDevice, None),
    ("Trotec", "RG57H(B)/BGE", "remote", MideaDevice, None),
    ("Trotec", "RG57H3(B)/BGCEF-M", "remote", MideaDevice, None),
    ("Trotec", "TROTEC protocol", "remote", TrotecDevice, None),
    ("Trotec", "TROTEC_3550 protocol", "remote", Trotec3550Device, None),
    ("Truma", "40091-86700", "remote", TrumaDevice, None),
    ("Truma", "Aventa", "unit", TrumaDevice, None),
    ("Truma", "TRUMA protocol", "remote", TrumaDevice, None),
    ("Ultimate", "Heat Pump", "unit", GreeDevice, "YAW1F"),
    ("Vaillant", "VAI5-035WNI", "unit", GreeDevice, "YAW1F"),
    ("Vaillant", "YACIFB", "remote", GreeDevice, "YAW1F"),
    ("Vestel", "BIOX CXP-9", "unit", VestelAcDevice, None),
    ("Vestel", "VESTEL_AC protocol", "remote", VestelAcDevice, None),
    ("Voltas", "122LZF 4011252", "unit", VoltasDevice, "122LZF"),
    ("Voltas", "VOLTAS kVoltas122LZF protocol", "remote", VoltasDevice, "122LZF"),
    ("Voltas", "VOLTAS kVoltasUnknown protocol", "remote", VoltasDevice, "Unknown"),
    ("Whirlpool", "DG11J1-04", "remote", WhirlpoolAcDevice, "DG11J13A"),
    ("Whirlpool", "DG11J1-3A", "remote", WhirlpoolAcDevice, "DG11J13A"),
    ("Whirlpool", "DG11J1-91", "remote", WhirlpoolAcDevice, "DG11J191"),
    ("Whirlpool", "SPIS409L", "unit", WhirlpoolAcDevice, "DG11J13A"),
    ("Whirlpool", "SPIS412L", "unit", WhirlpoolAcDevice, "DG11J13A"),
    ("Whirlpool", "SPIW409L", "unit", WhirlpoolAcDevice, "DG11J13A"),
    ("Whirlpool", "SPIW412L", "unit", WhirlpoolAcDevice, "DG11J13A"),
    ("Whirlpool", "SPIW418L", "unit", WhirlpoolAcDevice, "DG11J13A"),
    (
        "Whirlpool",
        "WHIRLPOOL_AC DG11J13A protocol",
        "remote",
        WhirlpoolAcDevice,
        "DG11J13A",
    ),
    (
        "Whirlpool",
        "WHIRLPOOL_AC DG11J191 protocol",
        "remote",
        WhirlpoolAcDevice,
        "DG11J191",
    ),
    # SmartIR climate files (tools/smartir; docs/smartir/report.md)
    ("LG", "W12TCM", "unit", LgAcDevice, "GE6711AR2853M"),  # SmartIR 1067
    ("Actron", "Actron", "unit", CoolixDevice, None),  # SmartIR 1140
    ("Electrolux", "EACS/I-HAT/N3", "unit", CoolixDevice, None),  # SmartIR 1700
    (
        "General Electric",
        "ASHA09LCC",
        "unit",
        FujitsuAcDevice,
        "ARRAH2E",
    ),  # SmartIR 1042
    ("LG", "R09AWN", "unit", LgAcDevice, "GE6711AR2853M"),  # SmartIR 1060
    ("LG", "R24AWN", "unit", LgAcDevice, "GE6711AR2853M"),  # SmartIR 1060
    ("LG", "E09EK", "unit", LgAcDevice, "GE6711AR2853M"),  # SmartIR 1060
    ("LG", "P12EP1", "unit", Lg2Device, "AKB74955603"),  # SmartIR 1063
    ("LG", "LA090HYV", "unit", Lg2Device, "AKB74955603"),  # SmartIR 1066
    ("LG", "LA120HYV", "unit", Lg2Device, "AKB74955603"),  # SmartIR 1066
    ("LG", "LAN090HYV", "unit", Lg2Device, "AKB74955603"),  # SmartIR 1066
    ("LG", "LAN120HYV", "unit", Lg2Device, "AKB74955603"),  # SmartIR 1066
    ("LG", "AKB74295304", "unit", Lg2Device, "AKB74955603"),  # SmartIR 1069
    ("LG", "PC09SQ NSJ", "unit", Lg2Device, "AKB74955603"),  # SmartIR 1070
    ("Carrier", "Carrier", "unit", CoolixDevice, None),  # SmartIR 1160
    ("Carrier", "42LUVH025N-1", "unit", CoolixDevice, None),  # SmartIR 1164
    ("Fujitsu", "AR-JE5", "unit", FujitsuAcDevice, "ARDB1"),  # SmartIR 1286
    ("Fujitsu", "ASYG-LMCE", "unit", FujitsuAcDevice, "ARRAH2E"),  # SmartIR 1287
    ("Fujitsu", "AR-REM7E", "unit", FujitsuAcDevice, "ARRAH2E"),  # SmartIR 1287
    ("Fujitsu", "AR-REW2E", "unit", FujitsuAcDevice, "ARRAH2E"),  # SmartIR 1287
    ("Fujitsu", "ASYG07LM", "unit", FujitsuAcDevice, "ARRAH2E"),  # SmartIR 1293
    ("Fujitsu", "ASYG09LM", "unit", FujitsuAcDevice, "ARRAH2E"),  # SmartIR 1293
    ("Springer", "Split Hi Wall Maxiflex", "unit", CoolixDevice, None),  # SmartIR 1360
    ("Midea", "MSY-12HRDN1", "unit", CoolixDevice, None),  # SmartIR 1382
    ("Midea", "KFR-35G", "unit", CoolixDevice, None),  # SmartIR 1383
    ("Midea", "MSMACU-18HRFN1-QRD0GW", "unit", CoolixDevice, None),  # SmartIR 1384
    ("Midea", "RG70E/BGEF", "remote", CoolixDevice, None),  # SmartIR 1387
    ("Midea", "MAP05R1WWT", "unit", CoolixDevice, None),  # SmartIR 1389
    ("Midea", "RG52C1/BGE", "remote", CoolixDevice, None),  # SmartIR 1390
    ("Midea", "RG58E3/BGEF", "unit", CoolixDevice, None),  # SmartIR 1391
    ("Midea", "RG70C/BGEF", "remote", CoolixDevice, None),  # SmartIR 1394
    ("Samsung", "AR**TSHQBURN", "unit", CoolixDevice, None),  # SmartIR 1405
    ("Alliance", "Alliance", "unit", CoolixDevice, None),  # SmartIR 1460
    ("Beko", "BPEU 120", "unit", CoolixDevice, None),  # SmartIR 1604
    ("Tornado", "Super - Inverter A, i", "unit", CoolixDevice, None),  # SmartIR 1620
    ("Tornado", "Inverter", "unit", CoolixDevice, None),  # SmartIR 1620
    ("Tornado", "Inverter A", "unit", CoolixDevice, None),  # SmartIR 1620
    ("Tornado", "Super Design", "unit", CoolixDevice, None),  # SmartIR 1620
    ("Tornado", "Super Plasma", "unit", CoolixDevice, None),  # SmartIR 1620
    ("Tornado", "Gold i", "unit", CoolixDevice, None),  # SmartIR 1620
    ("Tornado", "Multi ON-OFF", "unit", CoolixDevice, None),  # SmartIR 1620
    ("Tornado", "Multi Inverter", "unit", CoolixDevice, None),  # SmartIR 1620
    ("Tornado", "Super Gold i", "unit", CoolixDevice, None),  # SmartIR 1620
    ("Tornado", "Plasma Gold", "unit", CoolixDevice, None),  # SmartIR 1620
    ("Tornado", "Super Legend 40", "unit", KelonDevice, "16C"),  # SmartIR 1621
    ("Electrolux", "EPI12LEIWI", "unit", CoolixDevice, None),  # SmartIR 1704
    ("Kelvinator", "KSV25HRG", "unit", CoolixDevice, "quiet"),  # SmartIR 1740
    ("Daitsu", "DS12U-RV", "unit", CoolixDevice, None),  # SmartIR 1760
    ("Ballu", "BSD/in-09HN1_20Y", "unit", CoolixDevice, None),  # SmartIR 1801
    ("Electra", "Electra", "unit", CoolixDevice, "16C"),  # SmartIR 1941
    (
        "Electra",
        "Electra Platinum Plus Inverter",
        "unit",
        CoolixDevice,
        None,
    ),  # SmartIR 1944
    ("Ariston", "A-IFWHxx-IGX", "unit", CoolixDevice, None),  # SmartIR 2020
    ("Lennox", "LNMTE026V2", "unit", CoolixDevice, None),  # SmartIR 2161
    ("Rotenso", "Ukura", "unit", CoolixDevice, None),  # SmartIR 2480
    ("Rotenso", "Maze", "remote", CoolixDevice, None),  # SmartIR 2480
    ("Komeco", "Komeco", "unit", CoolixDevice, None),  # SmartIR 2620
    ("Fisher", "FSOAI-SU-90AE2", "unit", CoolixDevice, None),  # SmartIR 2641
    ("Kaden", "KS09", "unit", CoolixDevice, None),  # SmartIR 3360
    ("Kaden", "KS12", "unit", CoolixDevice, None),  # SmartIR 3360
    ("Kaden", "KS18", "unit", CoolixDevice, None),  # SmartIR 3360
    ("Kaden", "KS24", "unit", CoolixDevice, None),  # SmartIR 3360
    ("Kaden", "KS28", "unit", CoolixDevice, None),  # SmartIR 3360
    ("LG", "P12RK", "unit", LgAcDevice, "GE6711AR2853M"),  # SmartIR 7062
    ("Fujitsu", "ASYG18LF", "unit", FujitsuAcDevice, "ARRAH2E"),  # SmartIR 1292
    ("Fujitsu", "AR-RY12", "unit", FujitsuAcDevice, "ARRAH2E"),  # SmartIR 1292
    ("Beko", "BEVCA 120", "unit", ElectraAcDevice, "aux"),  # SmartIR 1600
    ("Electrolux", "EXP26U758CW", "unit", ElectraAcDevice, "aux"),  # SmartIR 1703
    ("Ballu", "YKR-K/002E", "unit", ElectraAcDevice, "aux"),  # SmartIR 1800
    ("AUX", "AUX FREEDOM AUX-09FH", "unit", ElectraAcDevice, "aux"),  # SmartIR 1961
    ("AUX", "iClima ICI-09A", "unit", ElectraAcDevice, "aux"),  # SmartIR 1962
    ("AUX", "Kendal Split Inverter", "unit", ElectraAcDevice, "aux"),  # SmartIR 1963
    ("Sendo", "SND-18/IK", "unit", ElectraAcDevice, "aux"),  # SmartIR 2080
    ("BAXI", "BAXI", "unit", ElectraAcDevice, "aux"),  # SmartIR 2380
    ("FanWorld", "FW6-3000", "unit", ElectraAcDevice, "aux"),  # SmartIR 2460
    ("ELGIN", "HVQI18B2IA", "unit", ElectraAcDevice, "aux"),  # SmartIR 2800
    ("Mundoclima", "MUPR-09-H9A", "unit", ElectraAcDevice, "aux"),  # SmartIR 3220
    ("Mundoclima", "MUPR-12-H9A", "unit", ElectraAcDevice, "aux"),  # SmartIR 3220
    ("Mundoclima", "MUPR-18-H9A", "unit", ElectraAcDevice, "aux"),  # SmartIR 3220
    ("Mundoclima", "MUPR-24-H9A", "unit", ElectraAcDevice, "aux"),  # SmartIR 3220
    ("Mundoclima", "MUPR-09-H5A", "unit", ElectraAcDevice, "aux"),  # SmartIR 3220
    ("Mundoclima", "MUPR-12-H5A", "unit", ElectraAcDevice, "aux"),  # SmartIR 3220
    ("Mundoclima", "MUPR-18-H5A", "unit", ElectraAcDevice, "aux"),  # SmartIR 3220
    ("Mundoclima", "MUPR-24-H5A", "unit", ElectraAcDevice, "aux"),  # SmartIR 3220
    ("PARKAIR", "DI-A", "unit", ElectraAcDevice, "aux"),  # SmartIR 3300
    ("Zephir", "DualSplit", "unit", ElectraAcDevice, "aux"),  # SmartIR 3380
    ("Toyotomi", "AKIRA GAN/GAG-A128 VL", "unit", GreeDevice, "YX1FSF"),  # SmartIR 1000
    ("Panasonic", "CS-CE7HKEW", "unit", PanasonicAcDevice, "JKE-M13"),  # SmartIR 1020
    ("Panasonic", "CS-CE9HKEW", "unit", PanasonicAcDevice, "JKE-M13"),  # SmartIR 1020
    ("Panasonic", "CS-CE12HKEW", "unit", PanasonicAcDevice, "JKE-M13"),  # SmartIR 1020
    ("Panasonic", "CS-PC24MKF", "unit", PanasonicAcDevice, "JKE-M13"),  # SmartIR 1020
    ("Panasonic", "CS-C24PKF", "unit", PanasonicAcDevice, "JKE-M13"),  # SmartIR 1020
    ("Panasonic", "CS-HE9JKE", "unit", PanasonicAcDevice, "RKR-81"),  # SmartIR 1023
    ("Panasonic", "CS-HE12JKE", "unit", PanasonicAcDevice, "RKR-81"),  # SmartIR 1023
    ("Panasonic", "CS-HE9LKE", "unit", PanasonicAcDevice, "RKR-81"),  # SmartIR 1023
    ("Panasonic", "CS-PC12QKT", "unit", PanasonicAcDevice, "JKE-M13"),  # SmartIR 1026
    ("Panasonic", "CS-U9RKR", "unit", PanasonicAcDevice, "RKR-81"),  # SmartIR 1028
    ("Panasonic", "CS-U12RKR", "unit", PanasonicAcDevice, "RKR-81"),  # SmartIR 1028
    ("Panasonic", "CS-E12JKDW", "unit", PanasonicAcDevice, "JKE-M13"),  # SmartIR 1030
    (
        "Panasonic",
        "SRK25ZMP-S, SRK35ZMP-S, SRK45ZMP-S",
        "unit",
        MitsubishiHeavy88Device,
        None,
    ),  # SmartIR 1031
    ("Hitachi", "RAC-50HK1", "unit", Hitachi264Device, None),  # SmartIR 1080
    ("Daikin", "FTE09NV25", "unit", Daikin160Device, None),  # SmartIR 1111
    (
        "Mitsubishi Electric",
        "PAR-FL32MA",
        "unit",
        Mitsubishi136Device,
        None,
    ),  # SmartIR 1131
    ("Carrier", "40MAQB12B--3", "unit", MideaDevice, "RG57-F"),  # SmartIR 1163
    ("Carrier", "40MAQB18B--3", "unit", MideaDevice, "RG57-F"),  # SmartIR 1163
    ("Sungold", "Sungold", "unit", MideaDevice, "RG57-F"),  # SmartIR 1220
    ("Consul", "CBV12CBBNA", "unit", KelonDevice, "dry-grade"),  # SmartIR 1241
    ("Consul", "CBY12DBBNA", "unit", KelonDevice, "dry-grade"),  # SmartIR 1241
    ("Haier", "Top-Tech 14", "unit", HaierYrw02Device, "A"),  # SmartIR 1321
    ("Midea", "MPD-12CRN7", "unit", MideaDevice, "RG57"),  # SmartIR 1392
    ("Midea", "MPPHB-09CRN7-QB6-N", "unit", MideaDevice, "RG57"),  # SmartIR 1393
    ("Midea", "RG10B(D1)/BGEFU1", "remote", MideaDevice, "RG57"),  # SmartIR 1395
    ("Hisense", "DGR11R2", "unit", KelonDevice, "dry-grade"),  # SmartIR 1522
    ("Beko", "BXEU 090", "unit", HaierYrw02Device, "A"),  # SmartIR 1603
    ("Electrolux", "EACS-HA", "unit", GreeDevice, "YAW1F"),  # SmartIR 1701
    ("Trotec", "YX1F", "unit", GreeDevice, "YAW1F"),  # SmartIR 1781
    ("Pioneer", "WYS018GMFI17RL", "unit", MideaDevice, "RG57-F"),  # SmartIR 2040
    ("Pioneer", "WYS009GMFI17RL", "unit", MideaDevice, "RG57-F"),  # SmartIR 2040
    ("Pioneer", "CB018GMFILCFHD", "unit", MideaDevice, "RG57-F"),  # SmartIR 2040
    ("Pioneer", "CB012GMFILCFHD", "unit", MideaDevice, "RG57-F"),  # SmartIR 2040
    ("IGC", "RAK-12NH", "unit", KelonDevice, "dry-grade"),  # SmartIR 2200
    ("IGC", "RAK-18NH", "unit", KelonDevice, "dry-grade"),  # SmartIR 2200
    ("Blueridge", "RG57A4", "unit", MideaDevice, "RG57-F"),  # SmartIR 2220
    ("Blueridge", "BGEFU1", "unit", MideaDevice, "RG57-F"),  # SmartIR 2220
    ("Endesa", "DGR11", "unit", KelonDevice, "dry-grade"),  # SmartIR 2500
    ("Goodman", "MSH123E21AXAA", "unit", MideaDevice, "RG57"),  # SmartIR 2900
    ("Goodman", "MST183E20ACAA", "unit", MideaDevice, "RG57"),  # SmartIR 2900
    ("Goodman", "RG57E1/BGEU1", "remote", MideaDevice, "RG57"),  # SmartIR 2900
    (
        "EcoAir",
        "Split Type Wall Air Conditioner",
        "unit",
        MideaDevice,
        "RG57-F",
    ),  # SmartIR 2960
    ("Viessmann", "Vitoclima 300-S", "unit", GreeDevice, "YAW1F-wifi"),  # SmartIR 3040
    ("Hisense", "AS-07UR4SYDD815G", "unit", KelonDevice, "dry-grade"),  # SmartIR 5520
    ("Panasonic", "CS-SA9CKP", "unit", PanasonicAc32Device, None),  # SmartIR 1027
    ("General Electric", "AE1PH09IWF", "unit", KelvinatorDevice, None),  # SmartIR 1041
    ("General Electric", "AE0PH09IWO", "unit", KelvinatorDevice, None),  # SmartIR 1041
    ("General Electric", "AE1PH12IWF", "unit", KelvinatorDevice, None),  # SmartIR 1041
    ("General Electric", "AE0PH12IWO", "unit", KelvinatorDevice, None),  # SmartIR 1041
    ("General Electric", "AE4PH18IWF", "unit", KelvinatorDevice, None),  # SmartIR 1041
    ("General Electric", "AE5PH18IWO", "unit", KelvinatorDevice, None),  # SmartIR 1041
    ("Daikin", "FTXS20LVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXS25LVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXS35LVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXS46LVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXS50LVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXS60LVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXS71LVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXS85LVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXS95LVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FVXS50FV1B", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXL35J2V1B", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXM25UVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXM35UVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXD25DVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXS35G2V1B", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTXM71UVMA", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "FTM09PV2S", "unit", Daikin312Device, None),  # SmartIR 1101
    ("Daikin", "ATX20KV1B", "unit", Daikin312Device, None),  # SmartIR 1106
    ("Daikin", "ATX25KV1B", "unit", Daikin312Device, None),  # SmartIR 1106
    ("Daikin", "ATX35KV1B", "unit", Daikin312Device, None),  # SmartIR 1106
    ("Daikin", "FTXG25EV1BS", "unit", Daikin312Device, None),  # SmartIR 1108
    ("Daikin", "FTXG35EV1BS", "unit", Daikin312Device, None),  # SmartIR 1108
    ("Daikin", "FTXG35EV1BW", "unit", Daikin312Device, None),  # SmartIR 1108
    ("Daikin", "FTC15NV14", "unit", DaikinArcDevice, None),  # SmartIR 1110
    ("Daikin", "FTC20NV14", "unit", DaikinArcDevice, None),  # SmartIR 1110
    ("Daikin", "FTC25NV14", "unit", DaikinArcDevice, None),  # SmartIR 1110
    ("Daikin", "FTC35NV14", "unit", DaikinArcDevice, None),  # SmartIR 1110
    ("Daikin", "ATKC09TV2S", "unit", DaikinArcDevice, None),  # SmartIR 1112
    ("Daikin", "FTKQ12TV2S", "unit", DaikinArcDevice, None),  # SmartIR 1112
    ("Daikin", "FTXM35UVMZ", "unit", Daikin312Device, None),  # SmartIR 1114
    ("Daikin", "DTXF35TVMA", "unit", Daikin312Device, None),  # SmartIR 1117
    ("Daikin", "ARC452A21", "unit", Daikin312Device, None),  # SmartIR 1118
    ("Daikin", "FTXS09LVJU", "unit", Daikin312Device, None),  # SmartIR 1118
    ("Daikin", "FTXS12LVJU", "unit", Daikin312Device, None),  # SmartIR 1118
    ("Daikin", "FTXS15LVJU", "unit", Daikin312Device, None),  # SmartIR 1118
    ("Daikin", "FTXS18LVJU", "unit", Daikin312Device, None),  # SmartIR 1118
    ("Daikin", "FTXS24LVJU", "unit", Daikin312Device, None),  # SmartIR 1118
    ("Daikin", "FTXS60FVMA", "unit", Daikin216Device, None),  # SmartIR 1119
    ("Gree", "GWH18ACD-D3DNA 1M", "unit", GreeDevice, "YAW1F-wifi"),  # SmartIR 1186
    (
        "Toshiba",
        "RAS-13NKV-E / RAS-13NAV-E",
        "unit",
        ToshibaAcDevice,
        None,
    ),  # SmartIR 1260
    (
        "Toshiba",
        "RAS-13NKV-A / RAS-13NAV-A",
        "unit",
        ToshibaAcDevice,
        None,
    ),  # SmartIR 1260
    (
        "Toshiba",
        "RAS-16NKV-E / RAS-16NAV-E",
        "unit",
        ToshibaAcDevice,
        None,
    ),  # SmartIR 1260
    (
        "Toshiba",
        "RAS-16NKV-A / RAS-16NAV-A",
        "unit",
        ToshibaAcDevice,
        None,
    ),  # SmartIR 1260
    ("Toshiba", "RAS-M10SKV-E", "unit", ToshibaAcDevice, None),  # SmartIR 1260
    ("Toshiba", "WH-TA05NE", "unit", ToshibaAcDevice, None),  # SmartIR 1261
    ("Toshiba", "WH-TA11EJ", "unit", ToshibaAcDevice, None),  # SmartIR 1261
    ("Toshiba", "RAC-PD0812CRRU", "unit", MideaDevice, "RG57-F"),  # SmartIR 1262
    ("Toshiba", "RAC-PD1013CWRU", "unit", MideaDevice, "RG57-F"),  # SmartIR 1262
    ("Toshiba", "RAC-PD1213CWRU", "unit", MideaDevice, "RG57-F"),  # SmartIR 1262
    ("Toshiba", "RAC-PD1414CWRU", "unit", MideaDevice, "RG57-F"),  # SmartIR 1262
    ("Toshiba", "RAS-13SKVR-A", "unit", ToshibaAcDevice, None),  # SmartIR 1264
    ("Haier", "HSU-09HPL03/R03", "unit", Haier176Device, "A"),  # SmartIR 1322
    ("Tadiran", "TAC 297H V3.2", "unit", AmcorDevice, None),  # SmartIR 1346
    ("Midea", "42MAQA09S5", "unit", CoolixDevice, None),  # SmartIR 1388
    (
        "Mitsubishi Heavy",
        "SRK25ZJ-S1",
        "unit",
        MitsubishiHeavy88Device,
        None,
    ),  # SmartIR 1680
    (
        "Mitsubishi Heavy",
        "SRK13CRV-S1",
        "unit",
        MitsubishiHeavy88Device,
        None,
    ),  # SmartIR 1680
    (
        "Mitsubishi Heavy",
        "SRK20ZSA-W",
        "unit",
        MitsubishiHeavy152Device,
        None,
    ),  # SmartIR 1686
    (
        "Mitsubishi Heavy",
        "SRK25ZSA-W",
        "unit",
        MitsubishiHeavy152Device,
        None,
    ),  # SmartIR 1686
    (
        "Mitsubishi Heavy",
        "SRK35ZSA-W",
        "unit",
        MitsubishiHeavy152Device,
        None,
    ),  # SmartIR 1686
    (
        "Mitsubishi Heavy",
        "SRK50ZSA-W",
        "unit",
        MitsubishiHeavy152Device,
        None,
    ),  # SmartIR 1686
    (
        "Mitsubishi Heavy",
        "SRK35ZJX-S",
        "unit",
        MitsubishiHeavy88Device,
        None,
    ),  # SmartIR 1687
    (
        "Mitsubishi Heavy",
        "SRK20ZJX-S",
        "unit",
        MitsubishiHeavy88Device,
        None,
    ),  # SmartIR 1687
    (
        "Mitsubishi Heavy",
        "SRK25ZSP-W",
        "unit",
        MitsubishiHeavy88Device,
        None,
    ),  # SmartIR 1688
    (
        "Mitsubishi Heavy",
        "SRK35ZSP-W",
        "unit",
        MitsubishiHeavy88Device,
        None,
    ),  # SmartIR 1688
    (
        "Mitsubishi Heavy",
        "SRK45ZSP-W",
        "unit",
        MitsubishiHeavy88Device,
        None,
    ),  # SmartIR 1688
    (
        "Mitsubishi Heavy",
        "DXK12Z3-S",
        "unit",
        MitsubishiHeavy88Device,
        None,
    ),  # SmartIR 1692
    (
        "Mitsubishi Heavy",
        "DXK09Z5-S",
        "unit",
        MitsubishiHeavy88Device,
        None,
    ),  # SmartIR 1692
    (
        "Mitsubishi Heavy",
        "DXK15Z5-S",
        "unit",
        MitsubishiHeavy88Device,
        None,
    ),  # SmartIR 1692
    ("Kelvinator", "KCV70HRC", "unit", KelvinatorDevice, None),  # SmartIR 1741
    ("Electra", "RC-3", "unit", AirwellDevice, None),  # SmartIR 1946
    ("Mirage", "Magnum Inverter 19", "unit", CoolixDevice, None),  # SmartIR 2100
    ("Hyndai", "H-ARI22-09H", "unit", ElectraAcDevice, "aux"),  # SmartIR 2662
    ("ELGIN", "HVQI12B2FB", "unit", CoolixDevice, None),  # SmartIR 2801
    ("Senville", "SENA/12HF/IZ", "unit", MideaDevice, "RG57"),  # SmartIR 2860
    ("Casper", "SC-09FS32", "unit", ElectraAcDevice, None),  # SmartIR 3240
)

# 0.1.x strings of the devices that were pure Python in 0.1.x.
ALIASES = {
    ("airspool", "generic"): ("Airspool", "AIRSPOOL protocol"),
    ("airspool", "airspool"): ("Airspool", "AIRSPOOL protocol"),
    ("airspool", "airspool mini-split"): ("Airspool", "Mini-split"),
    ("daikin", "generic"): ("Daikin", "DAIKIN_NATIVE protocol"),
    ("daikin", "smash 2"): ("Daikin", "Smash II"),
    ("lg", "generic"): ("LG", "LG_NATIVE protocol"),
    ("lg", "inverter v"): ("LG", "Inverter V"),
    ("lg", "dual inverter"): ("LG", "Dual Inverter"),
    ("panasonic", "generic"): ("Panasonic", "PANASONIC_NATIVE protocol"),
    ("panasonic", "4 way cassette"): ("Panasonic", "4-Way Cassette"),
    ("sharp", "j-tech"): ("Sharp", "J-Tech"),
}
