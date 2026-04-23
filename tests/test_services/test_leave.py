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

        r = join_svc.handle(Message(type=MsgType.JOIN, player_id=""))
        pid = r.player_id
        world = GameWorldState.get_instance()
        assert world.get_player(pid) is not None

        leave_svc.handle(Message(type=MsgType.LEAVE, player_id=pid))
        assert world.get_player(pid) is None

    def test_leave_increments_seq(self):
        join_svc = JoinService()
        leave_svc = LeaveService()

        r1 = join_svc.handle(Message(type=MsgType.JOIN, player_id=""))
        pid = r1.player_id
        r2 = leave_svc.handle(Message(type=MsgType.LEAVE, player_id=pid))
        assert r2.seq == r1.seq + 1

    def test_leave_unknown_player_is_noop(self):
        leave_svc = LeaveService()
        result = leave_svc.handle(Message(type=MsgType.LEAVE, player_id="ghost"))
        assert result is not None
        assert result.type == MsgType.STATE_SYNC
