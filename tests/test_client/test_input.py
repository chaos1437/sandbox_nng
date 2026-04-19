# tests/test_client/test_input.py
import pytest
from client.input_handler import InputHandler


class TestInputHandler:
    def test_key_to_dir_mapping(self):
        resolved = {"up": 259, "down": 258, "left": 260, "right": 261, "quit": 113, "chat": 116}
        h = InputHandler(resolved)
        assert h.key_to_dir[259] == "up"
        assert h.key_to_dir[258] == "down"
        assert h.key_to_dir[260] == "left"
        assert h.key_to_dir[261] == "right"

    def test_get_direction(self):
        resolved = {"up": 259, "down": 258, "quit": 113, "chat": 116}
        h = InputHandler(resolved)
        assert h.get_direction(259) == "up"
        assert h.get_direction(999) is None

    def test_get_move_delta(self):
        resolved = {"up": 259, "down": 258, "chat": 116}
        h = InputHandler(resolved)
        assert h.get_move_delta("up") == (0, -1)
        assert h.get_move_delta("down") == (0, 1)
        assert h.get_move_delta("right") == (1, 0)
        assert h.get_move_delta("left") == (-1, 0)
        assert h.get_move_delta("unknown") == (0, 0)
