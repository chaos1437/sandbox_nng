import pytest
from server.state.chunk import Chunk, generate_chunk, CHUNK_SIZE


class TestChunk:
    def test_chunk_creation(self):
        chunk = Chunk(cx=0, cy=0)
        assert chunk.cx == 0
        assert chunk.cy == 0
        assert len(chunk.tiles) == CHUNK_SIZE
        assert len(chunk.tiles[0]) == CHUNK_SIZE
        assert chunk.dirty is False

    def test_chunk_dirty_flag(self):
        chunk = Chunk(cx=5, cy=-3)
        assert chunk.dirty is False
        chunk.dirty = True
        assert chunk.dirty is True

    def test_chunk_tiles_all_empty(self):
        chunk = Chunk(cx=0, cy=0)
        from shared.constants import TILE_EMPTY

        for row in chunk.tiles:
            for tile in row:
                assert tile == TILE_EMPTY

    def test_chunk_set_tile(self):
        chunk = Chunk(cx=0, cy=0)
        from shared.constants import TILE_WALL

        chunk.set_tile(5, 10, TILE_WALL)
        assert chunk.get_tile(5, 10) == TILE_WALL
        assert chunk.dirty is True

    def test_chunk_set_tile_out_of_bounds(self):
        chunk = Chunk(cx=0, cy=0)
        from shared.constants import TILE_WALL

        result = chunk.set_tile(32, 0, TILE_WALL)
        assert result is False
        result = chunk.set_tile(0, 32, TILE_WALL)
        assert result is False

    def test_chunk_get_tile_out_of_bounds(self):
        chunk = Chunk(cx=0, cy=0)
        assert chunk.get_tile(-1, 0) is None
        assert chunk.get_tile(0, -1) is None
        assert chunk.get_tile(32, 32) is None

    def test_chunk_to_dict(self):
        chunk = Chunk(cx=1, cy=2)
        from shared.constants import TILE_WALL

        chunk.set_tile(3, 4, TILE_WALL)
        data = chunk.to_dict()
        assert data["cx"] == 1
        assert data["cy"] == 2
        assert data["tiles"][4][3] == TILE_WALL

    def test_chunk_from_dict(self):
        data = {
            "cx": 5,
            "cy": -1,
            "tiles": [["." for _ in range(CHUNK_SIZE)] for _ in range(CHUNK_SIZE)],
        }
        chunk = Chunk.from_dict(data)
        assert chunk.cx == 5
        assert chunk.cy == -1
        assert len(chunk.tiles) == CHUNK_SIZE


class TestGenerateChunk:
    def test_generate_chunk_returns_chunk(self):
        chunk = generate_chunk(0, 0, seed=12345)
        assert isinstance(chunk, Chunk)
        assert chunk.cx == 0
        assert chunk.cy == 0
        assert chunk.dirty is False

    def test_generate_chunk_same_seed_same_tiles(self):
        chunk1 = generate_chunk(1, 1, seed=999)
        chunk2 = generate_chunk(1, 1, seed=999)
        assert chunk1.tiles == chunk2.tiles

    def test_generate_chunk_all_passable(self):
        chunk = generate_chunk(0, 0, seed=42)
        from shared.constants import TILE_EMPTY

        for row in chunk.tiles:
            for tile in row:
                assert tile == TILE_EMPTY
