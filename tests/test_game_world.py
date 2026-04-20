# tests/test_game_world.py
import pytest
from server.ecs.game_world import GameWorld
from server.ecs.entity import Entity
from server.ecs.component import PositionComponent
from shared.protocol import Message
from shared.constants import MsgType


class TestGameWorld:
    def test_register_system_adds_to_list(self, world, movement_controller):
        world.register_system(movement_controller)
        assert movement_controller in world.systems

    def test_handle_message_join_creates_entity(self, world):
        msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(msg)
        assert resp is not None
        assert resp.type == MsgType.STATE_SYNC
        player_id = list(resp.payload["players"].keys())[0]
        entity = world.get_entity(player_id)
        assert entity is not None
        assert entity.has_component(PositionComponent)

    def test_handle_message_join_calls_on_player_join(self, world, hook_collector):
        world.register_system(hook_collector)
        msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(msg)
        assert len(hook_collector.on_player_join_called) == 1

    def test_handle_message_move_moves_entity(self, world):
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        player_id = list(resp.payload["players"].keys())[0]

        entity = world.get_entity(player_id)
        initial_x = entity.get_component(PositionComponent).x

        move_msg = Message(type=MsgType.MOVE, player_id=player_id, payload={"dx": 1, "dy": 0})
        world.handle_message(move_msg)

        new_x = entity.get_component(PositionComponent).x
        assert new_x == initial_x + world.chunks.tile_size

    def test_handle_message_move_calls_hooks(self, world, hook_collector):
        world.register_system(hook_collector)
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        player_id = resp.player_id

        hook_collector.on_before_move_called.clear()
        hook_collector.on_after_move_called.clear()
        move_msg = Message(type=MsgType.MOVE, player_id=player_id, payload={"dx": 1, "dy": 0})
        world.handle_message(move_msg)

        assert len(hook_collector.on_before_move_called) == 1
        assert hook_collector.on_before_move_called[0] == (player_id, 1, 0)
        assert len(hook_collector.on_after_move_called) == 1
        assert hook_collector.on_after_move_called[0] == (player_id, 1, 0)

    def test_handle_message_leave_removes_entity(self, world):
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        player_id = resp.player_id

        leave_msg = Message(type=MsgType.LEAVE, player_id=player_id)
        world.handle_message(leave_msg)

        assert world.get_entity(player_id) is None

    def test_handle_message_leave_calls_on_player_leave(self, world, hook_collector):
        world.register_system(hook_collector)
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        player_id = resp.player_id

        hook_collector.on_player_leave_called.clear()
        leave_msg = Message(type=MsgType.LEAVE, player_id=player_id)
        world.handle_message(leave_msg)

        assert len(hook_collector.on_player_leave_called) == 1
        assert hook_collector.on_player_leave_called[0] == player_id

    def test_on_before_move_false_blocks_move(self, world, hook_collector):
        hook_collector.set_block_move(True)
        world.register_system(hook_collector)
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        player_id = list(resp.payload["players"].keys())[0]

        entity = world.get_entity(player_id)
        initial_x = entity.get_component(PositionComponent).x

        move_msg = Message(type=MsgType.MOVE, player_id=player_id, payload={"dx": 5, "dy": 0})
        world.handle_message(move_msg)

        new_x = entity.get_component(PositionComponent).x
        assert new_x == initial_x

    def test_get_state_snapshot_structure(self, world):
        join_msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(join_msg)
        player_id = list(world.entities.keys())[0]

        snap = world.get_state_snapshot()
        assert "seq" in snap
        assert "players" in snap
        assert player_id in snap["players"]
        assert "x" in snap["players"][player_id]
        assert "y" in snap["players"][player_id]

    def test_get_state_snapshot_with_map(self, world):
        join_msg = Message(type=MsgType.JOIN)
        world.handle_message(join_msg)

        snap = world.get_state_snapshot(include_map=True)
        assert "map" in snap
        assert "width" in snap["map"]
        assert "height" in snap["map"]
        assert "tiles" in snap["map"]

    def test_multiple_systems_called_in_registration_order(self, world):
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

    # Server-side tests (previously in test_server.py)
    def test_join_creates_player_returns_state_sync(self, world):
        msg = Message(type=MsgType.JOIN)
        resp = world.handle_message(msg)
        assert resp is not None
        assert resp.type == MsgType.STATE_SYNC
        assert resp.player_id in world.entities

    def test_move_updates_position_returns_state_sync(self, world):
        e = Entity("p1")
        spawn_x = (world.map_width // 2) * world.chunks.tile_size
        spawn_y = (world.map_height // 2) * world.chunks.tile_size
        e.add_component(PositionComponent(x=spawn_x, y=spawn_y))
        world.add_entity(e)
        old_x = spawn_x
        msg = Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 2, "dy": 0})
        resp = world.handle_message(msg)
        assert resp is not None
        assert resp.type == MsgType.STATE_SYNC
        assert e.get_component(PositionComponent).x == old_x + 2 * world.chunks.tile_size

    def test_leave_removes_player(self, world):
        e = Entity("p1")
        e.add_component(PositionComponent(x=2, y=2))
        world.add_entity(e)
        msg = Message(type=MsgType.LEAVE, player_id="p1")
        resp = world.handle_message(msg)
        assert resp is None
        assert "p1" not in world.entities

    def test_move_unknown_player_returns_state_sync(self, world):
        msg = Message(type=MsgType.MOVE, player_id="unknown", payload={"dx": 1, "dy": 0})
        resp = world.handle_message(msg)
        assert resp is not None
        assert resp.type == MsgType.STATE_SYNC

    def test_position_component_large_coords(self):
        from server.ecs.component import PositionComponent
        pos = PositionComponent(x=5000, y=3000)
        assert isinstance(pos.x, int) or isinstance(pos.x, float)
        assert pos.x == 5000
        assert pos.y == 3000

    def test_game_world_uses_chunk_manager(self):
        """GameWorld should use ChunkManager for collision, not GameMap."""
        from server.ecs.chunk import ChunkManager
        world = GameWorld()
        assert hasattr(world, 'chunks')
        assert isinstance(world.chunks, ChunkManager)

    def test_handle_message_move_uses_tile_coords_dxdy(self):
        """MOVE with dx=1, tile_size=16 should move entity by 16 world units."""
        world = GameWorld()
        from server.ecs.entity import Entity
        from server.ecs.component import PositionComponent
        tile_x, tile_y = 10, 5
        tile_size = world.chunks.tile_size
        e = Entity("p1")
        e.add_component(PositionComponent(x=tile_x * tile_size, y=tile_y * tile_size))
        world.add_entity(e)

        old_x = e.get_component(PositionComponent).x
        move_msg = Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 1, "dy": 0})
        world.handle_message(move_msg)

        new_x = e.get_component(PositionComponent).x
        assert new_x == old_x + tile_size
