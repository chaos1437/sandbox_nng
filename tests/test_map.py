# tests/test_map.py
import pytest
from server.ecs.map import GameMap


class TestGameMap:
    def test_is_passable_empty(self):
        m = GameMap(width=5, height=5)
        assert m.is_passable(0, 0) is True
        assert m.is_passable(2, 2) is True

    def test_is_passable_wall(self):
        m = GameMap(width=5, height=5)
        m.set_wall(2, 2)
        assert m.is_passable(2, 2) is False

    def test_is_passable_out_of_bounds(self):
        m = GameMap(width=5, height=5)
        assert m.is_passable(-1, 0) is False
        assert m.is_passable(5, 0) is False
        assert m.is_passable(0, 5) is False

    def test_to_lines_returns_deep_copy(self):
        m = GameMap(width=3, height=3)
        copy = m.to_lines()
        copy[0][0] = "#"
        assert m.tiles[0][0] != "#"
