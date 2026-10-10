"""Link against the real aiobroadlink classes (the fakes cannot show how
its protocol keeps waiters and devices)."""

import asyncio

import pytest

abl = pytest.importorskip("aiobroadlink.aiobroadlink")

from hvactest.link import Link  # noqa: E402

RM_MAC = bytes([6, 5, 4, 3, 2, 1])


def hello_reply(mac=RM_MAC, ip=bytes([20, 1, 168, 192]), devtype=0x27C2):
    data = bytearray(80)
    data[38:40] = (0x07).to_bytes(2, "little")
    data[52:54] = devtype.to_bytes(2, "little")
    data[54:58] = ip
    data[58:64] = mac
    data[64:68] = b"RM3\x00"
    checksum = 0xBEAF
    for byte in data:
        checksum = (checksum + byte) & 0xFFFF
    data[32:34] = checksum.to_bytes(2, "little")
    return bytes(data)


class AnsweringTransport:
    """Answers every Hello with one RM."""

    def __init__(self, protocol):
        self.protocol = protocol

    def get_extra_info(self, key):
        return ("192.168.1.10", 4000)

    def sendto(self, packet, addr):
        if packet[38] == 0x06:  # Hello
            asyncio.get_running_loop().call_later(
                0.02,
                self.protocol.datagram_received,
                hello_reply(),
                ("192.168.1.20", 80),
            )

    def close(self):
        pass


def test_discovery_finds_the_device_again_attached_to_the_protocol():
    async def go():
        async def endpoint(protocol, ip):
            protocol.transport = AnsweringTransport(protocol)

        link = Link(abl=abl, endpoint=endpoint)
        await link.start()
        for _ in range(2):
            (remote,) = await link.discover(timeout=0.3)
            assert remote.device.controller is link.protocol
            assert link.protocol.devices[remote.mac] is remote.device

    asyncio.run(go())


def test_a_socket_error_while_sending_does_not_raise():
    # A UDP send that fails (no route) makes asyncio call the protocol's
    # error_received, which aiobroadlink's protocol lacks.
    async def go():
        link = Link(abl=abl)
        await link.start("127.0.0.1")
        assert await link.discover(target="8.8.8.8", timeout=0.2) == []
        link.close()

    asyncio.run(go())


def test_a_failed_start_leaves_no_half_started_link():
    async def go():
        async def endpoint(protocol, ip):
            raise OSError("cannot bind")

        link = Link(abl=abl, endpoint=endpoint)
        with pytest.raises(OSError):
            await link.start()
        assert link.protocol is None

    asyncio.run(go())
