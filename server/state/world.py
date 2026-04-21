from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from server.state.models import Player, ChatMessage

if TYPE_CHECKING:
    from shared.constants import TILE_WALL, TILE_EMPTY

__all__ = ["GameWorldState", "get_world"]


class GameWorldState:
    """Singleton game state — players, map, chat.

    Single instance via get_world(), resettable for testing.
    Supports extension hooks (plugin-like pattern for future features).
    """

    _instance: Optional["GameWorldState"] = None

    def __init__(self, width: int = 40, height: int = 20):
        self.width = width
        self.height = height
        self.cells: list[list[bool]] = [
            [False for _ in range(width)] for _ in range(height)
        ]
        self.players: dict[str, Player] = {}
        self.chat_messages: list[ChatMessage] = []
        self.seq: int = 0

    @classmethod
    def get_instance(cls) -> "GameWorldState":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton — for testing."""
        cls._instance = None

    def add_player(self, player: Player) -> None:
        self.players[player.id] = player

    def remove_player(self, player_id: str) -> None:
        self.players.pop(player_id, None)

    def get_player(self, player_id: str) -> Optional[Player]:
        return self.players.get(player_id)

    def set_wall(self, cell_x: int, cell_y: int) -> None:
        if 0 <= cell_x < self.width and 0 <= cell_y < self.height:
            self.cells[cell_y][cell_x] = True

    def is_passable(self, cell_x: int, cell_y: int) -> bool:
        if not (0 <= cell_x < self.width and 0 <= cell_y < self.height):
            return False
        return not self.cells[cell_y][cell_x]

    def add_chat_message(self, msg: ChatMessage, max_lines: int = 5) -> None:
        self.chat_messages.append(msg)
        if len(self.chat_messages) > max_lines:
            self.chat_messages = self.chat_messages[-max_lines:]

    def get_state_snapshot(self, include_map: bool = False) -> dict:
        snap = {
            "seq": self.seq,
            "players": {pid: {"x": p.x, "y": p.y} for pid, p in self.players.items()},
        }
        if include_map:
            snap["map"] = {
                "width": self.width,
                "height": self.height,
                "tiles": self._grid_to_strings(),
            }
        if self.chat_messages:
            snap["chat"] = [
                {"player_id": m.player_id, "text": m.text} for m in self.chat_messages
            ]
        return snap

    def _grid_to_strings(self) -> list[list[str]]:
        from shared.constants import TILE_WALL, TILE_EMPTY

        result = []
        for row in self.cells:
            result.append([TILE_WALL if cell else TILE_EMPTY for cell in row])
        return result


def get_world() -> GameWorldState:
    return GameWorldState.get_instance()
