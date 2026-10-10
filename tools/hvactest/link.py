"""The Broadlink side, through aiobroadlink: the only module that touches
the network."""

import asyncio
import socket
from dataclasses import dataclass

BROADCAST = "255.255.255.255"


@dataclass
class Remote:
    """A Broadlink device that sends and learns IR codes."""

    mac: str
    ip: str
    kind: str  # aiobroadlink's class: rm, rm4, rmp, rm4p
    description: str  # what the device calls itself
    device: object  # the aiobroadlink device


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


class Link:
    """One aiobroadlink UDP endpoint. ``abl`` (the aiobroadlink module) and
    ``endpoint`` (an async callable making the datagram endpoint) are seams
    the tests replace."""

    def __init__(self, abl=None, endpoint=None):
        if abl is None:
            from aiobroadlink import aiobroadlink as abl
        self.abl = abl
        self._endpoint = endpoint
        self.protocol = None
        self.bind_ip = None

    async def start(self, target=BROADCAST):
        self.protocol = self.abl.BroadlinkProtocol()
        self.bind_ip = local_ip(target)
        if self._endpoint is not None:
            await self._endpoint(self.protocol, self.bind_ip)
        else:
            loop = asyncio.get_running_loop()
            await loop.create_datagram_endpoint(
                lambda: self.protocol, local_addr=(self.bind_ip, 0)
            )

    async def discover(self, target=BROADCAST, timeout=5.0):
        """The IR-capable devices answering a Hello (broadcast, or unicast
        to ``target``) within ``timeout`` seconds."""
        scout = self.abl.BroadlinkDevice(0x1234, "Scout")
        scout.controller = self.protocol
        scout.ip = target
        _, port = self.protocol.transport.get_extra_info("sockname")[:2]
        scout.hello(self.bind_ip, port)
        found = {}
        loop = asyncio.get_running_loop()
        end = loop.time() + timeout
        while (left := end - loop.time()) > 0:
            try:
                dev = await asyncio.wait_for(scout.result.get(), timeout=left)
            except asyncio.TimeoutError:
                break
            if not isinstance(dev, self.abl.rm):
                continue  # plugs, sensors: no IR
            self.protocol.register(dev)
            found[dev.mac] = Remote(dev.mac, dev.ip, type(dev).__name__, dev.name, dev)
        return sorted(found.values(), key=lambda r: r.ip)

    async def send(self, remote, packet, timeout=5):
        """Whether ``remote`` acknowledged sending the IR ``packet``."""
        return bool(await remote.device.send_code(bytes(packet), timeout=timeout))

    async def learn(self, remote, timeout=10):
        """The packet ``remote`` learned within ``timeout`` seconds, or None."""
        code = await remote.device.learn_ir_code(timeout=timeout)
        return bytes(code) if code else None

    def close(self):
        if self.protocol is not None and self.protocol.transport is not None:
            self.protocol.transport.close()
