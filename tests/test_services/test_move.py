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

    def _join_player(self, player_id: str = "p1") -> None:
        JoinService().handle(Message(type=MsgType.JOIN, player_id=player_id))

    # ── Basic movement ───────────────────────────────────────────

    def test_move_updates_position(self):
        self._join_player()
        svc = MoveService(max_speed_tiles_per_sec=10.0)

        result = svc.handle(
            Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 1, "dy": 0})
        )

        world = GameWorldState.get_instance()
        assert world.get_player("p1").x == world.width // 2 + 1

    def test_move_invalidates_on_wall(self):
        self._join_player()
        world = GameWorldState.get_instance()
        # Place wall to the right of starting position
        wall_x = world.width // 2 + 1
        wall_y = world.height // 2
        world.set_wall(wall_x, wall_y)

        svc = MoveService(max_speed_tiles_per_sec=10.0)
        result = svc.handle(
            Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 1, "dy": 0})
        )

        # Player should NOT have moved into wall
        assert world.get_player("p1").x == world.width // 2

    def test_move_ignores_invalid_types(self):
        self._join_player()
        svc = MoveService(max_speed_tiles_per_sec=10.0)

        result = svc.handle(
            Message(type=MsgType.MOVE, player_id="p1", payload={"dx": "bad", "dy": 0})
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
        self._join_player()
        # 10 tiles/sec = 0.1s min interval
        svc = MoveService(max_speed_tiles_per_sec=10.0)

        # First move should always succeed
        r1 = svc.handle(
            Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 1, "dy": 0})
        )
        assert r1.payload["players"]["p1"]["x"] == 20 + 1

    def test_rate_limit_blocks_too_fast(self):
        self._join_player()
        svc = MoveService(max_speed_tiles_per_sec=10.0)  # 0.1s min interval

        # First move
        svc.handle(
            Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 1, "dy": 0})
        )

        # Immediate second move — should be blocked
        r2 = svc.handle(
            Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 1, "dy": 0})
        )

        world = GameWorldState.get_instance()
        # Player should still be at x=21 (didn't move)
        assert world.get_player("p1").x == 21

    def test_rate_limit_violations_tracked(self):
        self._join_player()
        svc = MoveService(max_speed_tiles_per_sec=10.0)

        svc.handle(
            Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 1, "dy": 0})
        )
        svc.handle(
            Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 1, "dy": 0})
        )

        world = GameWorldState.get_instance()
        assert world.get_player("p1").violations == 1

    def test_rate_limit_zero_speed_blocks_all(self):
        self._join_player()
        svc = MoveService(max_speed_tiles_per_sec=0.0)

        svc.handle(
            Message(type=MsgType.MOVE, player_id="p1", payload={"dx": 1, "dy": 0})
        )

        world = GameWorldState.get_instance()
        assert world.get_player("p1").violations == 1
