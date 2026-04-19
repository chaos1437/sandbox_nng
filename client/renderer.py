# client/renderer.py
import curses
from client.state import ClientGameState
from shared.constants import TILE_EMPTY, TILE_WALL, TILE_PLAYER

_CHAT_LINES = 5
_CHAT_INPUT_LINE = _CHAT_LINES + 1


class RoguelikeRenderer:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

    def render(self, state: ClientGameState):
        self.stdscr.clear()
        max_y, max_x = self.stdscr.getmaxyx()
        map_bottom = state.map_height

        # Draw map
        for y, row in enumerate(state.map):
            for x, tile in enumerate(row):
                if y >= max_y or x >= max_x:
                    break
                char = tile if tile != TILE_EMPTY else "."
                self.stdscr.addch(y, x, char)

        # Draw players (overwrite map tiles)
        for pid, (x, y) in state.player_positions.items():
            if y >= max_y or x >= max_x:
                continue
            char = TILE_PLAYER if pid == state.my_player_id else "P"
            self.stdscr.addch(y, x, char)

        # Chat area: lines map_height to map_height + _CHAT_LINES
        if state.chat_open:
            chat_start = map_bottom
            # Show last 5 messages
            for i, line in enumerate(state.chat_messages[-_CHAT_LINES:]):
                y = chat_start + i
                if y >= max_y:
                    break
                text = f"{line.player_id}: {line.text}"
                if len(text) > max_x - 1:
                    text = text[: max_x - 1]
                self.stdscr.addstr(y, 0, text)

            # Input line
            input_y = chat_start + _CHAT_LINES
            if input_y < max_y:
                prompt = f"> {state.chat_input}"
                if len(prompt) > max_x - 1:
                    prompt = prompt[: max_x - 1]
                self.stdscr.addstr(input_y, 0, prompt)
                self.stdscr.clrtoeol()
        else:
            # Status line
            my_pos = state.get_my_position()
            status = f"Player: {state.my_player_id} | Pos: {my_pos} | Seq: {state.server_seq} | Press t to chat"
            if len(status) > max_x - 1:
                status = status[: max_x - 1]
            self.stdscr.addstr(map_bottom, 0, status)

        self.stdscr.refresh()

    def get_key(self):
        return self.stdscr.getch()
