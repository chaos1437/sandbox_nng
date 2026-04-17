# client/input_handler.py
from shared.constants import DIRS

class InputHandler:
    def __init__(self, resolved_controls: dict):
        # resolved_controls: {action: curses_key_int}
        self.key_to_dir = {}
        for action, key in resolved_controls.items():
            if action in DIRS:
                self.key_to_dir[key] = action

    def get_direction(self, key) -> str | None:
        return self.key_to_dir.get(key)

    def get_move_delta(self, direction: str) -> tuple[int, int]:
        return DIRS.get(direction, (0, 0))