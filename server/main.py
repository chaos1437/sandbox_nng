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
from shared.network import Connection, read_message
from server.registry import ConnectionRegistry

log = setup_logger(__name__, 'server.log', console=False)


async def handle_client(
    reader, writer, world: GameWorld, registry: ConnectionRegistry, serializer: Serializer
):
    conn = Connection(reader, writer, serializer)
    registry.add(conn)
    log.info(f'Client connected: {conn.addr}')

    try:
        while True:
            msg = await read_message(reader, serializer)
            if msg is None:
                break
            log.info(f'Received: {msg.type} from {msg.player_id}')

            msg = Message(
                type=msg.type,
                seq=msg.seq,
                player_id=conn.player_id or msg.player_id,
                payload=msg.payload,
            )

            resp = world.handle_message(msg)
            if resp:
                if resp.player_id and not conn.player_id:
                    conn.player_id = resp.player_id
                    log.info(f'Player {conn.player_id} joined from {conn.addr}')
                resp = Message(
                    type=resp.type,
                    seq=resp.seq,
                    player_id=conn.player_id,
                    payload=resp.payload,
                )
                await registry.broadcast(resp)
                log.info(f'Broadcast {resp.type} to {len(registry.all())} clients')
    except Exception as e:
        log.error(f'Error: {e}\n{traceback.format_exc()}')
    finally:
        if conn.player_id:
            world.remove_entity(conn.player_id)
        conn.close()
        await conn.wait_closed()
        registry.remove(conn)


async def main(port: int = 8765, serializer: Serializer | None = None):
    if serializer is None:
        from shared.serializers import JsonSerializer
        serializer = JsonSerializer()

    cfg = load_server_config()
    port = port or cfg.port
    host = getattr(cfg, 'host', '0.0.0.0')

    world = GameWorld()
    from server.ecs.systems.movement_controller import MovementController
    from server.ecs.systems.chat import ChatSystem
    world.register_system(MovementController(max_speed_tiles_per_sec=cfg.player_max_speed_tiles_per_sec))
    world.register_system(ChatSystem())
    registry = ConnectionRegistry()

    last_seq = 0

    async def tick_broadcast():
        nonlocal last_seq
        while True:
            await asyncio.sleep(0.5)
            if registry.all() and world.seq != last_seq:
                last_seq = world.seq
                resp = world._make_state_sync()
                await registry.broadcast(resp)

    async def handler(reader, writer):
        await handle_client(reader, writer, world, registry, serializer)

    server = await asyncio.start_server(handler, host, port)
    log.info(f'Listening on {host}:{port}')
    asyncio.create_task(tick_broadcast())

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    asyncio.run(main(args.port))