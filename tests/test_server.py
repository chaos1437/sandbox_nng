# tests/test_server.py
import pytest
from server.map import GameMap
from server.player import Player
from server.game_state import GameState
from server.handlers import handle_message
from shared.protocol import Message
from shared.constants import MSG_JOIN, MSG_MOVE, MSG_LEAVE, MSG_STATE_SYNC


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


class TestPlayer:
    def test_move_valid(self):
        m = GameMap(width=5, height=5)
        p = Player("p1", 2, 2)
        assert p.move(1, 0, m) is True
        assert p.x == 3
        assert p.y == 2

    def test_move_into_wall(self):
        m = GameMap(width=5, height=5)
        m.set_wall(3, 2)
        p = Player("p1", 2, 2)
        assert p.move(1, 0, m) is False
        assert p.x == 2
        assert p.y == 2


class TestGameState:
    def test_add_player_generates_id(self):
        s = GameState()
        p = s.add_player()
        assert p.player_id is not None
        assert len(p.player_id) == 8

    def test_add_player_at_center(self):
        s = GameState()
        p = s.add_player()
        assert p.x == s.map.width // 2
        assert p.y == s.map.height // 2

    def test_add_player_custom_id(self):
        s = GameState()
        p = s.add_player("myid")
        assert p.player_id == "myid"

    def test_remove_player(self):
        s = GameState()
        p = s.add_player()
        pid = p.player_id
        s.remove_player(pid)
        assert pid not in s.players

    def test_move_player(self):
        s = GameState()
        p = s.add_player("p1")
        assert p.x == s.map.width // 2
        assert p.y == s.map.height // 2
        result = s.move_player("p1", 1, 0)
        assert result is True
        assert p.x == s.map.width // 2 + 1

    def test_get_state_snapshot(self):
        s = GameState()
        p = s.add_player("p1")
        snap = s.get_state_snapshot()
        assert snap["seq"] == 0
        assert "p1" in snap["players"]
        assert snap["players"]["p1"]["x"] == p.x

    def test_get_state_snapshot_with_include_map(self):
        s = GameState()
        s.add_player("p1")
        snap = s.get_state_snapshot(include_map=True)
        assert "map" in snap
        assert snap["map"]["width"] == s.map.width
        assert snap["map"]["height"] == s.map.height
        assert "tiles" in snap["map"]


class TestHandlers:
    def test_join_creates_player_returns_state_sync(self):
        s = GameState()
        msg = Message(type=MSG_JOIN)
        resp = handle_message(s, msg)
        assert resp is not None
        assert resp.type == MSG_STATE_SYNC
        assert resp.player_id in s.players

    def test_move_updates_position_returns_state_sync(self):
        s = GameState()
        p = s.add_player("p1")
        old_x = p.x
        msg = Message(type=MSG_MOVE, player_id="p1", payload={"dx": 2, "dy": 0})
        resp = handle_message(s, msg)
        assert resp is not None
        assert resp.type == MSG_STATE_SYNC
        assert p.x == old_x + 2

    def test_leave_removes_player(self):
        s = GameState()
        p = s.add_player("p1")
        msg = Message(type=MSG_LEAVE, player_id="p1")
        resp = handle_message(s, msg)
        assert resp is None
        assert "p1" not in s.players

    def test_move_unknown_player_returns_state_sync(self):
        s = GameState()
        msg = Message(type=MSG_MOVE, player_id="unknown", payload={"dx": 1, "dy": 0})
        resp = handle_message(s, msg)
        assert resp is not None
        assert resp.type == MSG_STATE_SYNC
