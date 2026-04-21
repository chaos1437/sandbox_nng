from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from server.state.models import Player, ChatMessage
from server.state.fov_manager import FOVManager

if TYPE_CHECKING:
    from server.state.chunk_manager import ChunkManager

__all__ = ["GameWorldState", "get_world"]


class GameWorldState:
    """Singleton game state — players, map (chunk-based), chat.

    Single instance via get_world(), resettable for testing.
    """

    _instance: Optional["GameWorldState"] = None

    def __init__(
        self,
        world_name: str = "default",
        world_dir: str = "./server/worlds",
        world_cx: int = 16,
        world_cy: int = 16,
        chunk_size: int = 32,
        cache_size: int = 64,
        seed: int = 42,
        fov_radius: int = 1,
    ):
        from server.state.chunk_manager import ChunkManager

        self.world_name = world_name
        self.chunk_manager = ChunkManager(
            world_name=world_name,
            world_dir=world_dir,
            world_cx=world_cx,
            world_cy=world_cy,
            chunk_size=chunk_size,
            cache_size=cache_size,
            seed=seed,
        )
        self.players: dict[str, Player] = {}
        self.chat_messages: list[ChatMessage] = []
        self.seq: int = 0
        self.fov_manager = FOVManager(chunk_radius=fov_radius)

    @classmethod
    def get_instance(cls) -> "GameWorldState":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    def add_player(self, player: Player) -> None:
        self.players[player.id] = player

    def remove_player(self, player_id: str) -> None:
        self.players.pop(player_id, None)

    def get_player(self, player_id: str) -> Optional[Player]:
        return self.players.get(player_id)

    def set_wall(self, cell_x: int, cell_y: int) -> bool:
        cx, cy, lx, ly = self.chunk_manager.world_to_chunk(cell_x, cell_y)
        chunk = self.chunk_manager.get_chunk(cx, cy)
        if chunk is None:
            return False
        from shared.constants import TILE_WALL

        return chunk.set_tile(lx, ly, TILE_WALL)

    def is_passable(self, cell_x: int, cell_y: int) -> bool:
        cx, cy, lx, ly = self.chunk_manager.world_to_chunk(cell_x, cell_y)
        chunk = self.chunk_manager.get_chunk(cx, cy)
        if chunk is None:
            return False
        tile = chunk.get_tile(lx, ly)
        if tile is None:
            return False
        from shared.constants import TILE_EMPTY

        return tile == TILE_EMPTY

    def add_chat_message(self, msg: ChatMessage, max_lines: int = 5) -> None:
        self.chat_messages.append(msg)
        if len(self.chat_messages) > max_lines:
            self.chat_messages = self.chat_messages[-max_lines:]

    def flush(self):
        self.chunk_manager.flush()

    @property
    def width(self) -> int:
        return self.chunk_manager.chunk_size * self.chunk_manager.world_cx

    @property
    def height(self) -> int:
        return self.chunk_manager.chunk_size * self.chunk_manager.world_cy

    def get_state_snapshot(self, include_map: bool = False) -> dict:
        snap = {
            "seq": self.seq,
            "players": {pid: {"x": p.x, "y": p.y} for pid, p in self.players.items()},
        }
        if include_map:
            snap["map"] = {
                "chunk_size": self.chunk_manager.chunk_size,
                "world_cx": self.chunk_manager.world_cx,
                "world_cy": self.chunk_manager.world_cy,
                "tiles": self._get_center_chunk_tiles(),
            }
        if self.chat_messages:
            snap["chat"] = [
                {"player_id": m.player_id, "text": m.text} for m in self.chat_messages
            ]
        return snap

    def get_player_view(self, player_id: str) -> dict:
        player = self.players.get(player_id)
        if player is None:
            return {
                "seq": self.seq,
                "players": {},
                "full_chunks": [],
                "deltas": [],
            }
        fov_chunks = self.fov_manager.update_fov(player)
        full_chunks = []
        deltas = []
        for cx, cy in fov_chunks:
            chunk = self.chunk_manager.get_chunk(cx, cy)
            if chunk is None:
                continue
            full_chunks.append({"cx": cx, "cy": cy, "tiles": chunk.tiles})
            for ly in range(len(chunk.tiles)):
                for lx in range(len(chunk.tiles[ly])):
                    wx = cx * self.chunk_manager.chunk_size + lx
                    wy = cy * self.chunk_manager.chunk_size + ly
                    deltas.append([wx, wy, chunk.tiles[ly][lx]])
        return {
            "seq": self.seq,
            "players": {pid: {"x": p.x, "y": p.y} for pid, p in self.players.items()},
            "full_chunks": full_chunks,
            "deltas": deltas,
        }

    def _get_center_chunk_tiles(self):
        cx = self.chunk_manager.world_cx // 2
        cy = self.chunk_manager.world_cy // 2
        chunk = self.chunk_manager.get_chunk(cx, cy)
        if chunk is None:
            return [
                ["." for _ in range(self.chunk_manager.chunk_size)]
                for _ in range(self.chunk_manager.chunk_size)
            ]
        return chunk.tiles


def get_world() -> GameWorldState:
    return GameWorldState.get_instance()
