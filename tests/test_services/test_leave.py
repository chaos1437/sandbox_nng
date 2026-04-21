# tests/test_services/test_leave.py
import pytest
from server.services.leave import LeaveService
from server.services.join import JoinService
from server.state.world import GameWorldState
from shared.protocol import Message
from shared.constants import MsgType


class TestLeaveService:
    def setup_method(self):
        GameWorldState.reset()

    def test_leave_removes_player(self):
        join_svc = JoinService()
        leave_svc = LeaveService()

        join_svc.handle(Message(type=MsgType.JOIN, player_id="p1"))
        world = GameWorldState.get_instance()
        assert world.get_player("p1") is not None

        leave_svc.handle(Message(type=MsgType.LEAVE, player_id="p1"))
        assert world.get_player("p1") is None

    def test_leave_increments_seq(self):
        join_svc = JoinService()
        leave_svc = LeaveService()

        r1 = join_svc.handle(Message(type=MsgType.JOIN, player_id="p1"))
        r2 = leave_svc.handle(Message(type=MsgType.LEAVE, player_id="p1"))
        assert r2.payload["seq"] == r1.payload["seq"] + 1

    def test_leave_unknown_player_is_noop(self):
        leave_svc = LeaveService()
        result = leave_svc.handle(Message(type=MsgType.LEAVE, player_id="ghost"))
        assert result is not None
        assert result.type == MsgType.STATE_SYNC
