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
from .protocols.table import TableDevice
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
    ("Toyotomi", "AKIRA GAN/GAG-A128 VL", "unit", TableDevice, "1000"),  # SmartIR 1000
    ("Toyotomi", "AKIRA GAN/GAG-A135FW-M", "unit", TableDevice, "1001"),  # SmartIR 1001
    ("Panasonic", "CS-CE7HKEW", "unit", TableDevice, "1020"),  # SmartIR 1020
    ("Panasonic", "CS-CE9HKEW", "unit", TableDevice, "1020"),  # SmartIR 1020
    ("Panasonic", "CS-CE12HKEW", "unit", TableDevice, "1020"),  # SmartIR 1020
    ("Panasonic", "CS-PC24MKF", "unit", TableDevice, "1020"),  # SmartIR 1020
    ("Panasonic", "CS-C24PKF", "unit", TableDevice, "1020"),  # SmartIR 1020
    ("Panasonic", "CS-RE9GKE", "unit", TableDevice, "1021"),  # SmartIR 1021
    ("Panasonic", "CS-RE12GKE", "unit", TableDevice, "1021"),  # SmartIR 1021
    ("Panasonic", "CS-RE9PKR", "unit", TableDevice, "1021"),  # SmartIR 1021
    ("Panasonic", "CSCU-Z25TKR", "unit", TableDevice, "1021"),  # SmartIR 1021
    ("Panasonic", "CS-Z25TK", "unit", TableDevice, "1022"),  # SmartIR 1022
    ("Panasonic", "CS-HE9JKE", "unit", TableDevice, "1023"),  # SmartIR 1023
    ("Panasonic", "CS-HE12JKE", "unit", TableDevice, "1023"),  # SmartIR 1023
    ("Panasonic", "CS-HE9LKE", "unit", TableDevice, "1023"),  # SmartIR 1023
    ("Panasonic", "CS-MRE7MKE", "unit", TableDevice, "1024"),  # SmartIR 1024
    ("Panasonic", "CS-E18FKR", "unit", TableDevice, "1025"),  # SmartIR 1025
    ("Panasonic", "CS-PC12QKT", "unit", TableDevice, "1026"),  # SmartIR 1026
    ("Panasonic", "CS-SA9CKP", "unit", TableDevice, "1027"),  # SmartIR 1027
    ("Panasonic", "CS-U9RKR", "unit", TableDevice, "1028"),  # SmartIR 1028
    ("Panasonic", "CS-U12RKR", "unit", TableDevice, "1028"),  # SmartIR 1028
    ("Panasonic", "CS-LJ22~LJ90BA2(YA2)", "unit", TableDevice, "1029"),  # SmartIR 1029
    ("Panasonic", "CS-E12JKDW", "unit", TableDevice, "1030"),  # SmartIR 1030
    (
        "Panasonic",
        "SRK25ZMP-S, SRK35ZMP-S, SRK45ZMP-S",
        "unit",
        TableDevice,
        "1031",
    ),  # SmartIR 1031
    ("Panasonic", "CS-CU-HU18YKYF", "unit", TableDevice, "1032"),  # SmartIR 1032
    ("Ggeneral Electric", "Unknown", "unit", TableDevice, "1040"),  # SmartIR 1040
    ("Ggeneral Electric", "AE1PH09IWF", "unit", TableDevice, "1041"),  # SmartIR 1041
    ("Ggeneral Electric", "AE0PH09IWO", "unit", TableDevice, "1041"),  # SmartIR 1041
    ("Ggeneral Electric", "AE1PH12IWF", "unit", TableDevice, "1041"),  # SmartIR 1041
    ("Ggeneral Electric", "AE0PH12IWO", "unit", TableDevice, "1041"),  # SmartIR 1041
    ("Ggeneral Electric", "AE4PH18IWF", "unit", TableDevice, "1041"),  # SmartIR 1041
    ("Ggeneral Electric", "AE5PH18IWO", "unit", TableDevice, "1041"),  # SmartIR 1041
    ("Ggeneral Electric", "ASHA09LCC", "unit", TableDevice, "1042"),  # SmartIR 1042
    ("General Electric", "ASWX09LECA", "unit", TableDevice, "1043"),  # SmartIR 1043
    ("General Electric", "AHD08LXW1", "unit", TableDevice, "1044"),  # SmartIR 1044
    ("LG", "R09AWN", "unit", TableDevice, "1060"),  # SmartIR 1060
    ("LG", "R24AWN", "unit", TableDevice, "1060"),  # SmartIR 1060
    ("LG", "E09EK", "unit", TableDevice, "1060"),  # SmartIR 1060
    ("LG", "Unknown", "unit", TableDevice, "1061"),  # SmartIR 1061
    ("LG", "P12RK", "unit", TableDevice, "1062"),  # SmartIR 1062
    ("LG", "A06AWV", "unit", TableDevice, "1062"),  # SmartIR 1062
    ("LG", "P12EP1", "unit", TableDevice, "1063"),  # SmartIR 1063
    ("LG", "LG080EC", "unit", TableDevice, "1065"),  # SmartIR 1065
    ("LG", "LG100EC", "unit", TableDevice, "1065"),  # SmartIR 1065
    ("LG", "LG150EC", "unit", TableDevice, "1065"),  # SmartIR 1065
    ("LG", "LG200EC", "unit", TableDevice, "1065"),  # SmartIR 1065
    ("LG", "LA090HYV", "unit", TableDevice, "1066"),  # SmartIR 1066
    ("LG", "LA120HYV", "unit", TableDevice, "1066"),  # SmartIR 1066
    ("LG", "LAN090HYV", "unit", TableDevice, "1066"),  # SmartIR 1066
    ("LG", "LAN120HYV", "unit", TableDevice, "1066"),  # SmartIR 1066
    ("LG", "W12TCM", "unit", LgAcDevice, "GE6711AR2853M"),  # SmartIR 1067
    ("LG", "AKB74295303", "unit", TableDevice, "1068"),  # SmartIR 1068
    ("LG", "AKB74295304", "unit", TableDevice, "1069"),  # SmartIR 1069
    ("LG", "PC09SQ NSJ", "unit", TableDevice, "1070"),  # SmartIR 1070
    ("Hitachi", "RAC-50HK1", "unit", TableDevice, "1080"),  # SmartIR 1080
    ("Hitachi", "RAC-10EH1", "unit", TableDevice, "1081"),  # SmartIR 1081
    ("Hitachi", "RAC-18EH1", "unit", TableDevice, "1081"),  # SmartIR 1081
    ("Hitachi", "RAS-10EH1", "unit", TableDevice, "1081"),  # SmartIR 1081
    ("Hitachi", "RAS-10EH3", "unit", TableDevice, "1081"),  # SmartIR 1081
    ("Hitachi", "RAS-18EH1", "unit", TableDevice, "1081"),  # SmartIR 1081
    ("Hitachi", "RAS-25YHA", "unit", TableDevice, "1082"),  # SmartIR 1082
    ("Hitachi", "RAS-35YHA", "unit", TableDevice, "1082"),  # SmartIR 1082
    ("LG", "RAS-32CNH2", "unit", TableDevice, "1083"),  # SmartIR 1083
    ("Hitachi", "RAS-DX18HDK", "unit", TableDevice, "1084"),  # SmartIR 1084
    ("Hitachi", "RAK-35RPC", "unit", TableDevice, "1084"),  # SmartIR 1084
    ("Hitachi", "RPA24B3BL", "unit", TableDevice, "1085"),  # SmartIR 1085
    ("Hitachi", "RAC-28NK1", "unit", TableDevice, "1086"),  # SmartIR 1086
    ("Hitachi", "RAC-36NK1", "unit", TableDevice, "1086"),  # SmartIR 1086
    ("Hitachi", "RAS-E25YHAB", "unit", TableDevice, "1087"),  # SmartIR 1087
    ("Hitachi", "RAS-E35YHAB", "unit", TableDevice, "1087"),  # SmartIR 1087
    ("Hitachi", "RAS-E50YHAB", "unit", TableDevice, "1087"),  # SmartIR 1087
    ("Hitachi", "RAF-25REX", "unit", TableDevice, "1088"),  # SmartIR 1088
    ("Hitachi", "RAF-35REX", "unit", TableDevice, "1088"),  # SmartIR 1088
    ("Hitachi", "RAF-50REX", "unit", TableDevice, "1088"),  # SmartIR 1088
    ("Hitachi", "RAK-35RXE", "unit", TableDevice, "1089"),  # SmartIR 1089
    ("Hitachi", "RAK-50RPE", "unit", TableDevice, "1090"),  # SmartIR 1090
    ("Hitachi", "HSPE2700FCINV", "unit", TableDevice, "1091"),  # SmartIR 1091
    ("Hitachi", "HSPE3200FCINV", "unit", TableDevice, "1091"),  # SmartIR 1091
    ("Hitachi", "HSPE5400FCINV", "unit", TableDevice, "1091"),  # SmartIR 1091
    ("Hitachi", "HSPE6400FCINV", "unit", TableDevice, "1091"),  # SmartIR 1091
    ("Hitachi", "RAS-E14HB", "unit", TableDevice, "1092"),  # SmartIR 1092
    ("Daikin", "FTXS25CVMB", "unit", TableDevice, "1100"),  # SmartIR 1100
    ("Daikin", "FTXS35CVMB", "unit", TableDevice, "1100"),  # SmartIR 1100
    ("Daikin", "FTXS60BVMB", "unit", TableDevice, "1100"),  # SmartIR 1100
    ("Daikin", "FVXS25BVMB", "unit", TableDevice, "1100"),  # SmartIR 1100
    ("Daikin", "FTXS20LVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXS25LVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXS35LVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXS46LVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXS50LVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXS60LVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXS71LVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXS85LVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXS95LVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FVXS50FV1B", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXL35J2V1B", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXM25UVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXM35UVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXD25DVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXS35G2V1B", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTXM71UVMA", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTM09PV2S", "unit", TableDevice, "1101"),  # SmartIR 1101
    ("Daikin", "FTV20AXV14", "unit", TableDevice, "1102"),  # SmartIR 1102
    ("Daikin", "Unknown", "unit", TableDevice, "1103"),  # SmartIR 1103
    ("Daikin", "TF25DVM", "unit", TableDevice, "1104"),  # SmartIR 1104
    ("Dalkin", "FTX12NMVJU", "unit", TableDevice, "1105"),  # SmartIR 1105
    ("Daikin", "ATX20KV1B", "unit", TableDevice, "1106"),  # SmartIR 1106
    ("Daikin", "ATX25KV1B", "unit", TableDevice, "1106"),  # SmartIR 1106
    ("Daikin", "ATX35KV1B", "unit", TableDevice, "1106"),  # SmartIR 1106
    ("Daikin", "FTX25JAV1NB", "unit", TableDevice, "1107"),  # SmartIR 1107
    ("Daikin", "FTXG25EV1BS", "unit", TableDevice, "1108"),  # SmartIR 1108
    ("Daikin", "FTXG35EV1BS", "unit", TableDevice, "1108"),  # SmartIR 1108
    ("Daikin", "FTXG35EV1BW", "unit", TableDevice, "1108"),  # SmartIR 1108
    ("Daikin", "BRC4C158", "unit", TableDevice, "1109"),  # SmartIR 1109
    ("Daikin", "FTC15NV14", "unit", TableDevice, "1110"),  # SmartIR 1110
    ("Daikin", "FTC20NV14", "unit", TableDevice, "1110"),  # SmartIR 1110
    ("Daikin", "FTC25NV14", "unit", TableDevice, "1110"),  # SmartIR 1110
    ("Daikin", "FTC35NV14", "unit", TableDevice, "1110"),  # SmartIR 1110
    ("Daikin", "FTE09NV25", "unit", TableDevice, "1111"),  # SmartIR 1111
    ("Daikin", "ATKC09TV2S", "unit", TableDevice, "1112"),  # SmartIR 1112
    ("Daikin", "FTKQ12TV2S", "unit", TableDevice, "1112"),  # SmartIR 1112
    ("Daikin", "FTXV35AV1B", "unit", TableDevice, "1113"),  # SmartIR 1113
    ("Daikin", "FTXM35UVMZ", "unit", TableDevice, "1114"),  # SmartIR 1114
    ("Daikin", "ftxb-c", "unit", TableDevice, "1115"),  # SmartIR 1115
    ("Daikin", "FCQ100KAVEA", "unit", TableDevice, "1116"),  # SmartIR 1116
    ("Daikin", "DTXF35TVMA", "unit", TableDevice, "1117"),  # SmartIR 1117
    ("Daikin", "ARC452A21", "unit", TableDevice, "1118"),  # SmartIR 1118
    ("Daikin", "FTXS09LVJU", "unit", TableDevice, "1118"),  # SmartIR 1118
    ("Daikin", "FTXS12LVJU", "unit", TableDevice, "1118"),  # SmartIR 1118
    ("Daikin", "FTXS15LVJU", "unit", TableDevice, "1118"),  # SmartIR 1118
    ("Daikin", "FTXS18LVJU", "unit", TableDevice, "1118"),  # SmartIR 1118
    ("Daikin", "FTXS24LVJU", "unit", TableDevice, "1118"),  # SmartIR 1118
    ("Daikin", "FTXS60FVMA", "unit", TableDevice, "1119"),  # SmartIR 1119
    ("Mitsubishi Electric", "MSZ-GL25VGD", "unit", TableDevice, "1120"),  # SmartIR 1120
    ("Mitsubishi Electric", "MSZ-GL35VGD", "unit", TableDevice, "1120"),  # SmartIR 1120
    ("Mitsubishi Electric", "MSZ-GL42VGD", "unit", TableDevice, "1120"),  # SmartIR 1120
    ("Mitsubishi Electric", "MSZ-GL50VGD", "unit", TableDevice, "1120"),  # SmartIR 1120
    ("Mitsubishi Electric", "MSZ-GL60VGD", "unit", TableDevice, "1120"),  # SmartIR 1120
    ("Mitsubishi Electric", "MSZ-GL71VGD", "unit", TableDevice, "1120"),  # SmartIR 1120
    ("Mitsubishi Electric", "MSZ-GL80VGD", "unit", TableDevice, "1120"),  # SmartIR 1120
    ("Mitsubishi Electric", "MSZ-GA35VA", "unit", TableDevice, "1121"),  # SmartIR 1121
    ("Mitsubishi", "MSZ-AP50VGKD", "unit", TableDevice, "1122"),  # SmartIR 1122
    (
        "Mitsubishi Electric",
        "SRK25ZSX-SRC25ZSX",
        "unit",
        TableDevice,
        "1123",
    ),  # SmartIR 1123
    ("Mitsubishi", "MSZ-SF25VE3", "unit", TableDevice, "1124"),  # SmartIR 1124
    ("Mitsubishi", "MSZ-SF35VE3", "unit", TableDevice, "1124"),  # SmartIR 1124
    ("Mitsubishi", "MSZ-SF42VE3", "unit", TableDevice, "1124"),  # SmartIR 1124
    ("Mitsubishi", "MSZ-SF50VE3", "unit", TableDevice, "1124"),  # SmartIR 1124
    ("Mitsubishi", "MSZ-AP20VG", "unit", TableDevice, "1124"),  # SmartIR 1124
    ("Mitsubishi", "MSZ-AP25VGD", "unit", TableDevice, "1124"),  # SmartIR 1124
    ("Mitsubishi Electric", "MLZ-KP25VF", "unit", TableDevice, "1125"),  # SmartIR 1125
    ("Mitsubishi Electric", "MLZ-KP35VF", "unit", TableDevice, "1125"),  # SmartIR 1125
    ("Mitsubishi Electric", "MLZ-KP50VF", "unit", TableDevice, "1125"),  # SmartIR 1125
    ("Mitsubishi Electric", "MSX09-NV II", "unit", TableDevice, "1126"),  # SmartIR 1126
    ("Mitsubishi Electric", "MSH-07RV", "unit", TableDevice, "1126"),  # SmartIR 1126
    ("Mitsubishi Electric", "MSH-12RV", "unit", TableDevice, "1126"),  # SmartIR 1126
    ("Mitsubishi Electric", "MS-24RV", "unit", TableDevice, "1126"),  # SmartIR 1126
    ("Mitsubishi Electric", "MSZ-HJ25VA", "unit", TableDevice, "1127"),  # SmartIR 1127
    ("Mitsubishi Electric", "MSZ-HJ35VA", "unit", TableDevice, "1128"),  # SmartIR 1128
    ("Mitsubishi Electric", "MSZ-GE22VA", "unit", TableDevice, "1129"),  # SmartIR 1129
    ("Mitsubishi Electric", "MS-SGD18VC", "unit", TableDevice, "1130"),  # SmartIR 1130
    ("Mitsubishi Electric", "PAR-FL32MA", "unit", TableDevice, "1131"),  # SmartIR 1131
    ("Mitsubishi Electric", "MSC-A12YV", "unit", TableDevice, "1132"),  # SmartIR 1132
    (
        "Mitsubishi Electric Starmex",
        "MSXY-FN10VE",
        "unit",
        TableDevice,
        "1133",
    ),  # SmartIR 1133
    (
        "Mitsubishi Electric Starmex",
        "MSXY-FN07VE",
        "unit",
        TableDevice,
        "1133",
    ),  # SmartIR 1133
    (
        "Mitsubishi Electric Starmex",
        "MSXY-FN13VE",
        "unit",
        TableDevice,
        "1133",
    ),  # SmartIR 1133
    (
        "Mitsubishi Electric Starmex",
        "MSXY-FN18VE",
        "unit",
        TableDevice,
        "1133",
    ),  # SmartIR 1133
    ("Mitsubishi Electric", "MG-GN18VF", "unit", TableDevice, "1134"),  # SmartIR 1134
    ("Mitsubishi Electric", "MS-GN18VF", "unit", TableDevice, "1134"),  # SmartIR 1134
    ("Mitsubishi Electric", "MS-GN13VF", "unit", TableDevice, "1134"),  # SmartIR 1134
    ("Mitsubishi", "MSZ-GE60VAD", "unit", TableDevice, "1135"),  # SmartIR 1135
    ("Mitsubishi", "MSZ-GE71VAD", "unit", TableDevice, "1135"),  # SmartIR 1135
    ("Mitsubishi", "MSZ-GE80VAD", "unit", TableDevice, "1135"),  # SmartIR 1135
    ("Mitsubishi Electric", "MSXY-FP10VG", "unit", TableDevice, "1136"),  # SmartIR 1136
    ("Mitsubishi Electric", "MSXY-FP13VG", "unit", TableDevice, "1136"),  # SmartIR 1136
    ("Mitsubishi Electric", "MSXY-FP18VG", "unit", TableDevice, "1136"),  # SmartIR 1136
    ("Mitsubishi Electric", "MSZ-HR35VF", "unit", TableDevice, "1137"),  # SmartIR 1137
    (
        "Mitsubishi Electric",
        "Remote KM09D/166901",
        "unit",
        TableDevice,
        "1138",
    ),  # SmartIR 1138
    ("Mitsubishi", "MLZ-KP09NA2", "unit", TableDevice, "1139"),  # SmartIR 1139
    ("Mitsubishi", "MLZ-KP18NA2", "unit", TableDevice, "1139"),  # SmartIR 1139
    ("Actron", "Unknown", "unit", CoolixDevice, None),  # SmartIR 1140
    ("Carrier", "Unknown", "unit", TableDevice, "1160"),  # SmartIR 1160
    ("Carrier", "40GKX-024RB", "unit", TableDevice, "1161"),  # SmartIR 1161
    ("Carrier", "42TVGS024-703", "unit", TableDevice, "1162"),  # SmartIR 1162
    ("Carrier", "40MAQB12B--3", "unit", TableDevice, "1163"),  # SmartIR 1163
    ("Carrier", "40MAQB18B--3", "unit", TableDevice, "1163"),  # SmartIR 1163
    ("Carrier", "42LUVH025N-1", "unit", TableDevice, "1164"),  # SmartIR 1164
    ("Carrier", "42P250HX", "unit", TableDevice, "1165"),  # SmartIR 1165
    ("Carrier", "53P250HX", "unit", TableDevice, "1165"),  # SmartIR 1165
    ("Carrier", "CS-A121N", "unit", TableDevice, "1166"),  # SmartIR 1166
    ("Gree", "GWH12-KF-K3DNA5G-I", "unit", TableDevice, "1180"),  # SmartIR 1180
    ("Gree", "Unknown", "unit", TableDevice, "1181"),  # SmartIR 1181
    ("Gree", "GMV-R45G/NaB-K", "unit", TableDevice, "1182"),  # SmartIR 1182
    (
        "Gree",
        "Gree Smart inverter models. WiFi off. Health on. Swing modes: [swing]_[led]",
        "unit",
        TableDevice,
        "1183",
    ),  # SmartIR 1183
    ("Gree", "GWH09KF", "unit", TableDevice, "1184"),  # SmartIR 1184
    ("Gree", "GC-EAF09HR", "unit", TableDevice, "1184"),  # SmartIR 1184
    ("Gree", "KFR-50LW", "unit", TableDevice, "1185"),  # SmartIR 1185
    ("Gree", "YAP1F2", "unit", TableDevice, "1185"),  # SmartIR 1185
    ("Gree", "GWH18ACD-D3DNA 1M", "unit", TableDevice, "1186"),  # SmartIR 1186
    ("Gree", "Unknown model", "unit", TableDevice, "1187"),  # SmartIR 1187
    ("Gree", "VIR18HP230V1AH", "unit", TableDevice, "1188"),  # SmartIR 1188
    ("Tosot", "T09H-SJ", "unit", TableDevice, "1200"),  # SmartIR 1200
    ("Sungold", "Unknown", "unit", TableDevice, "1220"),  # SmartIR 1220
    ("Consul", "Unknown", "unit", TableDevice, "1240"),  # SmartIR 1240
    ("Consul", "CBV12CBBNA", "unit", TableDevice, "1241"),  # SmartIR 1241
    ("Consul", "CBY12DBBNA", "unit", TableDevice, "1241"),  # SmartIR 1241
    (
        "Toshiba",
        "RAS-13NKV-E / RAS-13NAV-E",
        "unit",
        TableDevice,
        "1260",
    ),  # SmartIR 1260
    (
        "Toshiba",
        "RAS-13NKV-A / RAS-13NAV-A",
        "unit",
        TableDevice,
        "1260",
    ),  # SmartIR 1260
    (
        "Toshiba",
        "RAS-16NKV-E / RAS-16NAV-E",
        "unit",
        TableDevice,
        "1260",
    ),  # SmartIR 1260
    (
        "Toshiba",
        "RAS-16NKV-A / RAS-16NAV-A",
        "unit",
        TableDevice,
        "1260",
    ),  # SmartIR 1260
    ("Toshiba", "RAS-M10SKV-E", "unit", TableDevice, "1260"),  # SmartIR 1260
    ("Toshiba", "WH-TA05NE", "unit", TableDevice, "1261"),  # SmartIR 1261
    ("Toshiba", "WH-TA11EJ", "unit", TableDevice, "1261"),  # SmartIR 1261
    ("Toshiba", "RAC-PD0812CRRU", "unit", TableDevice, "1262"),  # SmartIR 1262
    ("Toshiba", "RAC-PD1013CWRU", "unit", TableDevice, "1262"),  # SmartIR 1262
    ("Toshiba", "RAC-PD1213CWRU", "unit", TableDevice, "1262"),  # SmartIR 1262
    ("Toshiba", "RAC-PD1414CWRU", "unit", TableDevice, "1262"),  # SmartIR 1262
    ("Toshiba", "RAS-B07J2KVSG-E", "unit", TableDevice, "1263"),  # SmartIR 1263
    ("Toshiba", "RAS-B10J2KVSG-E", "unit", TableDevice, "1263"),  # SmartIR 1263
    ("Toshiba", "RAS-B13J2KVSG-E", "unit", TableDevice, "1263"),  # SmartIR 1263
    ("Toshiba", "RAS-B10SKVP-E", "unit", TableDevice, "1263"),  # SmartIR 1263
    ("Toshiba", "RAS-13SKVR-A", "unit", TableDevice, "1264"),  # SmartIR 1264
    ("Toshiba", "RAS-35SKVP2-ND", "unit", TableDevice, "1265"),  # SmartIR 1265
    ("Fujitsu", "AR-RBE1E", "unit", TableDevice, "1280"),  # SmartIR 1280
    ("Fujitsu", "Unknown", "unit", TableDevice, "1281"),  # SmartIR 1281
    ("Fujitsu", "AR-JW11", "unit", TableDevice, "1282"),  # SmartIR 1282
    ("Fujitsu", "AR-AB5", "unit", TableDevice, "1283"),  # SmartIR 1283
    ("Fujitsu", "AR-RCE1E", "unit", TableDevice, "1285"),  # SmartIR 1285
    ("Fujitsu", "AR-PZ2", "unit", TableDevice, "1285"),  # SmartIR 1285
    ("Fujitsu", "AR-JE5", "unit", TableDevice, "1286"),  # SmartIR 1286
    ("Fujitsu", "ASYG-LMCE", "unit", TableDevice, "1287"),  # SmartIR 1287
    ("Fujitsu", "AR-REM7E", "unit", TableDevice, "1287"),  # SmartIR 1287
    ("Fujitsu", "AR-REW2E", "unit", TableDevice, "1287"),  # SmartIR 1287
    ("Fujitsu", "AR-AB8", "unit", TableDevice, "1288"),  # SmartIR 1288
    ("Fujitsu", "AR-RFL7J", "unit", TableDevice, "1290"),  # SmartIR 1290
    ("Fujitsu", "AR-REF1E", "unit", TableDevice, "1291"),  # SmartIR 1291
    ("Fujitsu", "ASYG18LF", "unit", TableDevice, "1292"),  # SmartIR 1292
    ("Fujitsu", "AR-RY12", "unit", TableDevice, "1292"),  # SmartIR 1292
    ("Fujitsu", "ASYG07LM", "unit", TableDevice, "1293"),  # SmartIR 1293
    ("Fujitsu", "ASYG09LM", "unit", TableDevice, "1293"),  # SmartIR 1293
    ("Sharp", "AY-B22DM", "unit", TableDevice, "1300"),  # SmartIR 1300
    ("Sharp", "AY-X13BE", "unit", TableDevice, "1301"),  # SmartIR 1301
    ("Haier", "Unknown", "unit", TableDevice, "1320"),  # SmartIR 1320
    ("Haier", "Top-Tech 14", "unit", TableDevice, "1321"),  # SmartIR 1321
    ("Haier", "HSU-09HPL03/R03", "unit", TableDevice, "1322"),  # SmartIR 1322
    ("Tadiran", "Unknown", "unit", TableDevice, "1340"),  # SmartIR 1340
    ("Tadiran", "TAC490", "unit", TableDevice, "1341"),  # SmartIR 1341
    ("Tadiran", "Tadiran-10i/15i/inv220a", "unit", TableDevice, "1342"),  # SmartIR 1342
    ("Tadiran", "Alpha Series", "unit", TableDevice, "1343"),  # SmartIR 1343
    ("Tadiran", "Remote Control YB1FA", "unit", TableDevice, "1344"),  # SmartIR 1344
    ("Tadiran", "Tadiran Inverter", "unit", TableDevice, "1344"),  # SmartIR 1344
    ("Tadiran", "TAC 297", "unit", TableDevice, "1345"),  # SmartIR 1345
    ("Tadiran", "TAC 297H V3.2", "unit", TableDevice, "1346"),  # SmartIR 1346
    ("Springer", "Split Hi Wall Maxiflex", "unit", TableDevice, "1360"),  # SmartIR 1360
    ("Midea", "Unknown", "unit", TableDevice, "1380"),  # SmartIR 1380
    ("Midea", "MSY-12HRDN1", "unit", TableDevice, "1382"),  # SmartIR 1382
    ("Midea", "KFR-35G", "unit", TableDevice, "1383"),  # SmartIR 1383
    ("Midea", "MSMACU-18HRFN1-QRD0GW", "unit", TableDevice, "1384"),  # SmartIR 1384
    ("Midea", "R11HG/E", "unit", TableDevice, "1385"),  # SmartIR 1385
    ("Midea", "KFR-32GW", "unit", TableDevice, "1386"),  # SmartIR 1386
    ("Midea", "RG70E/BGEF (Remote)", "unit", TableDevice, "1387"),  # SmartIR 1387
    ("Midea", "42MAQA09S5", "unit", TableDevice, "1388"),  # SmartIR 1388
    ("Midea", "MAP05R1WWT", "unit", TableDevice, "1389"),  # SmartIR 1389
    ("Midea", "RG52C1/BGE (Remote)", "unit", TableDevice, "1390"),  # SmartIR 1390
    ("Midea", "RG58E3/BGEF", "unit", TableDevice, "1391"),  # SmartIR 1391
    ("Midea", "MPD-12CRN7", "unit", TableDevice, "1392"),  # SmartIR 1392
    ("Midea", "MPPHB-09CRN7-QB6-N", "unit", TableDevice, "1393"),  # SmartIR 1393
    ("Midea", "RG70C/BGEF (Remote)", "unit", TableDevice, "1394"),  # SmartIR 1394
    ("Midea", "RG10B(D1)/BGEFU1 (Remote)", "unit", TableDevice, "1395"),  # SmartIR 1395
    ("Samsung", "Unknown", "unit", TableDevice, "1400"),  # SmartIR 1400
    ("Samsung", "AR**HSF/JFS**", "unit", TableDevice, "1401"),  # SmartIR 1401
    ("Samsung", "AR**TSHGAWK", "unit", TableDevice, "1402"),  # SmartIR 1402
    ("Samsung", "AR**TXHZ***", "unit", TableDevice, "1403"),  # SmartIR 1403
    ("Samsung", "AR**TSHZ****", "unit", TableDevice, "1404"),  # SmartIR 1404
    ("Samsung", "AR**TSHQBURN", "unit", TableDevice, "1405"),  # SmartIR 1405
    ("Samsung", "AR**NXWS***", "unit", TableDevice, "1407"),  # SmartIR 1407
    ("Samsung", "AR18HSFSAWKNEU Ver.01", "unit", TableDevice, "1408"),  # SmartIR 1408
    ("Sintech", "KFR-34GW", "unit", TableDevice, "1420"),  # SmartIR 1420
    ("Akai", "Unknown", "unit", TableDevice, "1440"),  # SmartIR 1440
    ("Akai", "TEM-26CHSAAK5", "unit", TableDevice, "1441"),  # SmartIR 1441
    ("Akai", "TEM-70CHSAAK5", "unit", TableDevice, "1441"),  # SmartIR 1441
    ("Akai", "TEM-26CHSAKA5", "unit", TableDevice, "1441"),  # SmartIR 1441
    ("Akai", "TEM-35CHSAKA", "unit", TableDevice, "1441"),  # SmartIR 1441
    ("Akai", "TEM-50CHSAKA", "unit", TableDevice, "1441"),  # SmartIR 1441
    ("Akai", "TEM-35CHSABH", "unit", TableDevice, "1441"),  # SmartIR 1441
    ("Akai", "TEM-35CHSF", "unit", TableDevice, "1441"),  # SmartIR 1441
    ("Alliance", "Unknown", "unit", TableDevice, "1460"),  # SmartIR 1460
    ("Junkers", "Excellence", "unit", TableDevice, "1480"),  # SmartIR 1480
    ("Sanyo", "Unknown", "unit", TableDevice, "1500"),  # SmartIR 1500
    ("Sanyo", "SAP-KR124EHEA", "unit", TableDevice, "1501"),  # SmartIR 1501
    ("Hisense", "Unknown", "unit", TableDevice, "1520"),  # SmartIR 1520
    ("Hisense", "DGR11R2", "unit", TableDevice, "1522"),  # SmartIR 1522
    ("Tadiran", "WIND 3P", "unit", TableDevice, "1560"),  # SmartIR 1560
    ("Chigo", "Unknown", "unit", TableDevice, "1580"),  # SmartIR 1580
    ("Chigo", "ZH/TY-01", "unit", TableDevice, "1581"),  # SmartIR 1581
    ("Chigo", "ZH/TT-14", "unit", TableDevice, "1582"),  # SmartIR 1582
    ("Beko", "BEVCA 120", "unit", TableDevice, "1600"),  # SmartIR 1600
    ("Beko", "BPAK 120", "unit", TableDevice, "1601"),  # SmartIR 1601
    ("Beko", "BXK 120", "unit", TableDevice, "1602"),  # SmartIR 1602
    ("Beko", "BXEU 090", "unit", TableDevice, "1603"),  # SmartIR 1603
    ("Beko", "BPEU 120", "unit", TableDevice, "1604"),  # SmartIR 1604
    ("Tornado", "Super - Inverter A, i", "unit", TableDevice, "1620"),  # SmartIR 1620
    ("Tornado", "Inverter", "unit", TableDevice, "1620"),  # SmartIR 1620
    ("Tornado", "Inverter A", "unit", TableDevice, "1620"),  # SmartIR 1620
    ("Tornado", "Super Design", "unit", TableDevice, "1620"),  # SmartIR 1620
    ("Tornado", "Super Plasma", "unit", TableDevice, "1620"),  # SmartIR 1620
    ("Tornado", "Gold i", "unit", TableDevice, "1620"),  # SmartIR 1620
    ("Tornado", "Multi ON-OFF", "unit", TableDevice, "1620"),  # SmartIR 1620
    ("Tornado", "Multi Inverter", "unit", TableDevice, "1620"),  # SmartIR 1620
    ("Tornado", "Super Gold i", "unit", TableDevice, "1620"),  # SmartIR 1620
    ("Tornado", "Plasma Gold", "unit", TableDevice, "1620"),  # SmartIR 1620
    ("Tornado", "Super Legend 40", "unit", TableDevice, "1621"),  # SmartIR 1621
    ("Tornado", "Master-22 X", "unit", TableDevice, "1622"),  # SmartIR 1622
    ("Tornado", "Inverter VRF", "unit", TableDevice, "1623"),  # SmartIR 1623
    ("Tornado", "Inverter VRF BOX", "unit", TableDevice, "1625"),  # SmartIR 1625
    ("Tornado", "MASTER-35 X 1PH", "unit", TableDevice, "1626"),  # SmartIR 1626
    ("Tornado", "MASTER-12A PLUS", "unit", TableDevice, "1627"),  # SmartIR 1627
    ("FUJIKO", "Unknown", "unit", TableDevice, "1640"),  # SmartIR 1640
    ("ROYAL", "08HPN1T1", "unit", TableDevice, "1660"),  # SmartIR 1660
    ("ROYAL", "RC-G25HN", "unit", TableDevice, "1661"),  # SmartIR 1661
    ("Mitsubishi Heavy", "SRK25ZJ-S1", "unit", TableDevice, "1680"),  # SmartIR 1680
    ("Mitsubishi Heavy", "SRK13CRV-S1", "unit", TableDevice, "1680"),  # SmartIR 1680
    ("Mitsubishi Heavy", "SRK71ZK-S", "unit", TableDevice, "1681"),  # SmartIR 1681
    ("Mitsubishi Heavy", "SRKM25H", "unit", TableDevice, "1682"),  # SmartIR 1682
    ("Mitsubishi Heavy", "SRK40HBE", "unit", TableDevice, "1682"),  # SmartIR 1682
    ("Mitsubishi Heavy", "RKS502A502", "unit", TableDevice, "1682"),  # SmartIR 1682
    ("Mitsubishi Heavy", "RKS502A503", "unit", TableDevice, "1682"),  # SmartIR 1682
    ("Mitsubishi Heavy", "DXK12ZMA-S", "unit", TableDevice, "1683"),  # SmartIR 1683
    (
        "Mitsubishi Heavy Industries",
        "DXK24ZRA",
        "unit",
        TableDevice,
        "1684",
    ),  # SmartIR 1684
    ("Mitsubishi Heavy", "SRK50ZS-S", "unit", TableDevice, "1685"),  # SmartIR 1685
    ("Mitsubishi Heavy", "SRK20ZSA-W", "unit", TableDevice, "1686"),  # SmartIR 1686
    ("Mitsubishi Heavy", "SRK25ZSA-W", "unit", TableDevice, "1686"),  # SmartIR 1686
    ("Mitsubishi Heavy", "SRK35ZSA-W", "unit", TableDevice, "1686"),  # SmartIR 1686
    ("Mitsubishi Heavy", "SRK50ZSA-W", "unit", TableDevice, "1686"),  # SmartIR 1686
    ("Mitsubishi Heavy", "SRK35ZJX-S", "unit", TableDevice, "1687"),  # SmartIR 1687
    ("Mitsubishi Heavy", "SRK20ZJX-S", "unit", TableDevice, "1687"),  # SmartIR 1687
    ("Mitsubishi Heavy", "SRK25ZSP-W", "unit", TableDevice, "1688"),  # SmartIR 1688
    ("Mitsubishi Heavy", "SRK35ZSP-W", "unit", TableDevice, "1688"),  # SmartIR 1688
    ("Mitsubishi Heavy", "SRK45ZSP-W", "unit", TableDevice, "1688"),  # SmartIR 1688
    ("Mitsubishi Heavy", "DXK12ZSA-W", "unit", TableDevice, "1689"),  # SmartIR 1689
    ("Mitsubishi Heavy", "FDUM VF2", "unit", TableDevice, "1690"),  # SmartIR 1690
    ("Mitsubishi Heavy", "SRK71ZRA-W", "unit", TableDevice, "1691"),  # SmartIR 1691
    ("Mitsubishi Heavy", "DXK12Z3-S", "unit", TableDevice, "1692"),  # SmartIR 1692
    ("Mitsubishi Heavy", "DXK09Z5-S", "unit", TableDevice, "1692"),  # SmartIR 1692
    ("Mitsubishi Heavy", "DXK15Z5-S", "unit", TableDevice, "1692"),  # SmartIR 1692
    ("Electrolux", "EACS/I-HAT/N3", "unit", CoolixDevice, None),  # SmartIR 1700
    ("Electrolux", "EACS-HA", "unit", TableDevice, "1701"),  # SmartIR 1701
    ("Electrolux", "QI/QE09F", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "QI/QE09R", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "QI/QE12F", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "QI/QE12R", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "QI/QE18F", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "QI/QE18R", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "QI/QE22F", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "QI/QE22R", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "XI/XE09F", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "XI/XE09R", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "XI/XE12F", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "XI/XE12R", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "XI/XE18F", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "XI/XE18R", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "XI/XE22F", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "XI/XE22R", "unit", TableDevice, "1702"),  # SmartIR 1702
    ("Electrolux", "EXP26U758CW", "unit", TableDevice, "1703"),  # SmartIR 1703
    ("Electrolux", "EPI12LEIWI", "unit", TableDevice, "1704"),  # SmartIR 1704
    ("Electrolux", "EACM-10 HR/N3", "unit", TableDevice, "1705"),  # SmartIR 1705
    ("Erisson", "EC-S07T2", "unit", TableDevice, "1720"),  # SmartIR 1720
    ("Kelvinator", "KSV25HRG", "unit", TableDevice, "1740"),  # SmartIR 1740
    ("Kelvinator", "KCV70HRC", "unit", TableDevice, "1741"),  # SmartIR 1741
    ("Daitsu", "DS12U-RV", "unit", TableDevice, "1760"),  # SmartIR 1760
    ("Daitsu", "DS-9KIDT", "unit", TableDevice, "1761"),  # SmartIR 1761
    ("Daitsu", "ASD9KI-DT", "unit", TableDevice, "1762"),  # SmartIR 1762
    ("Daitsu", "DOS12KIDB", "unit", TableDevice, "1763"),  # SmartIR 1763
    ("Daitsu", "DS-12KIDC(WD)", "unit", TableDevice, "1764"),  # SmartIR 1764
    ("Trotec", "YX1F6", "unit", TableDevice, "1780"),  # SmartIR 1780
    ("Trotec", "YX1F", "unit", TableDevice, "1781"),  # SmartIR 1781
    ("Trotec", "PAC 2600 X", "unit", TableDevice, "1782"),  # SmartIR 1782
    ("Ballu", "YKR-K/002E", "unit", TableDevice, "1800"),  # SmartIR 1800
    ("Ballu", "BSD/in-09HN1_20Y", "unit", TableDevice, "1801"),  # SmartIR 1801
    ("Riello", "WSI XN", "unit", TableDevice, "1820"),  # SmartIR 1820
    ("Riello", "RAR-3U4", "unit", TableDevice, "1820"),  # SmartIR 1820
    ("Hualing", "KFR-45GW/JNV", "unit", TableDevice, "1840"),  # SmartIR 1840
    ("Hualing", "KFR-45G/JNV", "unit", TableDevice, "1840"),  # SmartIR 1840
    ("Simbio", "Unknown", "unit", TableDevice, "1860"),  # SmartIR 1860
    ("Saunier Duval", "1", "unit", TableDevice, "1880"),  # SmartIR 1880
    ("TCL", "TAC-12CHSD/XA21I", "unit", TableDevice, "1900"),  # SmartIR 1900
    ("TCL", "TAC-12CHSD/XA71IN", "unit", TableDevice, "1901"),  # SmartIR 1901
    ("Aokesi", "Unknown", "unit", TableDevice, "1920"),  # SmartIR 1920
    ("Electra", "Unknown", "unit", TableDevice, "1940"),  # SmartIR 1940
    ("Electra", "Electra Classic", "unit", TableDevice, "1942"),  # SmartIR 1942
    (
        "Electra",
        "Electra Platinum Plus Inverter",
        "unit",
        TableDevice,
        "1944",
    ),  # SmartIR 1944
    ("Electra", "Electra", "unit", TableDevice, "1945"),  # SmartIR 1945
    ("Electra", "RC-3", "unit", TableDevice, "1946"),  # SmartIR 1946
    ("Electra", "Classic 10", "unit", TableDevice, "1948"),  # SmartIR 1948
    ("AUX", "Unknown", "unit", TableDevice, "1960"),  # SmartIR 1960
    ("AUX", "AUX FREEDOM AUX-09FH", "unit", TableDevice, "1961"),  # SmartIR 1961
    ("AUX", "iClima ICI-09A", "unit", TableDevice, "1962"),  # SmartIR 1962
    ("AUX", "Kendal Split Inverter", "unit", TableDevice, "1963"),  # SmartIR 1963
    ("Fuji", "Unknown", "unit", FujitsuAcDevice, "ARDB1"),  # SmartIR 1980
    ("Aeronik", "ASO-12IL", "unit", TableDevice, "2000"),  # SmartIR 2000
    ("Aeronik", "ASI-12IL", "unit", TableDevice, "2000"),  # SmartIR 2000
    ("Ariston", "A-IFWHxx-IGX", "unit", TableDevice, "2020"),  # SmartIR 2020
    ("Pioneer", "WYS018GMFI17RL", "unit", TableDevice, "2040"),  # SmartIR 2040
    ("Pioneer", "WYS009GMFI17RL", "unit", TableDevice, "2040"),  # SmartIR 2040
    ("Pioneer", "CB018GMFILCFHD", "unit", TableDevice, "2040"),  # SmartIR 2040
    ("Pioneer", "CB012GMFILCFHD", "unit", TableDevice, "2040"),  # SmartIR 2040
    ("Pioneer", "WT018GLFI19HLD", "unit", TableDevice, "2041"),  # SmartIR 2041
    ("Dimplex", "GDPAC12RC", "unit", TableDevice, "2060"),  # SmartIR 2060
    ("Sendo", "SND-18/IK", "unit", TableDevice, "2080"),  # SmartIR 2080
    ("Mirage", "Magnum Inverter 19", "unit", TableDevice, "2100"),  # SmartIR 2100
    ("Technibel", "MPAF13A0R5IAA", "unit", TableDevice, "2120"),  # SmartIR 2120
    ("Unionaire", "Artify", "unit", TableDevice, "2140"),  # SmartIR 2140
    ("Lennox", "2018", "unit", TableDevice, "2160"),  # SmartIR 2160
    ("Lennox", "2019", "unit", TableDevice, "2160"),  # SmartIR 2160
    ("Lennox", "LNMTE026V2", "unit", TableDevice, "2161"),  # SmartIR 2161
    ("Lennox", "LNINVE052", "unit", TableDevice, "2162"),  # SmartIR 2162
    ("Lennox", "LNINVC052", "unit", TableDevice, "2162"),  # SmartIR 2162
    ("Hokkaido", "LA09-DUAL H1", "unit", TableDevice, "2180"),  # SmartIR 2180
    ("IGC", "RAK-12NH", "unit", TableDevice, "2200"),  # SmartIR 2200
    ("IGC", "RAK-18NH", "unit", TableDevice, "2200"),  # SmartIR 2200
    ("Blueridge", "RG57A4", "unit", TableDevice, "2220"),  # SmartIR 2220
    ("Blueridge", "BGEFU1", "unit", TableDevice, "2220"),  # SmartIR 2220
    ("De'Longhi", "PAC N82ECO", "unit", TableDevice, "2240"),  # SmartIR 2240
    ("De'Longhi", "PAC AN111", "unit", TableDevice, "2240"),  # SmartIR 2240
    ("De'Longhi", "PAC EM77", "unit", TableDevice, "2241"),  # SmartIR 2241
    ("De'Longhi", "PAC AN140HPEW", "unit", TableDevice, "2242"),  # SmartIR 2242
    ("De'Longhi", "DL3000", "unit", TableDevice, "2243"),  # SmartIR 2243
    ("Profio", "Unknown", "unit", TableDevice, "2260"),  # SmartIR 2260
    ("Hantech", "A018-12KR2", "unit", TableDevice, "2280"),  # SmartIR 2280
    ("Hantech", "A016-09KR2/A", "unit", TableDevice, "2281"),  # SmartIR 2281
    ("Zanussi", "ZH/TT-02", "unit", TableDevice, "2300"),  # SmartIR 2300
    ("Zanussi", "ZACS/I-07 HPF/A17/N1", "unit", TableDevice, "2301"),  # SmartIR 2301
    ("Whynter", "ARC-08WB", "unit", TableDevice, "2320"),  # SmartIR 2320
    ("Whynter", "ARC-10WB", "unit", TableDevice, "2320"),  # SmartIR 2320
    ("Whynter", "ARC-126MD", "unit", TableDevice, "2320"),  # SmartIR 2320
    ("Whynter", "ARC-126MDB", "unit", TableDevice, "2320"),  # SmartIR 2320
    ("Whynter", "ARC-148MS", "unit", TableDevice, "2320"),  # SmartIR 2320
    ("Whynter", "ARC-12S", "unit", TableDevice, "2321"),  # SmartIR 2321
    ("Whynter", "ARC-12SD", "unit", TableDevice, "2321"),  # SmartIR 2321
    ("Whynter", "ARC-122DS", "unit", TableDevice, "2321"),  # SmartIR 2321
    ("Whynter", "ARC-14S", "unit", TableDevice, "2321"),  # SmartIR 2321
    ("Whynter", "ARC-141BG", "unit", TableDevice, "2321"),  # SmartIR 2321
    ("Whynter", "ARC-143MX", "unit", TableDevice, "2321"),  # SmartIR 2321
    ("Whynter", "ARC-101CW", "unit", TableDevice, "2321"),  # SmartIR 2321
    ("Vortex", "VOR-12C3/407", "unit", TableDevice, "2340"),  # SmartIR 2340
    ("Flouu", "Unknown", "unit", TableDevice, "2360"),  # SmartIR 2360
    ("BAXI", "Unknow", "unit", TableDevice, "2380"),  # SmartIR 2380
    ("Yamatsu", "YAM-12KDA", "unit", TableDevice, "2400"),  # SmartIR 2400
    ("Yamatsu", "AUS-07C53R013L24", "unit", TableDevice, "2400"),  # SmartIR 2400
    ("VS", "Unknown", "unit", TableDevice, "2420"),  # SmartIR 2420
    ("Vaillant", "ClimaVair VAI 8-025", "unit", TableDevice, "2440"),  # SmartIR 2440
    ("FanWorld", "FW6-3000", "unit", TableDevice, "2460"),  # SmartIR 2460
    ("Rotenso", "Ukura", "unit", TableDevice, "2480"),  # SmartIR 2480
    ("Rotenso", "Maze (remote)", "unit", TableDevice, "2480"),  # SmartIR 2480
    ("Endesa", "DGR11", "unit", TableDevice, "2500"),  # SmartIR 2500
    ("Galanz", "GZ-1002B-E3", "unit", TableDevice, "2520"),  # SmartIR 2520
    ("Audinac", "SP3500", "unit", TableDevice, "2540"),  # SmartIR 2540
    ("Mistral", "MPAC15CY28", "unit", TableDevice, "2560"),  # SmartIR 2560
    ("KOREL", "KSAL2-09DCEH", "unit", TableDevice, "2580"),  # SmartIR 2580
    ("Equation", "RCH-143", "unit", TableDevice, "2600"),  # SmartIR 2600
    ("Komeco", "Unknown", "unit", TableDevice, "2620"),  # SmartIR 2620
    ("Fisher", "FPR-91DE4-R", "unit", TableDevice, "2640"),  # SmartIR 2640
    ("Fisher", "FPR-121DE4-R", "unit", TableDevice, "2640"),  # SmartIR 2640
    ("Fisher", "FPR-141DE4-R", "unit", TableDevice, "2640"),  # SmartIR 2640
    ("Fisher", "FSOAI-SU-90AE2", "unit", TableDevice, "2641"),  # SmartIR 2641
    ("Hyundai", "HSE09PH5V", "unit", TableDevice, "2660"),  # SmartIR 2660
    ("Hyundai", "HY6INV", "unit", TableDevice, "2661"),  # SmartIR 2661
    ("Hyndai", "H-ARI22-09H", "unit", TableDevice, "2662"),  # SmartIR 2662
    ("Kolin", "RC-M7B1 (remote)", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-D201", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-D252", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-D562", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-D912", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-D202", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-D322", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-D632", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-20D", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-D362", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-D682", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-25D", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-D452", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("Kolin", "KSA-D782", "unit", TableDevice, "2700"),  # SmartIR 2700
    ("AEG", "AXP35U538CW", "unit", TableDevice, "2720"),  # SmartIR 2720
    ("Bosch", "5000i", "unit", TableDevice, "2740"),  # SmartIR 2740
    ("Tristar", "AC-5400", "unit", TableDevice, "2760"),  # SmartIR 2760
    ("Xiaomi", "KFR-35G/F3C1", "unit", TableDevice, "2780"),  # SmartIR 2780
    ("ELGIN", "HVQI18B2IA", "unit", TableDevice, "2800"),  # SmartIR 2800
    ("ELGIN", "HVQI12B2FB", "unit", TableDevice, "2801"),  # SmartIR 2801
    ("Pearl", "EXGC24FCBC1", "unit", TableDevice, "2820"),  # SmartIR 2820
    ("HTW", "HTWS035IX21D2-R32-I", "unit", TableDevice, "2840"),  # SmartIR 2840
    ("Senville", "SENA/12HF/IZ", "unit", TableDevice, "2860"),  # SmartIR 2860
    ("Bora", "18SRA-HE", "unit", TableDevice, "2880"),  # SmartIR 2880
    ("Goodman", "MSH123E21AXAA", "unit", TableDevice, "2900"),  # SmartIR 2900
    ("Goodman", "MST183E20ACAA", "unit", TableDevice, "2900"),  # SmartIR 2900
    ("Goodman", "RG57E1/BGEU1 (remote)", "unit", TableDevice, "2900"),  # SmartIR 2900
    ("Best", "BSTS18CNE2", "unit", TableDevice, "2920"),  # SmartIR 2920
    ("SAGA", "SAGA-A-22(CH)", "unit", TableDevice, "2940"),  # SmartIR 2940
    (
        "EcoAir",
        "Split Type Wall Air Conditioner",
        "unit",
        TableDevice,
        "2960",
    ),  # SmartIR 2960
    ("Agratto", "ECST12FR4-02", "unit", TableDevice, "2980"),  # SmartIR 2980
    ("Agratto", "ECST19QFIR4-02", "unit", TableDevice, "2980"),  # SmartIR 2980
    ("Philco", "Philco AC", "unit", TableDevice, "3000"),  # SmartIR 3000
    ("Klasse", "DOZ-S06JT", "unit", TableDevice, "3020"),  # SmartIR 3020
    ("Viessmann", "Vitoclima 300-S", "unit", TableDevice, "3040"),  # SmartIR 3040
    ("HappyTree", "TAC-12CHSD/XA81", "unit", TableDevice, "3060"),  # SmartIR 3060
    (
        "Voltas",
        "VOLTAS INV/AC 1.5T 183V MZJ3 3S",
        "unit",
        TableDevice,
        "3080",
    ),  # SmartIR 3080
    (
        "Cecotec",
        "EnergySilence 12000 AirClima (05290)",
        "unit",
        TableDevice,
        "3100",
    ),  # SmartIR 3100
    ("Cooper & Hunter", "Unknown", "unit", TableDevice, "3120"),  # SmartIR 3120
    ("Argo", "Ulisse13", "unit", TableDevice, "3140"),  # SmartIR 3140
    ("AquaThermal", "LM AURI-12", "unit", TableDevice, "3160"),  # SmartIR 3160
    ("Devanti", "WAC-05C-WH", "unit", TableDevice, "3180"),  # SmartIR 3180
    ("Friedrich", "CP12G10B", "unit", TableDevice, "3200"),  # SmartIR 3200
    ("Mundoclima", "MUPR-09-H9A", "unit", TableDevice, "3220"),  # SmartIR 3220
    ("Mundoclima", "MUPR-12-H9A", "unit", TableDevice, "3220"),  # SmartIR 3220
    ("Mundoclima", "MUPR-18-H9A", "unit", TableDevice, "3220"),  # SmartIR 3220
    ("Mundoclima", "MUPR-24-H9A", "unit", TableDevice, "3220"),  # SmartIR 3220
    ("Mundoclima", "MUPR-09-H5A", "unit", TableDevice, "3220"),  # SmartIR 3220
    ("Mundoclima", "MUPR-12-H5A", "unit", TableDevice, "3220"),  # SmartIR 3220
    ("Mundoclima", "MUPR-18-H5A", "unit", TableDevice, "3220"),  # SmartIR 3220
    ("Mundoclima", "MUPR-24-H5A", "unit", TableDevice, "3220"),  # SmartIR 3220
    ("Casper", "SC-09FS32", "unit", TableDevice, "3240"),  # SmartIR 3240
    ("PARKAIR", "DI-A", "unit", TableDevice, "3300"),  # SmartIR 3300
    ("Chunlan", "KFR-25GW/VW (CH-9)", "unit", TableDevice, "3320"),  # SmartIR 3320
    ("Wide", "WDS12ECO", "unit", TableDevice, "3340"),  # SmartIR 3340
    ("Kaden", "KS09", "unit", TableDevice, "3360"),  # SmartIR 3360
    ("Kaden", "KS12", "unit", TableDevice, "3360"),  # SmartIR 3360
    ("Kaden", "KS18", "unit", TableDevice, "3360"),  # SmartIR 3360
    ("Kaden", "KS24", "unit", TableDevice, "3360"),  # SmartIR 3360
    ("Kaden", "KS28", "unit", TableDevice, "3360"),  # SmartIR 3360
    ("Zephir", "DualSplit", "unit", TableDevice, "3380"),  # SmartIR 3380
    ("Daikin", "ARC433B51", "unit", TableDevice, "5120"),  # SmartIR 5120
    ("Mitsubishi Electric", "MSC-A12WV", "unit", TableDevice, "5140"),  # SmartIR 5140
    ("Hisense", "AS-07UR4SYDD815G", "unit", TableDevice, "5520"),  # SmartIR 5520
    (
        "Toshiba",
        "RAS-18NKV-E / RAS-18NAV-E",
        "unit",
        TableDevice,
        "7260",
    ),  # SmartIR 7260
    ("Sharp", "AH-AP9GMY", "unit", TableDevice, "7300"),  # SmartIR 7300
    ("Kelvinator", "KSV25HWH", "unit", TableDevice, "7740"),  # SmartIR 7740
    ("Family", "12WIFI", "unit", TableDevice, "7741"),  # SmartIR 7741
    ("Kolin", "KAG-145RSINV", "unit", TableDevice, "8700"),  # SmartIR 8700
    ("Viomi", "KF-26GW/Y4PF5-A5", "unit", TableDevice, "8720"),  # SmartIR 8720
    ("Sigma", "SGS32H13NE", "unit", TableDevice, "8800"),  # SmartIR 8800
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
