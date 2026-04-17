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
from shared.constants import MsgType
from shared.logging import setup_logger

log = setup_logger("client", "client.log", console=False)

async def main(stdscr):
    stdscr.keypad(True)
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
    log.info(f"Connected to {args.host}:{args.port}")

    # Send join
    join_msg = Message(type=MsgType.JOIN, player_id="")
    await network.send(join_msg)
    log.debug("Join request sent")

    # Start receive loop
    receive_task = asyncio.create_task(network.receive_loop())

    running = True
    while running:
        # Yield to receive_loop so it can fill the queue
        await asyncio.sleep(0)

        # Process network messages (drain without blocking)
        while True:
            try:
                msg = network.incoming.get_nowait()
                log.debug(f"Received: {msg.type}")
                if msg.type == MsgType.STATE_SYNC:
                    state.apply_state_sync(msg.payload)
                    if not state.my_player_id and msg.player_id:
                        state.set_player_id(msg.player_id)
                        log.info(f"Joined as {msg.player_id}, map {state.map_width}x{state.map_height}")
            except asyncio.QueueEmpty:
                break

        # Render
        if state.map:
            renderer.render(state)

        # Input
        key = renderer.get_key()
        if key != -1:
            log.debug(f"Key pressed: {key} (quit={quit_key})")
            if key == quit_key:
                running = False
            elif key in input_handler.key_to_dir:
                direction = input_handler.key_to_dir[key]
                dx, dy = input_handler.get_move_delta(direction)
                log.debug(f"Move: {direction} ({dx},{dy})")
                move_msg = Message(
                    type=MsgType.MOVE,
                    seq=state.server_seq,
                    player_id=state.my_player_id,
                    payload={"dx": dx, "dy": dy},
                )
                await network.send(move_msg)

    receive_task.cancel()
    try:
        await receive_task
    except asyncio.CancelledError:
        pass
    leave_msg = Message(type=MsgType.LEAVE, player_id=state.my_player_id)
    await network.send(leave_msg)
    await network.disconnect()

if __name__ == "__main__":
    curses.wrapper(lambda stdscr: asyncio.run(main(stdscr)))
