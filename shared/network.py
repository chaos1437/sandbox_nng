# shared/network.py
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


class ConnectionRegistry:
    def __init__(self):
        self._connections: list[Connection] = []

    def add(self, conn: Connection):
        self._connections.append(conn)

    def remove(self, conn: Connection):
        self._connections.remove(conn)

    async def broadcast(self, msg: Message):
        alive = []
        for conn in self._connections:
            if conn.is_alive:
                try:
                    await conn.send(msg)
                    alive.append(conn)
                except Exception:
                    conn.close()
            else:
                conn.close()
        self._connections = alive
        return self._connections

    def by_player(self, player_id: str) -> Connection | None:
        for conn in self._connections:
            if conn.player_id == player_id:
                return conn
        return None

    def all(self) -> list[Connection]:
        return list(self._connections)


async def read_message(reader: asyncio.StreamReader, serializer: Serializer) -> Message | None:
    data = await reader.readline()
    if not data:
        return None
    return serializer.decode(data.rstrip(b'\n'))