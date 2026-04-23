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

    def test_join_places_player_at_center(self):
        svc = JoinService()
        result = svc.handle(Message(type=MsgType.JOIN, player_id=""))
        pid = result.player_id
        world = GameWorldState.get_instance()
        p = world.get_player(pid)
        assert p is not None
        assert p.x == world.width // 2
        assert p.y == world.height // 2

    def test_join_includes_full_chunks_in_first_response(self):
        svc = JoinService()
        result = svc.handle(Message(type=MsgType.JOIN, player_id=""))
        assert "full_chunks" in result.payload
        assert len(result.payload["full_chunks"]) > 0
        assert "deltas" in result.payload
        assert isinstance(result.payload["deltas"], list)

    def test_join_increments_seq(self):
        svc = JoinService()
        result1 = svc.handle(Message(type=MsgType.JOIN, player_id=""))
        result2 = svc.handle(Message(type=MsgType.JOIN, player_id=""))
        assert result2.seq == result1.seq + 1
