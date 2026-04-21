# client/main.py
import asyncio
import curses
from client.config import resolve_controls
from client.network import NetworkClient
from client.state import ClientGameState
from client.input_handler import InputHandler
from client.renderer import RoguelikeRenderer
from shared.protocol import Message
from shared.constants import MsgType
from shared.logging import setup_logger

log = setup_logger("client", "client.log", console=False)


async def main(stdscr, config):
    """Run client. config is a ClientConfig dataclass."""
    stdscr.keypad(True)

    state = ClientGameState()
    network = NetworkClient(config.host, config.port)
    renderer = RoguelikeRenderer(
        stdscr,
        viewport_width=getattr(config, "viewport_width", 32),
        viewport_height=getattr(config, "viewport_height", 32),
        fov_radius=getattr(config, "fov_radius", 8),
    )
    controls = resolve_controls(config.controls)
    input_handler = InputHandler(controls)
    quit_key = controls.get("quit", ord("q"))

    if not await network.connect():
        return
    log.info(f"Connected to {config.host}:{config.port}")

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
                if msg.type == MsgType.STATE_SYNC:
                    state.apply_state_sync(msg.payload)
                    if not state.my_player_id and msg.player_id:
                        state.set_player_id(msg.player_id)
            except asyncio.QueueEmpty:
                break

        # Render
        if state.chunks:
            log.debug(f"Rendering with {len(state.chunks)} chunks")
            renderer.render(state)
        else:
            log.debug("No chunks to render")

        # Input
        curses.napms(16)  # ~60fps cap, prevents 100% CPU spin
        key = renderer.get_key()
        if key != -1:
            log.debug(
                f"Key pressed: {key} (quit={quit_key}, chat={input_handler.chat_key})"
            )
            if key == quit_key:
                running = False
            elif key == input_handler.chat_key:
                state.chat_open = not state.chat_open
                if not state.chat_open:
                    state.chat_input = ""
            elif state.chat_open:
                if key in (curses.KEY_ENTER, 10, 13):
                    if state.chat_input:
                        chat_msg = Message(
                            type=MsgType.CHAT,
                            seq=state.server_seq,
                            player_id=state.my_player_id,
                            payload={"text": state.chat_input},
                        )
                        await network.send(chat_msg)
                        state.chat_input = ""
                        state.chat_open = False
                elif key == 27:  # ESC
                    state.chat_input = ""
                    state.chat_open = False
                elif key == curses.KEY_BACKSPACE:
                    state.chat_input = state.chat_input[:-1]
                elif 32 <= key <= 126:
                    state.chat_input += chr(key)
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
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    from shared.config import load_client_config

    cfg = load_client_config()
    # CLI args override config file
    cfg.host = args.host
    cfg.port = args.port

    curses.wrapper(lambda stdscr: asyncio.run(main(stdscr, cfg)))
