import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_old_api_or_c_left():
    offenders = []
    for base in ("pyhvac", "tests", "tools"):
        for path in (ROOT / base).rglob("*.py"):
            if path.name == "test_pure_python.py":
                continue
            text = path.read_text()
            for pattern in (
                r"^\s*(from|import)\s+\S*\b(plugins|legacy|irhvac|hvaclib)\b",
                r"^\s*from\s+\S+\s+import\s+.*\b(irhvac|LegacyDevice)\b",
                r"PluginObject",
            ):
                for line in text.splitlines():
                    code = line.split("#", 1)[0]
                    if re.search(pattern, code):
                        offenders.append(f"{path.relative_to(ROOT)}: {line.strip()}")
    assert offenders == []


def test_nothing_compiled_is_shipped():
    assert not list((ROOT / "pyhvac").rglob("*.so"))
    assert not (ROOT / "setup.py").exists()


def test_the_pypi_upload_keeps_the_trusted_publishers_workflow_file():
    # PyPI's trusted publisher for pyhvac (environment AutoPublish) is bound
    # to .github/workflows/build_wheels.yml: renaming it breaks the upload.
    workflow = ROOT / ".github" / "workflows" / "build_wheels.yml"
    assert workflow.exists()
    text = workflow.read_text()
    assert "AutoPublish" in text and "gh-action-pypi-publish" in text
