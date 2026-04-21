import json
import os
import tempfile
import shutil
from pathlib import Path

import pytest

from server.state.chunk import Chunk, generate_chunk, CHUNK_SIZE


class TestChunkManager:
    @pytest.fixture
    def temp_world_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def chunk_manager(self, temp_world_dir):
        from server.state.chunk_manager import ChunkManager

        return ChunkManager(world_name="test_world", world_dir=temp_world_dir)

    # ── get_chunk ──────────────────────────────────────────────────

    def test_get_chunk_generates_new(self, chunk_manager):
        chunk = chunk_manager.get_chunk(0, 0)
        assert isinstance(chunk, Chunk)
        assert chunk.cx == 0
        assert chunk.cy == 0

    def test_get_chunk_returns_cached(self, chunk_manager):
        chunk1 = chunk_manager.get_chunk(0, 0)
        chunk2 = chunk_manager.get_chunk(0, 0)
        assert chunk1 is chunk2

    def test_get_chunk_different_coordinates(self, chunk_manager):
        chunk1 = chunk_manager.get_chunk(0, 0)
        chunk2 = chunk_manager.get_chunk(1, 0)
        assert chunk1 is not chunk2
        assert chunk1.cx == 0
        assert chunk2.cx == 1

    # ── Cache size / LRU ───────────────────────────────────────────

    def test_cache_size_limit(self, temp_world_dir):
        from server.state.chunk_manager import ChunkManager

        cm = ChunkManager(
            world_name="test_world", world_dir=temp_world_dir, cache_size=3
        )
        chunk_manager = cm

        chunk_manager.get_chunk(0, 0)
        chunk_manager.get_chunk(1, 0)
        chunk_manager.get_chunk(2, 0)

        assert len(chunk_manager._cache) == 3

        chunk_manager.get_chunk(3, 0)
        assert len(chunk_manager._cache) == 3

    def test_lru_eviction(self, temp_world_dir):
        from server.state.chunk_manager import ChunkManager

        cm = ChunkManager(
            world_name="test_world", world_dir=temp_world_dir, cache_size=3
        )
        chunk_manager = cm

        c0 = chunk_manager.get_chunk(0, 0)
        c1 = chunk_manager.get_chunk(1, 0)
        c2 = chunk_manager.get_chunk(2, 0)

        chunk_manager.get_chunk(0, 0)

        chunk_manager.get_chunk(3, 0)

        assert (0, 0) in chunk_manager._cache
        assert (1, 0) not in chunk_manager._cache

    # ── Dirty tracking ─────────────────────────────────────────────

    def test_get_chunk_not_dirty(self, chunk_manager):
        chunk = chunk_manager.get_chunk(0, 0)
        assert chunk.dirty is False

    def test_mark_chunk_dirty(self, chunk_manager):
        chunk_manager.get_chunk(0, 0)
        chunk_manager.mark_dirty(0, 0)
        chunk = chunk_manager.get_chunk(0, 0)
        assert chunk.dirty is True

    def test_dirty_chunks(self, chunk_manager):
        chunk_manager.get_chunk(0, 0)
        chunk_manager.get_chunk(1, 0)
        chunk_manager.mark_dirty(0, 0)
        chunk_manager.mark_dirty(1, 0)
        dirty = chunk_manager.get_dirty_chunks()
        assert len(dirty) == 2

    # ── Save / Flush ───────────────────────────────────────────────

    def test_flush_saves_dirty_chunks(self, chunk_manager, temp_world_dir):
        chunk_manager.get_chunk(0, 0)
        chunk_manager.mark_dirty(0, 0)
        chunk_manager.flush()

        chunk_file = Path(temp_world_dir) / "test_world" / "chunks" / "0_0.json"
        assert chunk_file.exists()

    def test_flush_clears_dirty_flag(self, chunk_manager):
        chunk_manager.get_chunk(0, 0)
        chunk_manager.mark_dirty(0, 0)
        chunk_manager.flush()
        chunk = chunk_manager.get_chunk(0, 0)
        assert chunk.dirty is False

    def test_load_chunk_from_disk(self, chunk_manager, temp_world_dir):
        chunk_manager.get_chunk(0, 0)
        chunk_manager.mark_dirty(0, 0)
        chunk_manager.flush()

        chunk_manager.reset()
        chunk_manager = chunk_manager.__class__(
            world_name="test_world", world_dir=temp_world_dir, cache_size=10
        )

        chunk = chunk_manager.get_chunk(0, 0)
        from shared.constants import TILE_EMPTY

        assert chunk.get_tile(0, 0) == TILE_EMPTY

    # ── Eviction to disk ───────────────────────────────────────────

    def test_evict_saves_dirty_chunk(self, chunk_manager):
        chunk = chunk_manager.get_chunk(0, 0)
        chunk.dirty = True

        chunk_manager.evict(0, 0)

        assert (0, 0) not in chunk_manager._cache

    def test_evict_clears_dirty_after_save(self, chunk_manager):
        chunk = chunk_manager.get_chunk(0, 0)
        chunk.dirty = True

        chunk_manager.evict(0, 0)
        loaded = chunk_manager.get_chunk(0, 0)

        assert loaded.dirty is False

    # ── World bounds ───────────────────────────────────────────────

    def test_world_bounds(self, chunk_manager, temp_world_dir):
        from server.state.chunk_manager import ChunkManager

        cm = ChunkManager(
            world_name="test_world",
            world_dir=temp_world_dir,
            world_cx=2,
            world_cy=2,
        )
        assert cm.world_cx == 2
        assert cm.world_cy == 2

    def test_out_of_world_bounds(self, temp_world_dir):
        from server.state.chunk_manager import ChunkManager

        cm = ChunkManager(
            world_name="test_world",
            world_dir=temp_world_dir,
            world_cx=2,
            world_cy=2,
        )

        chunk = cm.get_chunk(3, 0)
        assert chunk is None

        chunk = cm.get_chunk(-1, 0)
        assert chunk is None
