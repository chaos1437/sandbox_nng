# server/network/handlers.py
"""Network handlers — bridge between TCP connections and services."""

import asyncio
import traceback
from shared.network import Connection, read_message
from shared.protocol import Message
from shared.logging import setup_logger
from shared.constants import MsgType
from server.services.join import JoinService
from server.services.move import MoveService
from server.services.chat import ChatService
from server.services.leave import LeaveService
from server.state.world import get_world

log = setup_logger(__name__, "server.log", console=False)


class ServiceRegistry:
    """Holds all service instances for message routing."""

    def __init__(self, cfg):
        self.join = JoinService()
        self.move = MoveService(
            max_speed_tiles_per_sec=cfg.player_max_speed_tiles_per_sec
        )
        self.chat = ChatService(
            max_lines=cfg.chat_max_lines,
            max_length=cfg.chat_max_length,
        )
        self.leave = LeaveService()

    def dispatch(self, msg: Message) -> Message | None:
        """Route message to appropriate service."""
        if msg.type == "join":
            return self.join.handle(msg)
        elif msg.type == "move":
            return self.move.handle(msg)
        elif msg.type == "chat":
            return self.chat.handle(msg)
        elif msg.type == "leave":
            return self.leave.handle(msg)
        return None


async def handle_client(reader, writer, connections, services, serializer):
    """Handle one client connection.

    - Reads messages
    - Dispatches to services via ServiceRegistry
    - Broadcasts responses to clients (per-client views for move, all for join/chat)
    - On disconnect, calls leave service
    """
    conn = Connection(reader, writer, serializer)
    connections.add(conn)
    log.info(f"Client connected: {conn.addr}")

    try:
        while True:
            msg = await read_message(reader, serializer)
            if msg is None:
                break
            log.info(f"Received: {msg.type} from {msg.player_id}")

            # Player ID comes from server-side connection state, not from client.
            # Client doesn't send player_id - server assigns it on join.
            normalized = Message(
                type=msg.type,
                seq=msg.seq,
                player_id=conn.player_id,
                payload=msg.payload,
            )
            resp = services.dispatch(normalized)

            if resp:
                if resp.player_id and not conn.player_id:
                    conn.player_id = resp.player_id
                    log.info(f"Player {conn.player_id} joined from {conn.addr}")

                world = get_world()

                if resp.type == "move_near":
                    mover_id = resp.player_id
                    for c in connections.all():
                        if c.player_id is None:
                            continue
                        if c.player_id == mover_id:
                            view = world.get_player_view(mover_id)
                            await c.send(
                                Message(
                                    type=resp.type,
                                    seq=resp.seq,
                                    player_id=mover_id,
                                    payload=view,
                                )
                            )
                        else:
                            if world.fov_manager.should_send_to(c.player_id, mover_id):
                                mover = world.get_player(mover_id)
                                await c.send(
                                    Message(
                                        type=resp.type,
                                        seq=resp.seq,
                                        player_id=mover_id,
                                        payload={
                                            "mover_id": mover_id,
                                            "x": mover.x,
                                            "y": mover.y,
                                        }
                                        if mover
                                        else {},
                                    )
                                )
                else:
                    await connections.broadcast(resp)

                log.info(f"Sent {resp.type} to clients")

    except Exception as e:
        log.error(f"Error: {e}\n{traceback.format_exc()}")
    finally:
        if conn.player_id:
            services.leave.handle(Message(type="leave", player_id=conn.player_id))
        conn.close()
        await conn.wait_closed()
        connections.remove(conn)
