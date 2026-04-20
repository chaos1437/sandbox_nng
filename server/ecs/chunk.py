# server/ecs/chunk.py
"""Chunked world storage — tiles organized into 16x16 chunks keyed by world coords."""
from server.ecs.map import TILE_EMPTY, TILE_WALL


class Chunk:
    def __init__(self, cx: int, cy: int, size: int, tile_size: int):
        self.cx = cx
        self.cy = cy
        self.size = size
        self.tile_size = tile_size
        # tiles[y][x] — row-major, y is vertical
        self.tiles = [[TILE_EMPTY for _ in range(size)] for _ in range(size)]

    def _local_tile(self, world_x: int, world_y: int) -> tuple[int, int]:
        """Convert world coords to local tile coords within this chunk."""
        return (world_x // self.tile_size, world_y // self.tile_size)

    def is_wall(self, world_x: int, world_y: int) -> bool:
        tx, ty = self._local_tile(world_x, world_y)
        if tx < 0 or ty < 0 or tx >= self.size or ty >= self.size:
            return False
        return self.tiles[ty][tx] == TILE_WALL

    def set_wall(self, world_x: int, world_y: int):
        tx, ty = self._local_tile(world_x, world_y)
        if 0 <= tx < self.size and 0 <= ty < self.size:
            self.tiles[ty][tx] = TILE_WALL

    def to_lines(self) -> list[list[str]]:
        """Return a deep copy of the tile grid."""
        return [row[:] for row in self.tiles]


class ChunkManager:
    def __init__(self, tiles_per_chunk: int = 16, tile_size: int = 16):
        self.tiles_per_chunk = tiles_per_chunk
        self.tile_size = tile_size
        self._chunks: dict[tuple[int, int], Chunk] = {}

    def _chunk_key(self, world_x: int, world_y: int) -> tuple[int, int]:
        """Return the chunk key (cx, cy) for given world coords."""
        tx = world_x // self.tile_size
        ty = world_y // self.tile_size
        return (tx // self.tiles_per_chunk, ty // self.tiles_per_chunk)

    def get_chunk(self, cx: int, cy: int) -> Chunk:
        """Get or create a chunk at chunk coords (cx, cy)."""
        key = (cx, cy)
        if key not in self._chunks:
            self._chunks[key] = Chunk(cx, cy, self.tiles_per_chunk, self.tile_size)
        return self._chunks[key]

    def is_passable(self, x: int, y: int) -> bool:
        """Return True if world coord (x, y) is not inside a wall tile."""
        if x < 0 or y < 0:
            return False
        cx, cy = self._chunk_key(x, y)
        chunk = self._chunks.get((cx, cy))
        if chunk is None:
            return True  # unloaded chunk = no walls yet = passable
        return not chunk.is_wall(x, y)


TILE_SIZE = 16  # default, use ChunkManager.tile_size for actual value
