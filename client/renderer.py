# client/renderer.py
import curses
from client.state import ClientGameState
from shared.constants import TILE_EMPTY, TILE_WALL, TILE_PLAYER

_CHAT_LINES = 5


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

    def _try_addch(self, y: int, x: int, ch: str):
        max_y, max_x = self.stdscr.getmaxyx()
        if 0 <= y < max_y and 0 <= x < max_x:
            try:
                self.stdscr.addch(y, x, ch)
            except curses.error:
                pass

    def _try_addstr(self, y: int, x: int, s: str):
        max_y, max_x = self.stdscr.getmaxyx()
        if 0 <= y < max_y and 0 <= x < max_x:
            try:
                self.stdscr.addstr(y, x, s[: max_x - x])
            except curses.error:
                pass

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

        for vy in range(min(self.viewport_height, max_y)):
            for vx in range(min(self.viewport_width, max_x)):
                wx = px - vw2 + vx
                wy = py - vh2 + vy
                if not self._is_visible(px, py, wx, wy, state):
                    self._try_addch(vy, vx, " ")
                    continue
                tile = state.get_tile(wx, wy)
                if tile is None:
                    self._try_addch(vy, vx, ".")
                    continue
                char = tile if tile != TILE_EMPTY else "."
                self._try_addch(vy, vx, char)

        for pid, (x, y) in state.player_positions.items():
            dx = x - px
            dy = y - py
            if abs(dx) > vw2 or abs(dy) > vh2:
                continue
            vx = vw2 + dx
            vy = vh2 + dy
            if 0 <= vy < max_y and 0 <= vx < max_x:
                char = TILE_PLAYER if pid == state.my_player_id else "P"
                self._try_addch(vy, vx, char)

        if state.chat_open:
            chat_start = self.viewport_height
            for i, line in enumerate(state.chat_messages[-_CHAT_LINES:]):
                y = chat_start + i
                text = f"{line.player_id}: {line.text}"
                self._try_addstr(y, 0, text)
        else:
            status = f"Player: {state.my_player_id} | Pos: {my_pos} | Seq: {state.server_seq} | Press t to chat"
            self._try_addstr(self.viewport_height, 0, status)

        self.stdscr.refresh()

    def get_key(self):
        return self.stdscr.getch()
