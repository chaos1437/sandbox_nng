# tests/test_chunk.py
import pytest
from server.ecs.chunk import ChunkManager, Chunk

TILE_SIZE = 16


class TestChunk:
    def test_chunk_creation(self):
        chunk = Chunk(cx=0, cy=0, tiles_per_side=16, tile_size=16)
        assert chunk.cx == 0
        assert chunk.cy == 0
        assert chunk.tiles_per_side == 16

    def test_set_and_is_wall(self):
        chunk = Chunk(cx=0, cy=0, tiles_per_side=16, tile_size=16)
        # tile (5, 5) → world pixel (80, 80)
        chunk.set_wall(5 * TILE_SIZE, 5 * TILE_SIZE)
        assert chunk.is_wall(5 * TILE_SIZE, 5 * TILE_SIZE) is True
        # different tile
        assert chunk.is_wall(4 * TILE_SIZE, 5 * TILE_SIZE) is False


class TestChunkManager:
    def test_get_or_create_chunk(self):
        manager = ChunkManager(tiles_per_chunk=16, tile_size=16)
        chunk = manager.get_chunk(0, 0)
        assert chunk is not None
        assert chunk.cx == 0
        assert chunk.cy == 0

    def test_same_chunk_returned(self):
        manager = ChunkManager(tiles_per_chunk=16, tile_size=16)
        c1 = manager.get_chunk(0, 0)
        c2 = manager.get_chunk(0, 0)
        assert c1 is c2

    def test_is_passable_empty(self):
        manager = ChunkManager(tiles_per_chunk=16, tile_size=16)
        assert manager.is_passable(0, 0) is True
        assert manager.is_passable(100, 100) is True

    def test_is_passable_wall(self):
        manager = ChunkManager(tiles_per_chunk=16, tile_size=16)
        wall_pixel_x = 5 * TILE_SIZE
        wall_pixel_y = 5 * TILE_SIZE
        manager.get_chunk(0, 0).set_wall(wall_pixel_x, wall_pixel_y)
        # wall tile is impassable
        assert manager.is_passable(wall_pixel_x, wall_pixel_y) is False
        # adjacent tile is passable
        assert manager.is_passable((5 - 1) * TILE_SIZE, wall_pixel_y) is True

    def test_is_passable_out_of_range_negative(self):
        manager = ChunkManager(tiles_per_chunk=16, tile_size=16)
        assert manager.is_passable(-1, -1) is False
