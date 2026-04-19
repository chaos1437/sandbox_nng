# tests/test_shared/test_constants.py
import pytest
from shared.constants import DIRS, TILE_EMPTY, TILE_WALL, TILE_PLAYER


class TestConstants:
    def test_dirs_values(self):
        assert DIRS["up"] == (0, -1)
        assert DIRS["down"] == (0, 1)
        assert DIRS["right"] == (1, 0)
        assert DIRS["left"] == (-1, 0)

    def test_tile_chars(self):
        assert TILE_EMPTY == "."
        assert TILE_WALL == "#"
        assert TILE_PLAYER == "@"
