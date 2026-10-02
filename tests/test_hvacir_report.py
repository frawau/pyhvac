import dataclasses

import pytest

from hvacir.codes import Code, Key, SmartIRFile
from hvacir.match import Match
from hvacir.report import Row, markdown, python_rows, rows

CODE = (Code(Key("cool", "low", None, 20.0), (500, 500)),)


def file(number, brand, *models, codes=CODE):
    return SmartIRFile(
        number,
        brand,
        models,
        "Broadlink",
        "Base64",
        16,
        30,
        1,
        ("cool",),
        ("low",),
        (),
        codes,
        0,
    )


def test_only_covered_files_become_rows():
    results = [
        (file(1, "Acme", "A-1"), Match("covered", "Haier176Device/B")),
        (file(2, "acme", "B-2"), Match("near", "ElectraAcDevice")),
        (file(3, "Acme", "C-3"), Match("unknown")),
        (file(4, "Acme", "D-4"), Match("unsupported")),
    ]
    new, conflicts = rows(results)
    assert new == [
        Row("Acme", "A-1", "Haier176Device", "B", 1),
    ]
    assert conflicts == []


def test_existing_names_skip_or_conflict():
    results = [
        (file(5, "electra", "AXW12DCS"), Match("covered", "ElectraAcDevice")),
        (file(6, "Electra", "Classic INV 17"), Match("covered", "CoolixDevice")),
    ]
    new, conflicts = rows(results)
    assert new == []
    assert [(r.source, why) for r, why in conflicts] == [
        (6, "name taken by ElectraAcDevice/None")
    ]


def test_the_brand_keeps_pyhvacs_spelling():
    new, _ = rows(
        [
            (
                file(7, "MITSUBISHI HEAVY INDUSTRIES", "X9"),
                Match("covered", "CoolixDevice"),
            )
        ]
    )
    assert new[0].brand == "Mitsubishi Heavy Industries"


def test_a_file_without_models_is_named_after_its_brand():
    new, _ = rows([(file(8, "Acme"), Match("covered", "CoolixDevice"))])
    assert (new[0].brand, new[0].model) == ("Acme", "Acme")


@pytest.mark.parametrize("unknown", ["Unknown", "Unknow"])
def test_an_unknown_model_is_named_after_its_brand(unknown):
    new, _ = rows([(file(8, "Acme", unknown), Match("covered", "CoolixDevice"))])
    assert (new[0].brand, new[0].model) == ("Acme", "Acme")


def test_an_unknown_model_of_a_brand_with_that_device_is_skipped():
    new, conflicts = rows(
        [(file(8, "Beko", "Unknown"), Match("covered", "CoolixDevice"))]
    )
    assert (new, conflicts) == ([], [])


@pytest.mark.parametrize(
    "spelled, brand", [("Ggeneral Electric", "General Electric"), ("Fuji", "Fujitsu")]
)
def test_brand_spellings_are_corrected(spelled, brand):
    new, _ = rows([(file(8, spelled, "X-1"), Match("covered", "CoolixDevice"))])
    assert new[0].brand == brand


def test_fuji_unknown_is_fujitsus_existing_device():
    new, conflicts = rows(
        [(file(1980, "Fuji", "Unknown"), Match("covered", "FujitsuAcDevice/ARDB1"))]
    )
    assert (new, conflicts) == ([], [])


@pytest.mark.parametrize("model", ["RG70E/BGEF (Remote)", "Maze (remote)"])
def test_a_remote_named_as_such_is_a_remote_row(model):
    new, _ = rows([(file(8, "Acme", model), Match("covered", "CoolixDevice"))])
    assert (new[0].model, new[0].kind) == (model.rsplit(" (", 1)[0], "remote")


def test_rows_are_python():
    text = python_rows([Row("Acme", "A-1", "Haier176Device", "B", 1)])
    assert text == "    ('Acme', 'A-1', 'unit', Haier176Device, 'B'),  # SmartIR 1\n"
    remote = Row("Acme", "R-1", "CoolixDevice", None, 2, kind="remote")
    assert python_rows([remote]).startswith("    ('Acme', 'R-1', 'remote',")


def test_markdown_lists_every_file():
    results = [(file(1, "Acme", "A-1"), Match("near", "X", gaps={"fan": 3}))]
    text = markdown(results, [], [], [])
    assert "| 1 | Acme | near | X |" in text and "fan (3)" in text


def test_files_that_are_not_json_are_listed():
    assert "- not JSON: 2680" in markdown([], [], [], [], [2680])


def test_a_file_with_many_unreadable_codes_is_flagged():
    f = dataclasses.replace(file(9, "Acme", "A"), skipped=1)
    assert "| 1 (!) |" in markdown([(f, Match("unknown"))], [], [], [])


def test_the_report_lists_files_that_are_not_json(tmp_path):
    from hvacir.report import main

    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "2680.json").write_text("{not json")
    main([str(tmp_path / "out"), "--cache", str(cache), "--no-fetch", "--jobs", "1"])
    assert "- not JSON: 2680" in (tmp_path / "out" / "report.md").read_text()


def test_markdown_shows_codes_filed_under_another_state():
    results = [
        (file(1, "Acme", "A-1"), Match("covered", "X", verified=5, relabelled=2))
    ]
    assert "| 5 | 2 |" in markdown(results, [], [], [])
