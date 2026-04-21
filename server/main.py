# server/main.py
"""Server entry point — async TCP server with event-driven architecture."""

import asyncio
import argparse
from shared.config import load_server_config
from shared.logging import setup_logger
from shared.serializers import JsonSerializer
from server.network.connections import Connections
from server.network.handlers import handle_client, ServiceRegistry

log = setup_logger(__name__, "server.log", console=False)


async def main(port: int | None = None, serializer=None):
    """Start the game server."""
    if serializer is None:
        serializer = JsonSerializer()

    cfg = load_server_config()
    port = port or cfg.port
    host = getattr(cfg, "host", "0.0.0.0")

    connections = Connections()
    services = ServiceRegistry(cfg)

    last_seq = 0

    async def tick_broadcast():
        """Broadcast state sync periodically to all clients."""
        nonlocal last_seq
        from server.state.world import get_world
        from shared.protocol import Message
        from shared.constants import MsgType

        while True:
            await asyncio.sleep(cfg.state_sync_interval)
            world = get_world()
            if connections.all() and world.seq != last_seq:
                last_seq = world.seq
                resp = Message(
                    type=MsgType.STATE_SYNC,
                    seq=world.seq,
                    payload=world.get_state_snapshot(),
                )
                await connections.broadcast(resp)

    async def handler(reader, writer):
        await handle_client(reader, writer, connections, services, serializer)

    server = await asyncio.start_server(handler, host, port)
    log.info(f"Listening on {host}:{port}")
    asyncio.create_task(tick_broadcast())

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    asyncio.run(main(args.port))
