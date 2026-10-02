import dataclasses

from smartir.codes import Code, Key, SmartIRFile
from smartir.match import Match
from smartir.report import Row, markdown, python_rows, rows

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


def test_covered_files_name_their_candidate_others_are_tables():
    results = [
        (file(1, "Acme", "A-1"), Match("covered", "Haier176Device/B")),
        (file(2, "acme", "B-2"), Match("near", "ElectraAcDevice")),
        (file(3, "Acme", "C-3"), Match("unknown")),
        (file(4, "Acme", "D-4"), Match("unsupported")),
    ]
    new, conflicts = rows(results)
    assert new == [
        Row("Acme", "A-1", "Haier176Device", "B", 1, "covered"),
        Row("Acme", "B-2", "TableDevice", "2", 2, "near"),
        Row("Acme", "C-3", "TableDevice", "3", 3, "unknown"),
    ]
    assert conflicts == []


def test_existing_names_skip_or_conflict():
    results = [
        (file(5, "electra", "AXW12DCS"), Match("covered", "ElectraAcDevice")),
        (file(6, "Electra", "Classic INV 17"), Match("unknown")),
    ]
    new, conflicts = rows(results)
    assert new == []
    assert [(r.source, why) for r, why in conflicts] == [
        (6, "name taken by ElectraAcDevice/None")
    ]


def test_the_brand_keeps_pyhvacs_spelling():
    new, _ = rows([(file(7, "MITSUBISHI HEAVY INDUSTRIES", "X9"), Match("unknown"))])
    assert new[0].brand == "Mitsubishi Heavy Industries"


def test_a_file_without_models_gets_its_number():
    new, _ = rows([(file(8, "Acme"), Match("unknown"))])
    assert new[0].model == "SmartIR 8"


def test_rows_are_python():
    text = python_rows([Row("Acme", "A-1", "TableDevice", "1", 1, "unknown")])
    assert text == "    ('Acme', 'A-1', 'unit', TableDevice, '1'),  # SmartIR 1\n"


def test_markdown_lists_every_file():
    results = [(file(1, "Acme", "A-1"), Match("near", "X", gaps={"fan": 3}))]
    text = markdown(results, [], [], [])
    assert "| 1 | Acme | near | X |" in text and "fan (3)" in text


def test_files_that_are_not_json_are_listed():
    assert "- not JSON: 2680" in markdown([], [], [], [], [2680])


def test_a_file_with_many_unreadable_codes_is_flagged():
    f = dataclasses.replace(file(9, "Acme", "A"), skipped=1)
    assert "| 1 (!) |" in markdown([(f, Match("unknown"))], [], [], [])
