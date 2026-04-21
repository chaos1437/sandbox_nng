# tests/conftest.py
import pytest
from server.state.world import GameWorldState


@pytest.fixture
def world():
    """Fresh GameWorldState instance."""
    GameWorldState.reset()
    return GameWorldState.get_instance()


@pytest.fixture
def hook_collector():
    """HookCollector for verifying system hooks."""
    return HookCollector()


class HookCollector:
    def __init__(self):
        self.calls = []

    def record(self, event: str, *args):
        self.calls.append((event, args))
