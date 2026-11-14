"""The Broadlink side, through aiobroadlink: the only module that touches
the network.

Discovery runs on every active physical interface (Ethernet, Wi-Fi, and
bridges, bonds or VLANs over them; not loopback, VPN tunnels or container
bridges), each with its own endpoint, so a Broadlink on any attached
network is found and then reached through the interface that found it.
"""

import asyncio
import ipaddress
import json
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

BROADCAST = "255.255.255.255"
SCOUT_MAC = "00:00:00:00:00:00"  # aiobroadlink's discovery scouts
SYS_NET = Path("/sys/class/net")


@dataclass
class Remote:
    """A Broadlink device that sends and learns IR codes."""

    mac: str
    ip: str
    kind: str  # aiobroadlink's class: rm, rm4, rmp, rm4p
    description: str  # what the device calls itself
    device: object  # the aiobroadlink device
    interface: Optional[str] = None  # the interface that found it


@dataclass(frozen=True)
class Interface:
    name: str
    ip: str
    broadcast: str
    prefixlen: int

    @property
    def network(self):
        return ipaddress.ip_network(f"{self.ip}/{self.prefixlen}", strict=False)


def _ip_addr():
    """iproute2's view of the IPv4 addresses of the interfaces that are up."""
    out = subprocess.run(
        ["ip", "-j", "-4", "addr", "show", "up"],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    )
    return json.loads(out.stdout)


def _physical(name, net, seen=()):
    """Whether interface ``name`` is a device (Ethernet, Wi-Fi, USB...) or
    sits on one (a bridge, bond or VLAN whose lower devices include one)."""
    path = Path(net) / name
    if (path / "device").exists():
        return True
    return any(
        lower.name[len("lower_") :] not in seen
        and _physical(lower.name[len("lower_") :], net, seen + (name,))
        for lower in path.glob("lower_*")
    )


def physical_ipv4(run=_ip_addr, net=SYS_NET):
    """The IPv4 addresses of the active physical interfaces (empty where
    iproute2 is not available: the caller falls back to one interface)."""
    try:
        links = run()
    except (OSError, ValueError, subprocess.SubprocessError):
        return []
    out = []
    for link in links:
        name = link.get("ifname", "")
        if link.get("operstate") == "DOWN" or not _physical(name, net):
            continue
        for addr in link.get("addr_info", ()):
            ip = addr.get("local")
            if not ip or ip.startswith("127."):
                continue
            prefix = int(addr.get("prefixlen", 32))
            broadcast = addr.get("broadcast") or str(
                ipaddress.ip_network(f"{ip}/{prefix}", strict=False).broadcast_address
            )
            out.append(Interface(name, ip, broadcast, prefix))
    return out


def local_ip(target=BROADCAST):
    """The local address that routes to ``target`` (an arbitrary private
    address for a broadcast)."""
    probe = "10.255.255.255" if target == BROADCAST else target
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.connect((probe, 80))
            return sock.getsockname()[0]
        except OSError:
            return "0.0.0.0"


@dataclass
class _Endpoint:
    interface: Optional[Interface]  # None: the single fallback endpoint
    ip: str
    protocol: object


class Link:
    """One aiobroadlink endpoint per active physical interface (one bound
    to the default route's address where interfaces cannot be listed).
    ``abl`` (the aiobroadlink module), ``endpoint`` (an async callable
    making a datagram endpoint) and ``interfaces`` are seams the tests
    replace."""

    def __init__(self, abl=None, endpoint=None, interfaces=physical_ipv4):
        if abl is None:
            from aiobroadlink import aiobroadlink as abl
        self.abl = abl
        self._endpoint = endpoint
        self._interfaces = interfaces
        self.endpoints = []
        self.last_error = None  # the last UDP send error

    @property
    def started(self):
        return bool(self.endpoints)

    @property
    def protocols(self):
        return [e.protocol for e in self.endpoints]

    @property
    def protocol(self):
        """The first endpoint's protocol (None before start)."""
        return self.endpoints[0].protocol if self.endpoints else None

    async def _open(self, ip):
        protocol = self.abl.BroadlinkProtocol()
        # asyncio reports a failed UDP send (no route...) by calling the
        # protocol's error_received, which aiobroadlink's lacks.
        protocol.error_received = self._error_received
        if self._endpoint is not None:
            await self._endpoint(protocol, ip)
        else:
            loop = asyncio.get_running_loop()
            await loop.create_datagram_endpoint(lambda: protocol, local_addr=(ip, 0))
        return protocol

    async def start(self, target=BROADCAST):
        """Open the endpoints; on failure the link stays unstarted."""
        interfaces = self._interfaces() or [None]
        opened = []
        try:
            for interface in interfaces:
                ip = interface.ip if interface else local_ip(target)
                opened.append(_Endpoint(interface, ip, await self._open(ip)))
        except BaseException:
            for endpoint in opened:
                endpoint.protocol.transport.close()
            raise
        self.endpoints = opened

    def _error_received(self, exc):
        self.last_error = exc

    def _for(self, target):
        """The endpoints to send ``target`` a Hello from, and to what."""
        if target == BROADCAST:
            return [
                (e, e.interface.broadcast if e.interface else BROADCAST)
                for e in self.endpoints
            ]
        address = ipaddress.ip_address(target)
        on_lan = [
            e for e in self.endpoints if e.interface and address in e.interface.network
        ]
        return [(e, target) for e in (on_lan or self.endpoints)]

    async def _discover_on(self, endpoint, hello_to, timeout):
        protocol = endpoint.protocol
        # aiobroadlink keeps a scout's Hello waiter (only its own discovery
        # loop cleans it up): an old scout would take the new replies.
        for waiting in [d for d in protocol.waiting if d.mac == SCOUT_MAC]:
            del protocol.waiting[waiting]
        scout = self.abl.BroadlinkDevice(0x1234, "Scout")
        scout.controller = protocol
        scout.ip = hello_to
        _, port = protocol.transport.get_extra_info("sockname")[:2]
        scout.hello(endpoint.ip, port)
        found = []
        loop = asyncio.get_running_loop()
        end = loop.time() + timeout
        while (left := end - loop.time()) > 0:
            try:
                dev = await asyncio.wait_for(scout.result.get(), timeout=left)
            except asyncio.TimeoutError:
                break
            if not isinstance(dev, self.abl.rm):
                continue  # plugs, sensors: no IR
            protocol.register(dev)
            dev = protocol.devices.get(dev.mac, dev)  # the attached one
            name = endpoint.interface.name if endpoint.interface else None
            found.append(
                Remote(dev.mac, dev.ip, type(dev).__name__, dev.name, dev, name)
            )
        return found

    async def discover(self, target=BROADCAST, timeout=5.0):
        """The IR-capable devices answering a Hello within ``timeout``
        seconds: a broadcast on every interface, or unicast to ``target``
        from the interface whose network holds it."""
        results = await asyncio.gather(
            *(self._discover_on(e, to, timeout) for e, to in self._for(target))
        )
        found = {}
        for remote in (r for batch in results for r in batch):
            found.setdefault(remote.mac, remote)  # the first interface wins
        return sorted(found.values(), key=lambda r: r.ip)

    @staticmethod
    def _drain(device):
        """Drop answers that came after their waiter gave up: aiobroadlink
        hands every answer to the next reader of one queue."""
        queue = getattr(device, "result", None)
        while queue is not None and not queue.empty():
            queue.get_nowait()

    async def send(self, remote, packet, timeout=5):
        """Whether ``remote`` acknowledged sending the IR ``packet``."""
        self._drain(remote.device)
        return bool(await remote.device.send_code(bytes(packet), timeout=timeout))

    async def learn(self, remote, timeout=10):
        """The packet ``remote`` learned within ``timeout`` seconds, or None."""
        self._drain(remote.device)
        code = await remote.device.learn_ir_code(timeout=timeout)
        return bytes(code) if isinstance(code, (bytes, bytearray)) and code else None

    def close(self):
        for endpoint in self.endpoints:
            if endpoint.protocol.transport is not None:
                endpoint.protocol.transport.close()
