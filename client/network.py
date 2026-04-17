# client/network.py
import asyncio
from shared.protocol import encode, decode, Message

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
            print(f"[network] Connection failed: {e}")
            return False

    async def send(self, msg: Message):
        if self.writer:
            self.writer.write(encode(msg))
            await self.writer.drain()

    async def receive_loop(self):
        while self._running:
            try:
                data = await self.reader.read(1024)
                if not data:
                    break
                msg = decode(data)
                await self.incoming.put(msg)
            except Exception as e:
                print(f"[network] Receive error: {e}")
                break

    async def disconnect(self):
        self._running = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
