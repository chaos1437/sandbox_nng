# server/main.py
import asyncio
import traceback
import argparse
from server.game_state import GameState
from server.handlers import handle_message
from shared.protocol import encode, decode, Message
from shared.constants import MSG_JOIN, MSG_LEAVE, MSG_STATE_SYNC
from shared.logging import setup_logger

log = setup_logger("server", "server.log")


class ClientConnection:
    def __init__(self, reader, writer, state):
        self.reader = reader
        self.writer = writer
        self.state = state
        self.player_id: str | None = None
        self.addr = writer.get_extra_info("peername")


async def broadcast(clients: list[ClientConnection], msg: Message):
    """Send message to all connected clients."""
    data = encode(msg) + b'\n'
    dead = []
    for client in clients:
        try:
            client.writer.write(data)
            await client.writer.drain()
        except Exception:
            dead.append(client)
    for client in dead:
        clients.remove(client)


async def handle_client(reader, writer, state, clients: list[ClientConnection]):
    addr = writer.get_extra_info("peername")
    log.info(f"Client connected: {addr}")
    conn = ClientConnection(reader, writer, state)
    clients.append(conn)

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            msg = decode(data.rstrip(b'\n'))
            log.info(f"Received: {msg.type} from {msg.player_id}")

            resp = handle_message(conn.state, msg)
            if resp:
                if resp.type == MSG_STATE_SYNC and not conn.player_id:
                    conn.player_id = resp.player_id
                    log.info(f"Player {conn.player_id} joined from {addr}")
                # Broadcast state to ALL clients
                await broadcast(clients, resp)
                log.info(f"Broadcast {resp.type} to {len(clients)} clients")
    except Exception as e:
        log.error(f"Error: {e}\n{traceback.format_exc()}")
    finally:
        if conn.player_id:
            conn.state.remove_player(conn.player_id)
        clients.remove(conn)
        writer.close()
        await writer.wait_closed()
        log.info(f"Client disconnected: {addr}")


async def main(port: int = 8765):
    state = GameState()
    clients: list[ClientConnection] = []

    async def handler(reader, writer):
        await handle_client(reader, writer, state, clients)

    server = await asyncio.start_server(handler, "0.0.0.0", port)
    log.info(f"Listening on port {port}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    asyncio.run(main(args.port))
