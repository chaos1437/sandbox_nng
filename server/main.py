# server/main.py
import asyncio
import traceback
import argparse
from server.ecs.game_world import GameWorld
from shared.protocol import Message
from shared.constants import MsgType
from shared.logging import setup_logger
from shared.serializers import Serializer
from shared.config import load_server_config

log = setup_logger("server", "server.log")


class ClientConnection:
    def __init__(self, reader, writer, serializer: Serializer):
        self.reader = reader
        self.writer = writer
        self.serializer = serializer
        self.player_id: str | None = None
        self.addr = writer.get_extra_info("peername")

    async def send(self, msg: Message):
        data = self.serializer.encode(msg) + b'\n'
        self.writer.write(data)
        await self.writer.drain()


async def broadcast(clients: list[ClientConnection], msg: Message):
    """Send message to all connected clients. Return list of alive clients."""
    alive = []
    for conn in clients:
        try:
            await conn.send(msg)
            alive.append(conn)
        except Exception:
            conn.writer.close()
    return alive


async def handle_client(
    reader, writer, world: GameWorld,
    clients: list[ClientConnection], serializer: Serializer
):
    conn = ClientConnection(reader, writer, serializer)
    clients.append(conn)
    log.info(f"Client connected: {conn.addr}")

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            msg = serializer.decode(data.rstrip(b'\n'))
            log.info(f"Received: {msg.type} from {msg.player_id}")

            # SECURITY: ignore player_id from client, use server-assigned one
            msg = Message(
                type=msg.type,
                seq=msg.seq,
                player_id=conn.player_id or msg.player_id,
                payload=msg.payload,
            )

            resp = world.handle_message(msg)
            if resp:
                # SECURITY: always use server-assigned player_id
                if resp.player_id and not conn.player_id:
                    conn.player_id = resp.player_id
                    log.info(f"Player {conn.player_id} joined from {conn.addr}")
                resp = Message(
                    type=resp.type,
                    seq=resp.seq,
                    player_id=conn.player_id,
                    payload=resp.payload,
                )
                clients = await broadcast(clients, resp)
                log.info(f"Broadcast {resp.type} to {len(clients)} clients")
    except Exception as e:
        log.error(f"Error: {e}\n{traceback.format_exc()}")
    finally:
        if conn.player_id:
            world.remove_entity(conn.player_id)
        clients.remove(conn)
        conn.writer.close()
        await conn.writer.wait_closed()
        log.info(f"Client disconnected: {conn.addr}")


async def main(port: int = 8765, serializer: Serializer | None = None):
    if serializer is None:
        from shared.serializers import JsonSerializer
        serializer = JsonSerializer()

    cfg = load_server_config()
    # CLI port overrides config
    port = port or cfg.port

    world = GameWorld()
    from server.ecs.systems.movement_controller import MovementController
    world.register_system(MovementController(max_speed_tiles_per_sec=cfg.player_max_speed_tiles_per_sec))
    clients: list[ClientConnection] = []

    async def handler(reader, writer):
        await handle_client(reader, writer, world, clients, serializer)

    server = await asyncio.start_server(handler, "0.0.0.0", port)
    log.info(f"Listening on port {port}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    asyncio.run(main(args.port))
