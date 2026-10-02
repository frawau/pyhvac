import pytest

from pyhvac import registry


def test_brands_are_listed_as_manufacturers_write_them():
    names = registry.brands()
    assert "Mitsubishi Heavy Industries" in names and names == sorted(
        names, key=str.casefold
    )


def test_lookup_ignores_case_spaces_and_punctuation():
    a = registry.get_device(
        "mitsubishi_heavy_industries", registry.models("Mitsubishi Heavy Industries")[0]
    )
    assert a.brand == "Mitsubishi Heavy Industries"


def test_unknown_brand_or_model():
    with pytest.raises(KeyError, match="unknown brand"):
        registry.get_device("nope", "x")
    with pytest.raises(KeyError, match="unknown model"):
        registry.get_device("Daikin", "nope")


def test_model_may_be_left_out_only_for_single_model_brands():
    single = next(b for b in registry.brands() if len(registry.models(b)) == 1)
    assert registry.get_device(single).brand == single
    several = next(b for b in registry.brands() if len(registry.models(b)) > 1)
    with pytest.raises(KeyError, match="several models"):
        registry.get_device(several)


def test_variant_of_reads_the_brands_table():
    from pyhvac.protocols.coolix import CoolixDevice

    assert registry.variant_of(CoolixDevice, "kelvinator", "KSV25HRG") == "quiet"
    assert registry.variant_of(CoolixDevice, "Beko", "BINR 070/071") is None
    assert registry.variant_of(CoolixDevice, "Nobody", "nothing") is None
