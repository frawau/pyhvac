import asyncio
import json
import random

import pytest

pytest.importorskip("textual")

from textual.widgets import RichLog, Select, Switch  # noqa: E402

from hvactest.app import HvacTestApp, setpoints  # noqa: E402
from hvactest.link import Remote  # noqa: E402
from hvactest.log import SessionLog  # noqa: E402
from pyhvac import registry  # noqa: E402
from pyhvac.ir.formats import broadlink_packet, to_broadlink  # noqa: E402
from pyhvac.state import HvacState, TemperatureRange  # noqa: E402

MAC = "11:22:33:44:55:66"


class FakeLink:
    def __init__(self, learned=None, remotes=True):
        self.protocol = None
        self.sent = []
        self.learned = learned
        self.remotes = remotes

    async def start(self, target):
        self.protocol = object()

    async def discover(self, target, timeout=5.0):
        if not self.remotes:
            return []
        return [Remote(MAC, "192.168.1.20", "rm4", "RM4 mini", None)]

    async def send(self, remote, packet, timeout=5):
        self.sent.append(packet)
        return True

    async def learn(self, remote, timeout=10):
        return self.learned

    def close(self):
        pass


def text(app):
    log = app.query_one("#results", RichLog)
    return "\n".join(line.text for line in log.lines)


def run(case, **kw):
    async def go():
        app = HvacTestApp(**kw)
        async with app.run_test(size=(160, 50)) as pilot:
            await app.workers.wait_for_complete()
            await pilot.pause()
            await case(app, pilot)

    asyncio.run(go())


def test_setpoints_follow_the_range():
    assert setpoints(TemperatureRange(16.0, 18.0, (0, 5))) == [16, 16.5, 17, 17.5, 18]
    assert setpoints(TemperatureRange(17.0, 19.0)) == [17, 18, 19]


def test_discovery_selects_the_broadlink_and_names_it(tmp_path):
    rc = tmp_path / ".pyhvacrc"

    async def case(app, pilot):
        assert app.query_one("#remote", Select).value == MAC
        app.query_one("#name").value = "Living room"
        await pilot.click("#rename")
        await pilot.pause()
        assert json.loads(rc.read_text())["broadlink_names"] == {MAC: "Living room"}
        assert "Living room" in str(app.query_one("#remote", Select)._options)

    run(case, link=FakeLink(), names_path=rc)


def test_a_model_gets_its_own_controls(tmp_path):
    async def case(app, pilot):
        await app.use("Electra", "AXW12DCS")
        await pilot.pause()
        caps = app.device.capabilities
        assert [v for _, v in app.query_one("#mode", Select)._options] == list(
            caps.modes
        )
        assert app.query_one("#feature-light", Switch).value is False
        assert app.state() == app.device.normalise(HvacState(True, caps.modes[0], 24.0))

    run(case, link=FakeLink(), names_path=tmp_path / "rc")


def test_send_sends_pyhvacs_packet_and_logs_it(tmp_path):
    link = FakeLink()
    log_path = tmp_path / "session.jsonl"

    async def case(app, pilot):
        await app.use("Electra", "AXW12DCS")
        app.query_one("#mode", Select).value = "cool"
        await pilot.pause()
        await pilot.click("#send")
        await app.workers.wait_for_complete()
        dev = registry.get_device("Electra", "AXW12DCS")
        st = dev.normalise(HvacState(True, "cool", 24.0))
        assert link.sent == [to_broadlink(dev.encode(None, st).signal)]
        assert app.previous == st
        events = [json.loads(x)["event"] for x in log_path.read_text().splitlines()]
        assert events == ["send"]

    run(case, link=link, log=SessionLog(log_path), names_path=tmp_path / "rc")


def test_learn_shows_the_differing_fields(tmp_path):
    dev = registry.get_device("Electra", "AXW12DCS")
    learned = to_broadlink(dev.encode(None, HvacState(True, "auto", 22.0)).signal)

    async def case(app, pilot):
        await app.use("Electra", "AXW12DCS")
        await pilot.pause()
        await pilot.click("#learn")
        await app.workers.wait_for_complete()
        await pilot.pause()
        shown = text(app)
        assert "differs" in shown and "temperature" in shown

    run(case, link=FakeLink(learned), names_path=tmp_path / "rc")


def test_without_log_nothing_is_written(tmp_path):
    async def case(app, pilot):
        await app.use("Electra", "AXW12DCS")
        await pilot.click("#send")
        await app.workers.wait_for_complete()

    run(case, link=FakeLink(), names_path=tmp_path / "rc")
    assert sorted(p.name for p in tmp_path.iterdir()) == []


def test_no_broadlink_is_reported_and_send_refuses(tmp_path):
    link = FakeLink(remotes=False)

    async def case(app, pilot):
        await app.use("Electra", "AXW12DCS")
        await pilot.click("#send")
        await app.workers.wait_for_complete()
        await pilot.pause()
        shown = text(app)
        assert "no Broadlink found" in shown and "no Broadlink selected" in shown
        assert link.sent == []

    run(case, link=link, names_path=tmp_path / "rc")


def test_a_learn_timeout_is_reported_and_logged(tmp_path):
    log_path = tmp_path / "session.jsonl"

    async def case(app, pilot):
        await app.use("Electra", "AXW12DCS")
        await pilot.click("#learn")
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert "nothing learned" in text(app)
        (record,) = [json.loads(x) for x in log_path.read_text().splitlines()]
        assert record["event"] == "learn" and record["code"] is None

    run(
        case,
        link=FakeLink(learned=None),
        log=SessionLog(log_path),
        names_path=tmp_path / "rc",
    )


def test_a_pasted_non_code_is_refused(tmp_path):
    async def case(app, pilot):
        paste = app.query_one("#paste")
        paste.value = "hello"
        await paste.action_submit()
        await pilot.pause()
        assert app.learned is None
        assert "not" in text(app)

    run(case, link=None, names_path=tmp_path / "rc")


def test_a_malformed_rc_file_is_reported(tmp_path):
    rc = tmp_path / ".pyhvacrc"
    rc.write_text("{oops")

    async def case(app, pilot):
        assert "cannot read" in text(app)
        assert app.names == {}
        assert rc.read_text() == "{oops"

    run(case, link=FakeLink(), names_path=rc)


def test_match_says_when_no_model_decodes(tmp_path):
    async def case(app, pilot):
        rng = random.Random(1)
        pulses = [rng.randrange(300, 3000) for _ in range(60)] + [100000]
        app.learned = broadlink_packet(pulses)
        await pilot.click("#match")
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert "no pyhvac model decodes" in text(app)

    run(case, link=None, names_path=tmp_path / "rc")
