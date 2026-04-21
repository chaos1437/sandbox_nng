# client/renderer.py
import curses
from client.state import ClientGameState
from shared.constants import TILE_EMPTY, TILE_WALL, TILE_PLAYER

_CHAT_LINES = 5
_CHAT_INPUT_LINE = _CHAT_LINES + 1


class RoguelikeRenderer:
    def __init__(self, stdscr, viewport_width=32, viewport_height=32, fov_radius=8):
        self.stdscr = stdscr
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.fov_radius = fov_radius

    def _is_visible(
        self, px: int, py: int, tx: int, ty: int, state: ClientGameState
    ) -> bool:
        dx = abs(tx - px)
        dy = abs(ty - py)
        if dx > self.fov_radius or dy > self.fov_radius:
            return False
        return True

    def render(self, state: ClientGameState):
        self.stdscr.clear()
        max_y, max_x = self.stdscr.getmaxyx()

        my_pos = state.get_my_position()
        if my_pos is None:
            self.stdscr.refresh()
            return

        px, py = my_pos
        vw2 = self.viewport_width // 2
        vh2 = self.viewport_height // 2

        for vy in range(self.viewport_height):
            for vx in range(self.viewport_width):
                wx = px - vw2 + vx
                wy = py - vh2 + vy
                if vy >= max_y or vx >= max_x:
                    break
                if not self._is_visible(px, py, wx, wy, state):
                    self.stdscr.addch(vy, vx, " ")
                    continue
                tile = state.get_tile(wx, wy)
                if tile is None:
                    self.stdscr.addch(vy, vx, ".")
                    continue
                char = tile if tile != TILE_EMPTY else "."
                self.stdscr.addch(vy, vx, char)

        for pid, (x, y) in state.player_positions.items():
            dx = x - px
            dy = y - py
            if abs(dx) > vw2 or abs(dy) > vh2:
                continue
            vx = vw2 + dx
            vy = vh2 + dy
            if vy >= max_y or vx >= max_x or vy < 0 or vx < 0:
                continue
            char = TILE_PLAYER if pid == state.my_player_id else "P"
            self.stdscr.addch(vy, vx, char)

        if state.chat_open:
            chat_start = self.viewport_height
            for i, line in enumerate(state.chat_messages[-_CHAT_LINES:]):
                y = chat_start + i
                if y >= max_y:
                    break
                text = f"{line.player_id}: {line.text}"
                if len(text) > max_x - 1:
                    text = text[: max_x - 1]
                self.stdscr.addstr(y, 0, text)

            input_y = chat_start + _CHAT_LINES
            if input_y < max_y:
                prompt = f"> {state.chat_input}"
                if len(prompt) > max_x - 1:
                    prompt = prompt[: max_x - 1]
                self.stdscr.addstr(input_y, 0, prompt)
                self.stdscr.clrtoeol()
        else:
            status = f"Player: {state.my_player_id} | Pos: {my_pos} | Seq: {state.server_seq} | Press t to chat"
            if len(status) > max_x - 1:
                status = status[: max_x - 1]
            self.stdscr.addstr(self.viewport_height, 0, status)

        self.stdscr.refresh()

    def get_key(self):
        return self.stdscr.getch()
