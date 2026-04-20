# tests/test_chunk.py
import pytest
from server.ecs.chunk import ChunkManager, Chunk

TILE_SIZE = 16


class TestChunk:
    def test_chunk_creation(self):
        chunk = Chunk(cx=0, cy=0, size=16, tile_size=16)
        assert chunk.cx == 0
        assert chunk.cy == 0
        assert chunk.size == 16

    def test_set_and_is_wall(self):
        chunk = Chunk(cx=0, cy=0, size=16, tile_size=16)
        # set wall at world tile (5, 5) = world coord (5*TILE_SIZE, 5*TILE_SIZE)
        world_x = 5 * TILE_SIZE
        world_y = 5 * TILE_SIZE
        chunk.set_wall(world_x, world_y)
        assert chunk.is_wall(world_x, world_y) is True
        # different tile
        assert chunk.is_wall(4 * TILE_SIZE, 5 * TILE_SIZE) is False


class TestChunkManager:
    def test_get_or_create_chunk(self):
        cm = ChunkManager(tiles_per_chunk=16, tile_size=16)
        chunk = cm.get_chunk(0, 0)
        assert chunk is not None
        assert chunk.cx == 0
        assert chunk.cy == 0

    def test_same_chunkreturned(self):
        cm = ChunkManager(tiles_per_chunk=16, tile_size=16)
        c1 = cm.get_chunk(0, 0)
        c2 = cm.get_chunk(0, 0)
        assert c1 is c2  # same lazy instance

    def test_is_passable_empty(self):
        cm = ChunkManager(tiles_per_chunk=16, tile_size=16)
        assert cm.is_passable(0, 0) is True
        assert cm.is_passable(100, 100) is True  # unloaded chunk = passable

    def test_is_passable_wall(self):
        cm = ChunkManager(tiles_per_chunk=16, tile_size=16)
        wall_x = 5 * TILE_SIZE
        wall_y = 5 * TILE_SIZE
        chunk = cm.get_chunk(0, 0)
        chunk.set_wall(wall_x, wall_y)
        # wall tile is impassable
        assert cm.is_passable(wall_x, wall_y) is False
        # adjacent tile is passable
        assert cm.is_passable((5 - 1) * TILE_SIZE, wall_y) is True

    def test_is_passable_out_of_range_negative(self):
        cm = ChunkManager(tiles_per_chunk=16, tile_size=16)
        assert cm.is_passable(-1, -1) is False  # out of world bounds
