from dataclasses import dataclass, field
from typing import Optional

from shared.constants import TILE_EMPTY, TILE_WALL

CHUNK_SIZE = 32


@dataclass
class Chunk:
    cx: int
    cy: int
    tiles: list[list[str]] = field(
        default_factory=lambda: [
            [TILE_EMPTY for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)
        ]
    )
    dirty: bool = False

    def get_tile(self, lx: int, ly: int) -> Optional[str]:
        if not (0 <= lx < CHUNK_SIZE and 0 <= ly < CHUNK_SIZE):
            return None
        return self.tiles[ly][lx]

    def set_tile(self, lx: int, ly: int, tile: str) -> bool:
        if not (0 <= lx < CHUNK_SIZE and 0 <= ly < CHUNK_SIZE):
            return False
        self.tiles[ly][lx] = tile
        self.dirty = True
        return True

    def to_dict(self) -> dict:
        return {
            "cx": self.cx,
            "cy": self.cy,
            "tiles": self.tiles,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        return cls(
            cx=data["cx"],
            cy=data["cy"],
            tiles=data["tiles"],
            dirty=False,
        )


def generate_chunk(cx: int, cy: int, seed: int) -> Chunk:
    tiles = [[TILE_EMPTY for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)]
    return Chunk(cx=cx, cy=cy, tiles=tiles, dirty=False)
