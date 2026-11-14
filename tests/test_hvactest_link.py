import asyncio
import types

from hvactest.link import BROADCAST, Link


class FakeTransport:
    def __init__(self, ip="192.168.1.10"):
        self.closed = False
        self.ip = ip

    def get_extra_info(self, key):
        assert key == "sockname"
        return (self.ip, 41234)

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

    link = Link(abl=fake_abl(answers), endpoint=endpoint, interfaces=lambda: [])
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


# ------------------------------------------------- interfaces
IP_ADDR = [  # what `ip -j -4 addr show up` reports
    {
        "ifname": "lo",
        "operstate": "UNKNOWN",
        "addr_info": [{"local": "127.0.0.1", "prefixlen": 8}],
    },
    {
        "ifname": "br0",
        "operstate": "UP",
        "addr_info": [
            {"local": "192.168.128.1", "prefixlen": 24, "broadcast": "192.168.128.255"}
        ],
    },
    {
        "ifname": "wlp5s0",
        "operstate": "UP",
        "addr_info": [
            {"local": "10.0.5.7", "prefixlen": 22, "broadcast": "10.0.7.255"}
        ],
    },
    {
        "ifname": "docker0",
        "operstate": "UP",
        "addr_info": [
            {"local": "172.17.0.1", "prefixlen": 16, "broadcast": "172.17.255.255"}
        ],
    },
    {
        "ifname": "tun0",
        "operstate": "UNKNOWN",
        "addr_info": [{"local": "192.168.3.2", "prefixlen": 24}],
    },
    {
        "ifname": "eno1",
        "operstate": "DOWN",
        "addr_info": [{"local": "192.168.9.2", "prefixlen": 24}],
    },
]


def sys_tree(root):
    """A /sys/class/net: enp6s0 (physical) under br0, wlp5s0 and eno1
    physical, docker0 over a veth, tun0 and lo virtual."""
    net = root / "class" / "net"
    for name in ("lo", "br0", "enp6s0", "wlp5s0", "docker0", "veth1", "tun0", "eno1"):
        (net / name).mkdir(parents=True)
    for name in ("enp6s0", "wlp5s0", "eno1"):
        (net / name / "device").mkdir()
    (net / "br0" / "lower_enp6s0").symlink_to(net / "enp6s0")
    (net / "docker0" / "lower_veth1").symlink_to(net / "veth1")
    return net


def test_only_active_physical_interfaces_are_used(tmp_path):
    from hvactest.link import physical_ipv4

    found = physical_ipv4(run=lambda: IP_ADDR, net=sys_tree(tmp_path))
    assert [(i.name, i.ip, i.broadcast) for i in found] == [
        ("br0", "192.168.128.1", "192.168.128.255"),  # a bridge over a NIC
        ("wlp5s0", "10.0.5.7", "10.0.7.255"),
    ]


def test_no_ip_command_means_no_interfaces(tmp_path):
    from hvactest.link import physical_ipv4

    def missing():
        raise FileNotFoundError("ip")

    assert physical_ipv4(run=missing, net=sys_tree(tmp_path)) == []


def two_lans_abl(devices):
    """aiobroadlink fake: a Hello sent to a subnet broadcast (or a device's
    own address) from an endpoint is answered by that subnet's devices."""

    class Scout:
        def __init__(self, devtype, name):
            self.result = asyncio.Queue()
            self.ip = None
            self.controller = None

        def hello(self, ip, port):
            for dev in devices:
                same_lan = dev.ip.rsplit(".", 1)[0] == ip.rsplit(".", 1)[0]
                if same_lan and self.ip in (dev.ip, ip.rsplit(".", 1)[0] + ".255"):
                    self.result.put_nowait(dev)

    return types.SimpleNamespace(
        BroadlinkProtocol=FakeProtocol, BroadlinkDevice=Scout, rm=FakeRm
    )


def lans():
    from hvactest.link import Interface

    return [
        Interface("br0", "192.168.1.10", "192.168.1.255", 24),
        Interface("wlp5s0", "192.168.2.10", "192.168.2.255", 24),
    ]


async def two_lan_link(devices):
    async def endpoint(protocol, ip):
        protocol.transport = FakeTransport(ip)

    link = Link(abl=two_lans_abl(devices), endpoint=endpoint, interfaces=lans)
    await link.start()
    return link


def test_discovery_covers_every_interface():
    asyncio.run(_test_discovery_covers_every_interface())


async def _test_discovery_covers_every_interface():
    wired = FakeRm("11:11:11:11:11:11", "192.168.1.20")
    wifi = FakeRm("22:22:22:22:22:22", "192.168.2.30")
    link = await two_lan_link([wired, wifi])
    found = await link.discover(timeout=0.2)
    assert [(r.mac, r.interface) for r in found] == [
        ("11:11:11:11:11:11", "br0"),
        ("22:22:22:22:22:22", "wlp5s0"),
    ]
    by_ip = {p.transport.ip: p for p in link.protocols}
    assert by_ip["192.168.1.10"].registered == [wired]
    assert by_ip["192.168.2.10"].registered == [wifi]


def test_an_address_is_reached_through_its_interface():
    asyncio.run(_test_an_address_is_reached_through_its_interface())


async def _test_an_address_is_reached_through_its_interface():
    wifi = FakeRm("22:22:22:22:22:22", "192.168.2.30")
    link = await two_lan_link([wifi])
    (remote,) = await link.discover(target="192.168.2.30", timeout=0.2)
    assert remote.interface == "wlp5s0"
