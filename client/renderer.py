# client/renderer.py
import curses
from client.state import ClientGameState
from shared.constants import TILE_EMPTY, TILE_WALL, TILE_PLAYER

class RoguelikeRenderer:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

    def render(self, state: ClientGameState):
        self.stdscr.clear()

        # Draw map
        for y, row in enumerate(state.map):
            for x, tile in enumerate(row):
                char = tile if tile != TILE_EMPTY else "."
                self.stdscr.addch(y, x, char)

        # Draw players (overwrite map tiles)
        for pid, (x, y) in state.player_positions.items():
            char = TILE_PLAYER if pid == state.my_player_id else "P"
            self.stdscr.addch(y, x, char)

        # Status line
        my_pos = state.get_my_position()
        status = f"Player: {state.my_player_id} | Pos: {my_pos} | Seq: {state.server_seq}"
        self.stdscr.addstr(state.map_height + 1, 0, status)

        self.stdscr.refresh()

    def get_key(self):
        return self.stdscr.getch()
