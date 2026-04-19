# tests/test_movement_controller.py
import pytest
from server.ecs.systems.movement_controller import MovementController


class TestMovementController:
    def test_rate_limits_correctly(self, movement_controller, world):
        player_id = "p1"

        result = movement_controller.on_before_move(world, player_id, 1, 0)
        assert result is True

        result = movement_controller.on_before_move(world, player_id, 1, 0)
        assert result is False

    def test_records_violations(self, movement_controller, world):
        player_id = "p1"

        movement_controller.on_before_move(world, player_id, 1, 0)
        movement_controller.on_before_move(world, player_id, 1, 0)

        stats = movement_controller.get_stats(player_id)
        assert stats["violations"] == 1
        assert stats["total_moves"] == 1

    def test_cleans_up_on_player_leave(self, movement_controller, world):
        player_id = "p1"

        movement_controller.on_before_move(world, player_id, 1, 0)
        assert movement_controller.get_stats(player_id)["total_moves"] == 1

        movement_controller.on_player_leave(world, player_id)

        stats = movement_controller.get_stats(player_id)
        assert stats["total_moves"] == 0
        assert stats["violations"] == 0
