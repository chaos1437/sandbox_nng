# tests/test_services/test_move.py
import pytest
import time
from server.services.move import MoveService
from server.services.join import JoinService
from server.state.world import GameWorldState
from shared.protocol import Message
from shared.constants import MsgType


class TestMoveService:
    def setup_method(self):
        GameWorldState.reset()
        self._player_id = None

    def _join_player(self) -> str:
        resp = JoinService().handle(Message(type=MsgType.JOIN, player_id=""))
        self._player_id = resp.player_id
        return self._player_id

    # ── Basic movement ───────────────────────────────────────────

    def test_move_updates_position(self):
        pid = self._join_player()
        svc = MoveService(max_speed_tiles_per_sec=10.0)

        svc.handle(
            Message(type=MsgType.MOVE, player_id=pid, payload={"dx": 1, "dy": 0})
        )

        world = GameWorldState.get_instance()
        assert world.get_player(pid).x == world.width // 2 + 1

    def test_move_invalidates_on_wall(self):
        pid = self._join_player()
        world = GameWorldState.get_instance()
        wall_x = world.width // 2 + 1
        wall_y = world.height // 2
        world.set_wall(wall_x, wall_y)

        svc = MoveService(max_speed_tiles_per_sec=10.0)
        svc.handle(
            Message(type=MsgType.MOVE, player_id=pid, payload={"dx": 1, "dy": 0})
        )

        assert world.get_player(pid).x == world.width // 2

    def test_move_ignores_invalid_types(self):
        pid = self._join_player()
        svc = MoveService(max_speed_tiles_per_sec=10.0)

        result = svc.handle(
            Message(type=MsgType.MOVE, player_id=pid, payload={"dx": "bad", "dy": 0})
        )
        assert result.type == MsgType.STATE_SYNC

    def test_move_unknown_player_returns_sync(self):
        svc = MoveService(max_speed_tiles_per_sec=10.0)
        result = svc.handle(
            Message(type=MsgType.MOVE, player_id="ghost", payload={"dx": 1, "dy": 0})
        )
        assert result.type == MsgType.STATE_SYNC

    # ── Rate limiting ───────────────────────────────────────────

    def test_rate_limit_allows_fast_enough_moves(self):
        pid = self._join_player()
        world = GameWorldState.get_instance()
        center_x = world.width // 2

        svc = MoveService(max_speed_tiles_per_sec=10.0)

        svc.handle(
            Message(type=MsgType.MOVE, player_id=pid, payload={"dx": 1, "dy": 0})
        )
        assert world.get_player(pid).x == center_x + 1

    def test_rate_limit_blocks_too_fast(self):
        pid = self._join_player()
        world = GameWorldState.get_instance()
        center_x = world.width // 2

        svc = MoveService(max_speed_tiles_per_sec=10.0)

        svc.handle(
            Message(type=MsgType.MOVE, player_id=pid, payload={"dx": 1, "dy": 0})
        )

        svc.handle(
            Message(type=MsgType.MOVE, player_id=pid, payload={"dx": 1, "dy": 0})
        )

        assert world.get_player(pid).x == center_x + 1

    def test_rate_limit_violations_tracked(self):
        pid = self._join_player()
        svc = MoveService(max_speed_tiles_per_sec=10.0)

        svc.handle(
            Message(type=MsgType.MOVE, player_id=pid, payload={"dx": 1, "dy": 0})
        )
        svc.handle(
            Message(type=MsgType.MOVE, player_id=pid, payload={"dx": 1, "dy": 0})
        )

        world = GameWorldState.get_instance()
        assert world.get_player(pid).violations == 1

    def test_rate_limit_zero_speed_blocks_all(self):
        pid = self._join_player()
        svc = MoveService(max_speed_tiles_per_sec=0.0)

        svc.handle(
            Message(type=MsgType.MOVE, player_id=pid, payload={"dx": 1, "dy": 0})
        )

        world = GameWorldState.get_instance()
        assert world.get_player(pid).violations == 1

    def test_rate_limit_updates_total_moves(self):
        pid = self._join_player()
        svc = MoveService(max_speed_tiles_per_sec=10.0)

        svc.handle(
            Message(type=MsgType.MOVE, player_id=pid, payload={"dx": 1, "dy": 0})
        )

        world = GameWorldState.get_instance()
        assert world.get_player(pid).total_moves == 1