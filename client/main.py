# client/main.py
import asyncio
import argparse
import curses
from client.config import load_client_config, resolve_controls
from client.network import NetworkClient
from client.state import ClientGameState
from client.input_handler import InputHandler
from client.renderer import RoguelikeRenderer
from shared.protocol import Message
from shared.constants import MSG_JOIN, MSG_MOVE, MSG_LEAVE

async def main(stdscr):
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    config = load_client_config()
    state = ClientGameState()
    network = NetworkClient(args.host, args.port)
    renderer = RoguelikeRenderer(stdscr)
    controls = resolve_controls(config.get("controls", {}))
    input_handler = InputHandler(controls)
    quit_key = controls.get("quit", ord('q'))

    if not await network.connect():
        return

    # Send join
    join_msg = Message(type=MSG_JOIN, player_id="")
    await network.send(join_msg)

    # Start receive loop
    receive_task = asyncio.create_task(network.receive_loop())

    running = True
    while running:
        # Process network messages (drain without blocking)
        while True:
            try:
                msg = network.incoming.get_nowait()
                if msg.type == "joined":
                    state.set_player_id(msg.player_id)
                    network.player_id = msg.player_id
                    state.apply_map_sync(msg.payload["map"])
                elif msg.type == "state_sync":
                    state.apply_state_sync(msg.payload)
            except asyncio.QueueEmpty:
                break

        # Render
        if state.map:
            renderer.render(state)

        # Input
        curses.napms(33)  # ~30fps
        key = renderer.get_key()
        if key != -1:
            if key == quit_key:
                running = False
            elif key in input_handler.key_to_dir:
                direction = input_handler.key_to_dir[key]
                dx, dy = input_handler.get_move_delta(direction)
                move_msg = Message(
                    type=MSG_MOVE,
                    seq=state.server_seq,
                    player_id=network.player_id,
                    payload={"dx": dx, "dy": dy},
                )
                await network.send(move_msg)

    receive_task.cancel()
    try:
        await receive_task
    except asyncio.CancelledError:
        pass
    leave_msg = Message(type=MSG_LEAVE, player_id=network.player_id)
    await network.send(leave_msg)
    await network.disconnect()

if __name__ == "__main__":
    curses.wrapper(lambda stdscr: asyncio.run(main(stdscr)))
