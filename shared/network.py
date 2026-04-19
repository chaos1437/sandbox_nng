# shared/network.py
"""TCP connection layer — shared between client and server."""
import asyncio
from shared.serializers import Serializer
from shared.protocol import Message


class Connection:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, serializer: Serializer):
        self.reader = reader
        self.writer = writer
        self.serializer = serializer
        self.player_id: str | None = None
        self.addr = writer.get_extra_info('peername')

    async def send(self, msg: Message):
        data = self.serializer.encode(msg) + b'\n'
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
    async def connect(host: str, port: int, serializer: Serializer) -> 'Connection':
        """Create an outbound TCP connection (for clients)."""
        reader, writer = await asyncio.open_connection(host, port)
        return Connection(reader, writer, serializer)


async def read_message(reader: asyncio.StreamReader, serializer: Serializer) -> Message | None:
    """Read one newline-delimited message from a stream."""
    data = await reader.readline()
    if not data:
        return None
    return serializer.decode(data.rstrip(b'\n'))
