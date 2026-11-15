from pathlib import Path

import verified
from pyhvac import brands

FILE = Path(__file__).resolve().parents[1] / "VERIFIED.md"


def test_every_model_has_one_row():
    marks = verified.parse(FILE.read_text())
    assert sorted(marks) == sorted((b, m) for b, m, *_ in brands.MODELS)


def test_the_file_is_what_the_tool_writes():
    """Run ``python tools/verified.py`` after adding a model."""
    text = FILE.read_text()
    assert verified.render(brands.MODELS, verified.parse(text)) == text


def test_marks_and_notes_survive_a_sync():
    rows = [
        ("Tokio", "RG51|50/BGE", "remote", object, None),
        ("Daikin", "Smash II", "unit", object, "x"),
    ]
    marks = {("Daikin", "Smash II"): verified.Mark(True, "on a | b, pyhvac 0.2.0")}
    text = verified.render(rows, marks)
    assert verified.parse(text) == {
        ("Tokio", "RG51|50/BGE"): verified.Mark(False, ""),
        ("Daikin", "Smash II"): verified.Mark(True, "on a | b, pyhvac 0.2.0"),
    }


def test_a_tick_is_the_only_mark():
    text = verified.render(
        [("A", "B", "unit", object, None)], {("A", "B"): verified.Mark(True, "")}
    )
    bad = text.replace(verified.TICK, "yes")
    try:
        verified.parse(bad)
    except ValueError as err:
        assert "A B" in str(err)
    else:
        raise AssertionError("a mark other than the tick was accepted")
