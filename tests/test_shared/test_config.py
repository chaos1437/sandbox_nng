# tests/test_shared/test_config.py
import pytest
from client.config import resolve_controls


class TestResolveControls:
    def test_single_char_converted_to_ord(self):
        controls = {"up": "w", "down": "s", "left": "a", "right": "d", "quit": "q"}
        resolved = resolve_controls(controls)
        assert resolved["up"] == ord("w")
        assert resolved["down"] == ord("s")
        assert resolved["left"] == ord("a")
        assert resolved["right"] == ord("d")
        assert resolved["quit"] == ord("q")

    def test_quoted_single_char_converted_to_ord(self):
        controls = {"up": "'w'", "quit": "'q'"}
        resolved = resolve_controls(controls)
        assert resolved["up"] == ord("w")
        assert resolved["quit"] == ord("q")

    def test_double_quoted_single_char_converted_to_ord(self):
        controls = {'up': '"w"', "quit": '"q"'}
        resolved = resolve_controls(controls)
        assert resolved["up"] == ord("w")
        assert resolved["quit"] == ord("q")

    def test_curses_key_names_preserved(self):
        controls = {"up": "KEY_UP", "down": "KEY_DOWN"}
        resolved = resolve_controls(controls)
        import curses
        assert resolved["up"] == curses.KEY_UP
        assert resolved["down"] == curses.KEY_DOWN

    def test_mixed_controls(self):
        controls = {"up": "w", "down": "KEY_DOWN", "quit": "q"}
        resolved = resolve_controls(controls)
        import curses
        assert resolved["up"] == ord("w")
        assert resolved["down"] == curses.KEY_DOWN
        assert resolved["quit"] == ord("q")
