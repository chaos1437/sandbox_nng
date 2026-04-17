# client/network.py
import asyncio
from shared.protocol import encode, decode, Message
from shared.logging import setup_logger

log = setup_logger("network", "client.log")

class NetworkClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.player_id: str = ""
        self.incoming: asyncio.Queue[Message] = asyncio.Queue()
        self._running = False

    async def connect(self) -> bool:
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            self._running = True
            return True
        except Exception as e:
            log.error(f"Connection failed: {e}")
            return False

    async def send(self, msg: Message):
        if self.writer:
            self.writer.write(encode(msg) + b'\n')
            await self.writer.drain()

    async def receive_loop(self):
        while self._running:
            try:
                data = await self.reader.readline()
                if not data:
                    break
                msg = decode(data.rstrip(b'\n'))
                await self.incoming.put(msg)
            except Exception as e:
                log.error(f"Receive error: {e}")
                break

    async def disconnect(self):
        self._running = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
