# client/network.py
"""Client network layer — wraps shared Connection."""
import asyncio
from shared.protocol import Message
from shared.serializers import Serializer
from shared.network import Connection, read_message
from shared.logging import setup_logger

log = setup_logger("network", "client.log", console=False)


class NetworkClient:
    def __init__(self, host: str, port: int, serializer: Serializer | None = None):
        self.host = host
        self.port = port
        self.serializer = serializer
        self._conn: Connection | None = None
        self.incoming: asyncio.Queue[Message] = asyncio.Queue()
        self._running = False

    async def connect(self) -> bool:
        if self.serializer is None:
            from shared.serializers import JsonSerializer
            self.serializer = JsonSerializer()
        try:
            self._conn = await Connection.connect(self.host, self.port, self.serializer)
            self._running = True
            return True
        except Exception as e:
            log.error(f"Connection failed: {e}")
            return False

    async def send(self, msg: Message):
        if self._conn:
            await self._conn.send(msg)

    async def receive_loop(self):
        while self._running and self._conn:
            msg = await read_message(self._conn.reader, self._conn.serializer)
            if msg is None:
                break
            await self.incoming.put(msg)

    async def disconnect(self):
        self._running = False
        if self._conn:
            self._conn.close()
            await self._conn.wait_closed()
            self._conn = None
