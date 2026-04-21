# shared/network.py
"""TCP connection layer — shared between client and server.

Uses length-prefixed framing: [4 bytes length][N bytes serialized payload]
"""

import asyncio
from shared.protocol import Message
from shared.serializers import Serializer
from shared.framing import encode_message, decode_message


class Connection:
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        serializer: Serializer,
    ):
        self.reader = reader
        self.writer = writer
        self.serializer = serializer
        self.player_id: str | None = None
        self.addr = writer.get_extra_info("peername")

    async def send(self, msg: Message):
        data = encode_message(msg, self.serializer)
        self.writer.write(data)
        await self.writer.drain()

    def close(self):
        self.writer.close()

    async def wait_closed(self):
        await self.writer.wait_closed()

    @property
    def is_alive(self) -> bool:
        return not self.writer.is_closing()

    @staticmethod
    async def connect(host: str, port: int, serializer: Serializer) -> "Connection":
        """Create an outbound TCP connection (for clients)."""
        reader, writer = await asyncio.open_connection(host, port)
        return Connection(reader, writer, serializer)


async def read_message(
    reader: asyncio.StreamReader, serializer: Serializer
) -> Message | None:
    """Read one length-prefixed message from a stream."""
    try:
        header = await reader.readexactly(4)
    except asyncio.IncompleteReadError:
        return None
    length = int.from_bytes(header, "big")
    try:
        data = await reader.readexactly(length)
    except asyncio.IncompleteReadError:
        return None
    return decode_message(header + data, serializer)
