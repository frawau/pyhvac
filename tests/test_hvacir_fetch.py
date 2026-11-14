import io
import zipfile

from hvacir.fetch import ARCHIVE, fetch, files


def archive():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("SmartIR-master/codes/climate/1000.json", "{}")
        z.writestr("SmartIR-master/codes/climate/20.json", "{}")
        z.writestr("SmartIR-master/codes/climate/sub/9.json", "{}")
        z.writestr("SmartIR-master/codes/fan/1000.json", "{}")
        z.writestr("SmartIR-master/README.md", "")
    return buf.getvalue()


def test_only_climate_files_are_kept(tmp_path):
    asked = []
    dest = fetch(tmp_path, get=lambda url: asked.append(url) or archive())
    assert asked == [ARCHIVE]
    assert [p.name for p in files(dest)] == ["20.json", "1000.json"]
