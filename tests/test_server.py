# tests/test_server.py
import pytest
from server.map import GameMap
from server.ecs.game_world import GameWorld
from server.ecs.entity import Entity
from server.ecs.component import PositionComponent
from shared.protocol import Message
from shared.constants import MsgType


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


class TestGameWorld:
    def test_join_creates_player_returns_state_sync(self):
        world = GameWorld()
        msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(msg)
        assert resp is not None
        assert resp.type == MsgType.STATE_SYNC
        assert resp.player_id in world.entities

    def test_move_updates_position_returns_state_sync(self):
        world = GameWorld()
        # Pre-add a player entity
        e = Entity("p1")
        spawn_x = world.map.width // 2
        spawn_y = world.map.height // 2
        e.add_component(PositionComponent(x=spawn_x, y=spawn_y))
        world.add_entity(e)
        old_x = spawn_x
        msg = Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 2, "dy": 0})
        resp = world.handle_message(msg)
        assert resp is not None
        assert resp.type == MsgType.STATE_SYNC
        assert e.get_component(PositionComponent).x == old_x + 2

    def test_leave_removes_player(self):
        world = GameWorld()
        # Pre-add a player entity
        e = Entity("p1")
        e.add_component(PositionComponent(x=2, y=2))
        world.add_entity(e)
        msg = Message(type=MsgType.LEAVE, player_id="p1")
        resp = world.handle_message(msg)
        assert resp is None
        assert "p1" not in world.entities

    def test_move_unknown_player_returns_state_sync(self):
        world = GameWorld()
        msg = Message(type=MsgType.MOVE, player_id="unknown", payload={"dx": 1, "dy": 0})
        resp = world.handle_message(msg)
        assert resp is not None
        assert resp.type == MsgType.STATE_SYNC
