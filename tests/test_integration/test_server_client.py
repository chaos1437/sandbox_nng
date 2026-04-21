# tests/test_integration/test_server_client.py
"""Integration tests for server-client connection.

These tests verify the game world state and services work correctly
with the chunk-based streaming system.
"""

import pytest
from server.state.world import GameWorldState
from server.services.join import JoinService
from server.services.move import MoveService
from shared.protocol import Message
from shared.constants import MsgType


@pytest.fixture(autouse=True)
def reset_world():
    GameWorldState.reset()
    yield
    GameWorldState.reset()


class TestGameWorldChunkStreaming:
    """Test chunk-based world streaming."""

    def test_world_has_fov_manager(self):
        world = GameWorldState.get_instance()
        assert hasattr(world, "fov_manager")
        assert world.fov_manager is not None

    def test_join_returns_full_chunks(self):
        world = GameWorldState.get_instance()
        svc = JoinService()

        resp = svc.handle(Message(type=MsgType.JOIN, player_id="test_player"))

        assert resp.type == MsgType.STATE_SYNC
        assert "full_chunks" in resp.payload
        assert "deltas" in resp.payload
        assert len(resp.payload["full_chunks"]) > 0

    def test_join_returns_chunk_with_tiles(self):
        world = GameWorldState.get_instance()
        svc = JoinService()

        resp = svc.handle(Message(type=MsgType.JOIN, player_id="p1"))

        full_chunks = resp.payload["full_chunks"]
        assert len(full_chunks) > 0
        chunk = full_chunks[0]
        assert "cx" in chunk
        assert "cy" in chunk
        assert "tiles" in chunk
        assert len(chunk["tiles"]) == 32
        assert len(chunk["tiles"][0]) == 32

    def test_join_returns_deltas_array(self):
        world = GameWorldState.get_instance()
        svc = JoinService()

        resp = svc.handle(Message(type=MsgType.JOIN, player_id="p1"))

        deltas = resp.payload["deltas"]
        assert isinstance(deltas, list)
        if deltas:
            assert len(deltas[0]) == 3  # [x, y, tile]

    def test_player_in_world_after_join(self):
        world = GameWorldState.get_instance()
        svc = JoinService()

        resp = svc.handle(Message(type=MsgType.JOIN, player_id="p1"))

        player = world.get_player("p1")
        assert player is not None
        assert player.x == world.width // 2
        assert player.y == world.height // 2

    def test_move_returns_move_near_type(self):
        world = GameWorldState.get_instance()
        JoinService().handle(Message(type=MsgType.JOIN, player_id="p1"))

        svc = MoveService(max_speed_tiles_per_sec=100.0)
        resp = svc.handle(
            Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 1, "dy": 0})
        )

        assert resp.type == MsgType.MOVE_NEAR
        assert resp.payload["mover_id"] == "p1"

    def test_player_view_for_known_player(self):
        world = GameWorldState.get_instance()
        JoinService().handle(Message(type=MsgType.JOIN, player_id="p1"))

        view = world.get_player_view("p1")

        assert "full_chunks" in view
        assert "deltas" in view
        assert "players" in view
        assert "p1" in view["players"]

    def test_player_view_for_unknown_player(self):
        world = GameWorldState.get_instance()

        view = world.get_player_view("ghost")

        assert view["full_chunks"] == []
        assert view["deltas"] == []
