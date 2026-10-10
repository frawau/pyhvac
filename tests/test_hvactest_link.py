import asyncio
import types

from hvactest.link import BROADCAST, Link


class FakeTransport:
    def __init__(self):
        self.closed = False

    def get_extra_info(self, key):
        assert key == "sockname"
        return ("192.168.1.10", 41234)

    def close(self):
        self.closed = True


class FakeProtocol:
    def __init__(self):
        self.transport = None
        self.registered = []
        self.waiting = {}  # as aiobroadlink's: device -> pending answer
        self.devices = {}  # mac -> device

    def register(self, dev):
        self.registered.append(dev)
        self.devices.setdefault(dev.mac, dev)


class FakeRm:
    def __init__(self, mac, ip, name="RM4 mini"):
        self.mac, self.ip, self.name = mac, ip, name
        self.sent = []
        self.learned = b"\x26\x00\x02\x00\x10\x20"
        self.result = asyncio.Queue()

    async def send_code(self, code, timeout=5):
        self.sent.append(code)
        return True

    async def learn_ir_code(self, timeout=10):
        return self.learned


class FakeSp2:  # a plug: no IR
    mac, ip, name = "aa:aa:aa:aa:aa:aa", "192.168.1.30", "SP2"


def fake_abl(answers):
    class Scout:
        def __init__(self, devtype, name):
            self.result = asyncio.Queue()
            self.ip = None
            self.controller = None

        def hello(self, ip, port):
            self.hello_args = (self.ip, ip, port)
            for dev in answers:
                if self.ip in (BROADCAST, dev.ip):
                    self.result.put_nowait(dev)

    return types.SimpleNamespace(
        BroadlinkProtocol=FakeProtocol, BroadlinkDevice=Scout, rm=FakeRm
    )


async def started(answers):
    async def endpoint(protocol, ip):
        protocol.transport = FakeTransport()

    link = Link(abl=fake_abl(answers), endpoint=endpoint)
    await link.start()
    return link


def test_discovery_keeps_the_ir_devices():
    asyncio.run(_test_discovery_keeps_the_ir_devices())


async def _test_discovery_keeps_the_ir_devices():
    rm = FakeRm("11:22:33:44:55:66", "192.168.1.20")
    link = await started([rm, FakeSp2()])
    found = await link.discover(timeout=0.2)
    assert [(r.mac, r.ip, r.kind) for r in found] == [
        ("11:22:33:44:55:66", "192.168.1.20", "FakeRm")
    ]
    assert link.protocol.registered == [rm]


def test_discovery_can_target_one_address():
    asyncio.run(_test_discovery_can_target_one_address())


async def _test_discovery_can_target_one_address():
    a = FakeRm("11:22:33:44:55:66", "192.168.1.20")
    b = FakeRm("11:22:33:44:55:77", "192.168.1.21")
    link = await started([a, b])
    found = await link.discover(target="192.168.1.21", timeout=0.2)
    assert [r.ip for r in found] == ["192.168.1.21"]


def test_send_and_learn_go_to_the_device():
    asyncio.run(_test_send_and_learn_go_to_the_device())


async def _test_send_and_learn_go_to_the_device():
    rm = FakeRm("11:22:33:44:55:66", "192.168.1.20")
    link = await started([rm])
    (remote,) = await link.discover(timeout=0.2)
    assert await link.send(remote, b"\x26\x00") is True
    assert rm.sent == [b"\x26\x00"]
    assert await link.learn(remote) == rm.learned
    rm.learned = None
    assert await link.learn(remote) is None
    link.close()
    assert link.protocol.transport.closed


def test_stale_answers_are_dropped_and_only_packets_are_learned():
    asyncio.run(_test_stale_answers_are_dropped_and_only_packets_are_learned())


async def _test_stale_answers_are_dropped_and_only_packets_are_learned():
    # aiobroadlink answers through one queue: an answer that came after its
    # waiter gave up must not be read as the next operation's.
    rm = FakeRm("11:22:33:44:55:66", "192.168.1.20")
    link = await started([rm])
    (remote,) = await link.discover(timeout=0.2)
    rm.result.put_nowait(True)
    await link.send(remote, b"\x26\x00")
    assert rm.result.empty()
    rm.result.put_nowait(True)
    await link.learn(remote)
    assert rm.result.empty()
    rm.learned = True  # an acknowledgement, not a packet
    assert await link.learn(remote) is None
