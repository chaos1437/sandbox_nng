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

async def handle_client(reader, writer, state):
    addr = writer.get_extra_info("peername")
    log.info(f"Client connected: {addr}")
    player_id = None

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            msg = decode(data.rstrip(b'\n'))
            log.info(f"Received: {msg.type} from {msg.player_id}")

            if msg.type == MSG_JOIN:
                player_id = msg.player_id

            resp = handle_message(state, msg)
            if resp:
                if resp.type == MSG_STATE_SYNC and not player_id:
                    player_id = resp.player_id
                writer.write(encode(resp) + b'\n')
                await writer.drain()
                log.info(f"Sent {resp.type} to {resp.player_id}")
    except Exception as e:
        log.error(f"Error: {e}\n{traceback.format_exc()}")
    finally:
        if player_id:
            state.remove_player(player_id)
        writer.close()
        await writer.wait_closed()
        log.info(f"Client disconnected: {addr}")

async def main(port: int = 8765):
    state = GameState()
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, state), "0.0.0.0", port
    )
    log.info(f"Listening on port {port}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    asyncio.run(main(args.port))
