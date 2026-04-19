# tests/conftest.py
import pytest
from server.ecs.game_world import GameWorld
from server.ecs.entity import Entity
from server.ecs.component import PositionComponent
from server.ecs.systems.movement_controller import MovementController


@pytest.fixture
def world():
    """Fresh GameWorld instance."""
    return GameWorld()


@pytest.fixture
def entity():
    """Factory for Entity with optional PositionComponent."""
    def _make(entity_id: str, x: int = 0, y: int = 0) -> Entity:
        e = Entity(entity_id)
        e.add_component(PositionComponent(x=x, y=y))
        return e
    return _make


@pytest.fixture
def movement_controller():
    """MovementController with reasonable defaults."""
    return MovementController(max_speed_tiles_per_sec=10.0)


# Test system for hook verification — use via HookCollector fixture
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


@pytest.fixture
def hook_collector():
    """HookCollector for verifying system hooks."""
    return HookCollector()
