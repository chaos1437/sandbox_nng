# server/ecs/chunk.py
"""Chunked world storage — tiles organized into 16x16 chunks keyed by world coords."""
from server.ecs.map import TILE_EMPTY, TILE_WALL


class Chunk:
    def __init__(self, cx: int, cy: int, tiles_per_side: int, tile_size: int) -> None:
        self.cx = cx
        self.cy = cy
        self.tiles_per_side = tiles_per_side
        self.tile_size = tile_size
        # tiles[y][x] — row-major, y is vertical
        self.tiles = [[TILE_EMPTY for _ in range(tiles_per_side)] for _ in range(tiles_per_side)]

    def _world_to_tile(self, world_x: int, world_y: int) -> tuple[int, int]:
        """World coords (pixels) → tile coords within this chunk."""
        return (world_x // self.tile_size, world_y // self.tile_size)

    def is_wall(self, world_x: int, world_y: int) -> bool:
        """Return True if world coord (x,y) lands on a wall tile."""
        tx, ty = self._world_to_tile(world_x, world_y)
        if tx < 0 or ty < 0 or tx >= self.tiles_per_side or ty >= self.tiles_per_side:
            return False
        return self.tiles[ty][tx] == TILE_WALL

    def set_wall(self, world_x: int, world_y: int) -> None:
        """Mark tile at world coord as wall."""
        tx, ty = self._world_to_tile(world_x, world_y)
        if 0 <= tx < self.tiles_per_side and 0 <= ty < self.tiles_per_side:
            self.tiles[ty][tx] = TILE_WALL

    def to_lines(self) -> list[list[str]]:
        return [row[:] for row in self.tiles]


class ChunkManager:
    def __init__(self, tiles_per_chunk: int = 16, tile_size: int = 16) -> None:
        self.tiles_per_chunk = tiles_per_chunk
        self.tile_size = tile_size
        self._chunks: dict[tuple[int, int], Chunk] = {}

    def _chunk_key_for_world(self, world_x: int, world_y: int) -> tuple[int, int]:
        """World pixel coords → chunk key (cx, cy)."""
        tile_x = world_x // self.tile_size
        tile_y = world_y // self.tile_size
        return (tile_x // self.tiles_per_chunk, tile_y // self.tiles_per_chunk)

    def get_chunk(self, cx: int, cy: int) -> Chunk:
        key = (cx, cy)
        if key not in self._chunks:
            self._chunks[key] = Chunk(cx, cy, self.tiles_per_chunk, self.tile_size)
        return self._chunks[key]

    def is_passable(self, world_x: int, world_y: int) -> bool:
        """Return True if world pixel coord is not inside a wall tile."""
        if world_x < 0 or world_y < 0:
            return False
        cx, cy = self._chunk_key_for_world(world_x, world_y)
        chunk = self._chunks.get((cx, cy))
        if chunk is None:
            return True  # unloaded chunk = no walls = passable
        return not chunk.is_wall(world_x, world_y)
