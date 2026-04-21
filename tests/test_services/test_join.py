# tests/test_services/test_join.py
import pytest
from server.services.join import JoinService
from server.state.world import GameWorldState
from shared.protocol import Message
from shared.constants import MsgType


class TestJoinService:
    def setup_method(self):
        GameWorldState.reset()

    def test_join_generates_player_id(self):
        svc = JoinService()
        result = svc.handle(Message(type=MsgType.JOIN, player_id=""))
        assert result.type == MsgType.STATE_SYNC
        assert result.player_id != ""
        assert len(result.player_id) == 8  # short ID

    def test_join_uses_suggested_id(self):
        svc = JoinService()
        result = svc.handle(Message(type=MsgType.JOIN, player_id="myplayer"))
        assert result.player_id == "myplayer"

    def test_join_places_player_at_center(self):
        svc = JoinService()
        result = svc.handle(Message(type=MsgType.JOIN, player_id="p1"))
        world = GameWorldState.get_instance()
        p = world.get_player("p1")
        assert p is not None
        assert p.x == world.width // 2
        assert p.y == world.height // 2

    def test_join_includes_map_in_first_response(self):
        svc = JoinService()
        result = svc.handle(Message(type=MsgType.JOIN, player_id="p1"))
        assert "map" in result.payload
        assert "chunk_size" in result.payload["map"]
        assert "world_cx" in result.payload["map"]
        assert "world_cy" in result.payload["map"]

    def test_join_increments_seq(self):
        svc = JoinService()
        result1 = svc.handle(Message(type=MsgType.JOIN, player_id="p1"))
        result2 = svc.handle(Message(type=MsgType.JOIN, player_id="p2"))
        assert result2.payload["seq"] == 2
