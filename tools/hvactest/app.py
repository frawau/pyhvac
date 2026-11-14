"""hvactest: send pyhvac codes through a Broadlink RM, learn the real
remote's codes and compare them.

    python tools/hvactest/app.py [--ip ADDR] [--log FILE]

--ip is the Broadlink's address (else devices are discovered by broadcast
on every active physical interface: Ethernet, Wi-Fi, bridges over them);
--log appends a JSON line per action to FILE (off by default).
"""

import argparse
import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from rich.table import Table  # noqa: E402
from textual import on, work  # noqa: E402
from textual.app import App, ComposeResult  # noqa: E402
from textual.containers import Horizontal, Vertical, VerticalScroll  # noqa: E402
from textual.widgets import (  # noqa: E402
    Button,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Select,
    Switch,
)

from hvacir import match as M  # noqa: E402
from hvactest import names  # noqa: E402
from hvactest.compare import (  # noqa: E402
    compare,
    match_code,
    packet_from_base64,
)
from hvactest.link import BROADCAST, Link  # noqa: E402
from hvactest.log import SessionLog  # noqa: E402
from pyhvac import registry  # noqa: E402
from pyhvac.ir.formats import to_broadlink  # noqa: E402
from pyhvac.state import HvacState  # noqa: E402

VERDICTS = ("worked", "ignored", "wrong setting")


def setpoints(rng):
    """The °C setpoints a TemperatureRange offers, lowest first."""
    out = []
    for tenth in range(round(rng.min * 10), round(rng.max * 10) + 1):
        if tenth % 10 in rng.decimals:
            out.append(tenth / 10)
    return out


def b64(packet):
    return base64.b64encode(bytes(packet)).decode()


class HvacTestApp(App):
    """See the module docstring."""

    TITLE = "pyhvac test"
    CSS = """
    #left { width: 34; }
    #centre { width: 34; }
    #results { width: 1fr; border: round $accent; }
    #controls Label { margin-top: 1; }
    #bottom { height: auto; }
    #bottom Button { margin-right: 1; }
    #paste, #note { width: 1fr; }
    """
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(
        self, link=None, log=None, names_path=names.DEFAULT_PATH, target=BROADCAST
    ):
        super().__init__()
        self.link = link
        self.log_ = log or SessionLog(None)
        self.names_path = names_path
        self.target = target
        self.remotes = {}  # mac -> Remote
        self.device = None  # the pyhvac Device
        self.model = None  # (brand, model)
        self.previous = None  # the last state sent to this model
        self.learned = None  # the last learned or pasted packet
        self.candidates = None  # hvacir candidates, built for Match
        self.busy = None  # the Broadlink action running, if any

    # ------------------------------------------------------------- layout
    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="left"):
                yield Label("Broadlink")
                yield Select([], id="remote", prompt="(none)")
                yield Button("Discover", id="discover")
                yield Input(placeholder="name for this Broadlink", id="name")
                yield Button("Rename", id="rename")
                yield Label("Brand")
                yield Select(
                    [(b, b) for b in registry.brands()], id="brand", prompt="brand"
                )
                yield Label("Model")
                yield Select([], id="model", prompt="model")
            yield VerticalScroll(id="controls")
            yield RichLog(id="results", markup=True, wrap=True)
        with Horizontal(id="bottom"):
            yield Button("Send", id="send", variant="primary")
            yield Button("Learn", id="learn")
            yield Button("Compare", id="compare")
            yield Button("Match", id="match")
            yield Input(placeholder="paste a base64 Broadlink code", id="paste")
            yield Select([(v, v) for v in VERDICTS], id="verdict", prompt="verdict")
            yield Input(placeholder="note", id="note")
            yield Button("Log", id="log")
        yield Footer()

    def say(self, text):
        self.query_one("#results", RichLog).write(text)

    async def on_mount(self):
        found, error = names.load(self.names_path)
        if error:
            self.say(f"[red]{error}[/] (names not loaded)")
        self.names = found
        if self.log_.enabled:
            try:
                self.log_.path.open("a").close()
                self.say(f"logging to {self.log_.path}")
            except OSError as exc:
                self.say(
                    f"[red]cannot write the log {self.log_.path}: {exc}[/] (logging off)"
                )
                self.log_ = SessionLog(None)
        if self.link is None:
            self.say("offline: paste codes to compare and match")
        elif self.begin("discovering"):
            self.discover()

    def record(self, event, **data):
        """Log ``event`` if logging is on; a write error turns logging off."""
        try:
            return self.log_.write(event, **data)
        except OSError as exc:
            self.say(f"[red]cannot write the log: {exc}[/] (logging off)")
            self.log_ = SessionLog(None)
            return None

    def begin(self, what):
        """Start the Broadlink action ``what`` unless another one runs: the
        device answers through one queue, so actions must not overlap."""
        if self.busy is not None:
            self.say(f"[yellow]busy: {self.busy}…[/]")
            return False
        self.busy = what
        return True

    def failed(self, what, exc):
        self.say(f"[red]{what} failed: {exc}[/]")
        self.record("error", action=what, error=str(exc))

    # ------------------------------------------------------------ Broadlink
    def label(self, remote):
        name = self.names.get(remote.mac.lower())
        via = f" via {remote.interface}" if remote.interface else ""
        detail = f"{remote.kind} {remote.ip} {remote.mac}{via}"
        return f"{name} ({remote.ip}{via})" if name else detail

    def refresh_remotes(self):
        select = self.query_one("#remote", Select)
        current = select.value
        select.set_options([(self.label(r), mac) for mac, r in self.remotes.items()])
        if current in self.remotes:
            select.value = current
        elif len(self.remotes) == 1:
            select.value = next(iter(self.remotes))

    @work(group="link")
    async def discover(self):
        try:
            if not self.link.started:
                await self.link.start(self.target)
            found = await self.link.discover(self.target)
        except Exception as exc:  # the network: report, never crash
            self.failed("discovery", exc)
            return
        finally:
            self.busy = None
        self.remotes.update({r.mac: r for r in found})
        self.refresh_remotes()
        self.say(
            f"found {len(found)} Broadlink IR device(s)"
            if found
            else "[yellow]no Broadlink found[/] (try --ip, or work offline)"
        )

    def remote(self):
        mac = self.query_one("#remote", Select).value
        return self.remotes.get(mac) if mac is not Select.NULL else None

    @on(Button.Pressed, "#discover")
    def on_discover(self):
        if self.link is None:
            self.say("offline: no Broadlink link")
        elif self.begin("discovering"):
            self.discover()

    @on(Button.Pressed, "#rename")
    def on_rename(self):
        remote = self.remote()
        if remote is None:
            self.say("[yellow]choose a Broadlink first[/]")
            return
        name = self.query_one("#name", Input).value
        try:
            self.names = names.rename(remote.mac, name, self.names_path)
        except OSError as exc:
            self.say(f"[red]cannot save the name: {exc}[/]")
            return
        self.refresh_remotes()
        self.say(f"{remote.mac} is now {name.strip() or '(unnamed)'}")

    # ------------------------------------------------------- brand / model
    @on(Select.Changed, "#brand")
    async def on_brand(self, event):
        await self.drop_model()
        model = self.query_one("#model", Select)
        if event.value is Select.NULL:
            model.set_options([])
            return
        model.set_options([(m, m) for m in registry.models(event.value)])

    @on(Select.Changed, "#model")
    async def on_model(self, event):
        brand = self.query_one("#brand", Select).value
        if event.value is Select.NULL or brand is Select.NULL:
            await self.drop_model()
            return
        await self.use(brand, event.value)

    async def drop_model(self):
        """No model chosen: no device, no controls."""
        self.device = self.model = self.previous = None
        await self.query_one("#controls", VerticalScroll).remove_children()

    async def use(self, brand, model):
        """Select ``brand``/``model`` and build its controls."""
        self.device = registry.get_device(brand, model)
        self.model = (brand, model)
        self.previous = None
        caps = self.device.capabilities
        widgets = [Label("Power"), Switch(value=True, id="power")]
        widgets += [
            Label("Mode"),
            Select([(m, m) for m in caps.modes], id="mode", allow_blank=False),
        ]
        temps = setpoints(caps.temperature)
        default = caps.temperature.snap(24.0)
        widgets += [
            Label("Setpoint °C"),
            Select(
                [(f"{t:g}", t) for t in temps],
                id="setpoint",
                allow_blank=False,
                value=default,
            ),
        ]
        for attr, title in (
            ("fan", "Fan"),
            ("swing_v", "Swing V"),
            ("swing_h", "Swing H"),
        ):
            choice = getattr(caps, attr)
            if choice is not None:
                options = [(choice.label(v), v) for v in choice.values]
                widgets += [Label(title), Select(options, id=attr, allow_blank=False)]
        for name, choice in caps.features.items():
            if set(choice.values) == {False, True}:
                widgets += [Label(name), Switch(value=False, id=f"feature-{name}")]
            else:
                options = [(str(v), v) for v in choice.values]
                widgets += [
                    Label(name),
                    Select(options, id=f"feature-{name}", allow_blank=False),
                ]
        controls = self.query_one("#controls", VerticalScroll)
        await controls.remove_children()
        await controls.mount(*widgets)
        self.say(f"model {brand} / {model} ({type(self.device).__name__})")

    def state(self):
        """The HvacState the controls describe."""
        q = self.query_one
        caps = self.device.capabilities
        kw = {}
        for attr in ("fan", "swing_v", "swing_h"):
            if getattr(caps, attr) is not None:
                kw[attr] = q(f"#{attr}", Select).value
        features = {}
        for name in caps.features:
            features[name] = q(f"#feature-{name}").value
        return HvacState(
            q("#power", Switch).value,
            q("#mode", Select).value,
            q("#setpoint", Select).value,
            features=features,
            **kw,
        )

    def describe(self, state):
        text = (
            f"{'on' if state.power else 'off'} {state.mode} {state.temperature:g}°C "
            f"fan {state.fan} swing {state.swing_v}/{state.swing_h}"
        )
        for name, value in state.features.items():
            if value is True:
                text += f" +{name}"
            elif value is not False:  # a choice: say which
                text += f" {name}={value}"
        return text

    # ------------------------------------------------------------- actions
    def ready(self, need_remote=True):
        if self.device is None:
            self.say("[yellow]choose a brand and model first[/]")
            return False
        if need_remote and (self.link is None or self.remote() is None):
            self.say("[yellow]no Broadlink selected[/]")
            return False
        return True

    @on(Button.Pressed, "#send")
    def on_send(self):
        if self.ready() and self.begin("sending"):
            self.send()

    @work(group="link")
    async def send(self):
        try:
            await self._send()
        except Exception as exc:  # the network: report, never crash
            self.failed("send", exc)
        finally:
            self.busy = None

    async def _send(self):
        state = self.state()
        try:
            command = self.device.encode(self.previous, state)
        except (ValueError, KeyError) as exc:
            self.say(f"[red]cannot encode: {exc}[/]")
            return
        packet = to_broadlink(command.signal)
        remote = self.remote()
        ok = await self.link.send(remote, packet)
        if ok:
            self.previous = command.state
        self.say(
            f"sent {self.describe(command.state)}: "
            + (
                "[green]acknowledged[/]"
                if ok
                else f"[red]no answer from {self.label(remote)}[/]"
            )
        )
        self.record(
            "send",
            model=list(self.model),
            state=self.describe(command.state),
            code=b64(packet),
            acknowledged=ok,
        )

    @on(Button.Pressed, "#learn")
    def on_learn(self):
        if self.ready(need_remote=True) and self.begin("learning"):
            self.learn()

    @work(group="link")
    async def learn(self):
        try:
            await self._learn()
        except Exception as exc:  # the network, a bad packet: report
            self.failed("learn", exc)
        finally:
            self.busy = None

    async def _learn(self):
        self.say("press the button on the real remote (10 s)…")
        packet = await self.link.learn(self.remote())
        if packet is None:
            self.say("[yellow]nothing learned within 10 s[/]")
            self.record("learn", model=list(self.model), code=None)
            return
        self.learned = packet
        self.record("learn", model=list(self.model), code=b64(packet))
        self.show_compare()

    @on(Input.Submitted, "#paste")
    def on_paste(self, event):
        try:
            self.learned = packet_from_base64(event.value)
        except ValueError as exc:
            self.say(f"[red]{exc}[/]")
            return
        self.record("paste", code=b64(self.learned))
        if self.device is not None:
            self.show_compare()
        else:
            self.say("code read; choose a model to compare, or Match")

    @on(Button.Pressed, "#compare")
    def on_compare(self):
        if self.learned is None:
            self.say("[yellow]learn or paste a code first[/]")
        elif self.ready(need_remote=False):
            self.show_compare()

    def show_compare(self):
        state = self.state()
        result = compare(self.device, state, self.learned, self.previous)
        self.say(f"compare with {self.describe(state)}: [b]{result.verdict}[/]")
        if result.verdict == "differs":
            table = Table("field", "learned", "pyhvac")
            for name, (got, want) in result.fields.items():
                table.add_row(name, str(got), str(want))
            self.say(table)
        elif result.verdict == "not this protocol":
            self.say("try Match to find the model that sends it")
        self.record(
            "compare",
            model=list(self.model),
            state=self.describe(state),
            verdict=result.verdict,
            fields={k: list(map(str, v)) for k, v in result.fields.items()},
        )

    @on(Button.Pressed, "#match")
    def on_match(self):
        if self.learned is None:
            self.say("[yellow]learn or paste a code first[/]")
        else:
            self.match()

    @work(exclusive=True, group="match", thread=True)
    def match(self):
        if self.candidates is None:
            self.call_from_thread(self.say, "loading every pyhvac model…")
            self.candidates = M.candidates()
        rows = match_code(self.learned, self.candidates)
        self.call_from_thread(self.show_match, rows)

    def show_match(self, rows):
        if not rows:
            self.say("[yellow]no pyhvac model decodes this code[/]")
        else:
            table = Table("model", "state that sends it")
            for row in rows[:15]:
                table.add_row(row.name, row.state or "(decodes; no state matches)")
            self.say(table)
        self.record("match", rows=[[r.name, r.state] for r in rows])

    @on(Button.Pressed, "#log")
    def on_log(self):
        verdict = self.query_one("#verdict", Select).value
        if verdict is Select.NULL:
            self.say("[yellow]choose a verdict[/]")
            return
        note = self.query_one("#note", Input).value
        record = self.record(
            "verdict",
            model=list(self.model) if self.model else None,
            state=self.describe(self.previous) if self.previous else None,
            verdict=verdict,
            note=note,
        )
        self.say(f"verdict: {verdict}" + ("" if record else " (logging is off)"))

    def on_unmount(self):
        if self.link is not None:
            self.link.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ip", default=BROADCAST, help="the Broadlink's address")
    ap.add_argument("--log", default=None, help="append a JSON line per action here")
    ap.add_argument("--offline", action="store_true", help="no Broadlink")
    args = ap.parse_args(argv)
    link = None if args.offline else Link()
    HvacTestApp(link=link, log=SessionLog(args.log), target=args.ip).run()


if __name__ == "__main__":
    main()
