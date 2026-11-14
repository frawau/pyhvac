from pyhvac import registry
from pyhvac.state import HvacState
from hvacir.cluster import cluster, signature
from hvacir.codes import Code, Key, SmartIRFile


def learned(number, brand, temps=range(17, 27)):
    dev = registry.get_device(brand, registry.models(brand)[0])
    codes = tuple(
        Code(
            Key("cool", "auto", None, float(t)),
            dev.encode(None, HvacState(True, "cool", t)).signal.pulses,
        )
        for t in temps
    )
    return SmartIRFile(
        number,
        brand,
        ("X",),
        "Broadlink",
        "Base64",
        17,
        26,
        1,
        ("cool",),
        ("auto",),
        (),
        codes,
        0,
    )


def test_files_of_one_protocol_share_a_cluster():
    a, b, c = (
        learned(1, "Electra"),
        learned(2, "Electra", range(20, 25)),
        learned(3, "Daikin"),
    )
    assert signature(a) == signature(b) != signature(c)
    clusters = cluster([a, b, c])
    assert [cl.files for cl in clusters] == [(1, 2), (3,)]
    assert clusters[0].codes == 15 and clusters[0].keys == 10
    assert "Protocol(" in clusters[0].draft


def test_a_file_without_codes_is_left_out():
    empty = SmartIRFile(4, "X", (), "", "", None, None, None, (), (), (), (), 3)
    assert signature(empty) is None and cluster([empty]) == []
