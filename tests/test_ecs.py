# tests/test_ecs.py
import pytest
import time
from dataclasses import dataclass
from server.ecs.entity import Entity
from server.ecs.component import Component, PositionComponent
from server.ecs.system import System
from server.ecs.game_world import GameWorld
from server.ecs.systems.movement_controller import MovementController
from shared.protocol import Message
from shared.constants import MsgType


class TestEntity:
    def test_add_component_sets_entity_id(self):
        e = Entity("player1")
        comp = PositionComponent(entity_id="player1", x=10, y=20)
        e.add_component(comp)
        assert comp.entity_id == "player1"

    def test_add_component_get_component(self):
        e = Entity("player1")
        comp = PositionComponent(entity_id="player1", x=10, y=20)
        e.add_component(comp)
        retrieved = e.get_component(PositionComponent)
        assert retrieved is comp
        assert retrieved.x == 10
        assert retrieved.y == 20

    def test_get_component_returns_none_for_missing_type(self):
        e = Entity("player1")
        result = e.get_component(PositionComponent)
        assert result is None

    def test_has_component_returns_true_when_present(self):
        e = Entity("player1")
        comp = PositionComponent(entity_id="player1", x=10, y=20)
        e.add_component(comp)
        assert e.has_component(PositionComponent) is True

    def test_has_component_returns_false_when_missing(self):
        e = Entity("player1")
        assert e.has_component(PositionComponent) is False

    def test_remove_component(self):
        e = Entity("player1")
        comp = PositionComponent(entity_id="player1", x=10, y=20)
        e.add_component(comp)
        assert e.has_component(PositionComponent) is True
        e.remove_component(PositionComponent)
        assert e.has_component(PositionComponent) is False
        assert e.get_component(PositionComponent) is None


class TestPositionComponent:
    def test_has_correct_x_y_fields(self):
        pos = PositionComponent(entity_id="", x=5, y=10)
        assert pos.x == 5
        assert pos.y == 10
        assert pos.entity_id == ""

    def test_entity_id_is_settable(self):
        # Components have entity_id field but are not frozen
        pos = PositionComponent(entity_id="", x=5, y=10)
        pos.entity_id = "new_id"
        assert pos.entity_id == "new_id"


class TestSystem:
    def test_system_raises_notimplementederror_on_init(self):
        with pytest.raises(NotImplementedError):
            System()


class TestMovementController:
    def test_rate_limits_correctly(self):
        ctrl = MovementController(max_speed_tiles_per_sec=10.0)
        world = GameWorld()
        player_id = "p1"

        # First move should always be allowed (no previous move time)
        result = ctrl.on_before_move(world, player_id, 1, 0)
        assert result is True

        # Immediate second move should be blocked
        result = ctrl.on_before_move(world, player_id, 1, 0)
        assert result is False

    def test_records_violations(self):
        ctrl = MovementController(max_speed_tiles_per_sec=10.0)
        world = GameWorld()
        player_id = "p1"

        # First move allowed
        ctrl.on_before_move(world, player_id, 1, 0)
        # Immediate second move - violation
        ctrl.on_before_move(world, player_id, 1, 0)

        stats = ctrl.get_stats(player_id)
        assert stats["violations"] == 1
        assert stats["total_moves"] == 1

    def test_cleans_up_on_player_leave(self):
        ctrl = MovementController(max_speed_tiles_per_sec=10.0)
        world = GameWorld()
        player_id = "p1"

        # Make a move to create a record
        ctrl.on_before_move(world, player_id, 1, 0)
        assert ctrl.get_stats(player_id)["total_moves"] == 1

        # Player leaves
        ctrl.on_player_leave(world, player_id)

        # Record should be cleaned up
        stats = ctrl.get_stats(player_id)
        assert stats["total_moves"] == 0
        assert stats["violations"] == 0


# Concrete test system for testing GameWorld hooks
class HookCollector:
    def __init__(self):
        self.on_player_join_called = []
        self.on_before_move_called = []
        self.on_after_move_called = []
        self.on_player_leave_called = []
        self._block_move = False

    def set_block_move(self, block: bool):
        self._block_move = block

    def on_player_join(self, world: GameWorld, player_id: str) -> None:
        self.on_player_join_called.append(player_id)

    def on_before_move(self, world: GameWorld, player_id: str, dx: int, dy: int) -> bool:
        self.on_before_move_called.append((player_id, dx, dy))
        return not self._block_move

    def on_after_move(self, world: GameWorld, player_id: str, dx: int, dy: int) -> None:
        self.on_after_move_called.append((player_id, dx, dy))

    def on_player_leave(self, world: GameWorld, player_id: str) -> None:
        self.on_player_leave_called.append(player_id)


class TestGameWorld:
    def test_register_system_adds_to_list(self):
        world = GameWorld()
        ctrl = MovementController()
        world.register_system(ctrl)
        assert ctrl in world.systems

    def test_handle_message_join_creates_entity(self):
        world = GameWorld()
        msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(msg)
        assert resp is not None
        assert resp.type == MsgType.STATE_SYNC
        # Entity should be created - player_id is in the players dict
        player_id = list(resp.payload["players"].keys())[0]
        entity = world.get_entity(player_id)
        assert entity is not None
        assert entity.has_component(PositionComponent)

    def test_handle_message_join_calls_on_player_join(self):
        world = GameWorld()
        ts = HookCollector()
        world.register_system(ts)
        msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(msg)
        assert len(ts.on_player_join_called) == 1

    def test_handle_message_move_moves_entity(self):
        world = GameWorld()
        # First join to create entity
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        player_id = list(resp.payload["players"].keys())[0]

        # Get initial position
        entity = world.get_entity(player_id)
        initial_x = entity.get_component(PositionComponent).x

        # Move
        move_msg = Message(type=MsgType.MOVE, player_id=player_id, payload={"dx": 1, "dy": 0})
        world.handle_message(move_msg)

        # Check position updated
        new_x = entity.get_component(PositionComponent).x
        assert new_x == initial_x + 1

    def test_handle_message_move_calls_hooks(self):
        world = GameWorld()
        ts = HookCollector()
        world.register_system(ts)
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        player_id = resp.player_id

        ts.on_before_move_called.clear()
        ts.on_after_move_called.clear()
        move_msg = Message(type=MsgType.MOVE, player_id=player_id, payload={"dx": 1, "dy": 0})
        world.handle_message(move_msg)

        assert len(ts.on_before_move_called) == 1
        assert ts.on_before_move_called[0] == (player_id, 1, 0)
        assert len(ts.on_after_move_called) == 1
        assert ts.on_after_move_called[0] == (player_id, 1, 0)

    def test_handle_message_leave_removes_entity(self):
        world = GameWorld()
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        player_id = resp.player_id

        leave_msg = Message(type=MsgType.LEAVE, player_id=player_id)
        world.handle_message(leave_msg)

        assert world.get_entity(player_id) is None

    def test_handle_message_leave_calls_on_player_leave(self):
        world = GameWorld()
        ts = HookCollector()
        world.register_system(ts)
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        player_id = resp.player_id

        ts.on_player_leave_called.clear()
        leave_msg = Message(type=MsgType.LEAVE, player_id=player_id)
        world.handle_message(leave_msg)

        assert len(ts.on_player_leave_called) == 1
        assert ts.on_player_leave_called[0] == player_id

    def test_on_before_move_false_blocks_move(self):
        world = GameWorld()
        ts = HookCollector()
        ts.set_block_move(True)
        world.register_system(ts)
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        player_id = list(resp.payload["players"].keys())[0]

        entity = world.get_entity(player_id)
        initial_x = entity.get_component(PositionComponent).x

        move_msg = Message(type=MsgType.MOVE, player_id=player_id, payload={"dx": 5, "dy": 0})
        world.handle_message(move_msg)

        # Position should not have changed
        new_x = entity.get_component(PositionComponent).x
        assert new_x == initial_x

    def test_get_state_snapshot_structure(self):
        world = GameWorld()
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        # Player_id is in the entities dict, not in the response
        player_id = list(world.entities.keys())[0]

        snap = world.get_state_snapshot()
        assert "seq" in snap
        assert "players" in snap
        assert player_id in snap["players"]
        assert "x" in snap["players"][player_id]
        assert "y" in snap["players"][player_id]

    def test_get_state_snapshot_with_map(self):
        world = GameWorld()
        join_msg = Message(type=MsgType.JOIN)
        world.handle_message(join_msg)

        snap = world.get_state_snapshot(include_map=True)
        assert "map" in snap
        assert "width" in snap["map"]
        assert "height" in snap["map"]
        assert "tiles" in snap["map"]

    def test_multiple_systems_called_in_registration_order(self):
        world = GameWorld()
        call_order = []

        class FirstSystem:
            def __init__(self):
                pass

            def on_player_join(self, world, player_id):
                call_order.append("first")

        class SecondSystem:
            def __init__(self):
                pass

            def on_player_join(self, world, player_id):
                call_order.append("second")

        world.register_system(FirstSystem())
        world.register_system(SecondSystem())

        join_msg = Message(type=MsgType.JOIN)
        world.handle_message(join_msg)

        assert call_order == ["first", "second"]
