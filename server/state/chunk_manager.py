import json
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from server.state.chunk import Chunk, generate_chunk, CHUNK_SIZE

log = logging.getLogger(__name__)

DEFAULT_CACHE_SIZE = 64


class ChunkManager:
    def __init__(
        self,
        world_name: str,
        world_dir: str = "./server/worlds",
        world_cx: int = 16,
        world_cy: int = 16,
        chunk_size: int = CHUNK_SIZE,
        cache_size: int = DEFAULT_CACHE_SIZE,
        seed: int = 42,
    ):
        self.world_name = world_name
        self.world_dir = Path(world_dir)
        self.world_cx = world_cx
        self.world_cy = world_cy
        self.chunk_size = chunk_size
        self.cache_size = cache_size
        self.seed = seed

        self._cache: OrderedDict[tuple[int, int], Chunk] = OrderedDict()
        self._world_path = self.world_dir / world_name
        self._chunks_path = self._world_path / "chunks"
        self._ensure_dirs()

    def _ensure_dirs(self):
        self._chunks_path.mkdir(parents=True, exist_ok=True)

    def _chunk_file(self, cx: int, cy: int) -> Path:
        return self._chunks_path / f"{cx}_{cy}.json"

    def _load_from_disk(self, cx: int, cy: int) -> Optional[Chunk]:
        path = self._chunk_file(cx, cy)
        if not path.exists():
            return None
        try:
            with open(path) as f:
                data = json.load(f)
            return Chunk.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            log.warning(f"Failed to load chunk {cx},{cy}: {e}")
            return None

    def _save_to_disk(self, chunk: Chunk):
        path = self._chunk_file(chunk.cx, chunk.cy)
        with open(path, "w") as f:
            json.dump(chunk.to_dict(), f)
        log.debug(f"Saved chunk {chunk.cx},{chunk.cy} to {path}")

    def _generate(self, cx: int, cy: int) -> Chunk:
        return generate_chunk(cx, cy, self.seed)

    def _in_bounds(self, cx: int, cy: int) -> bool:
        return 0 <= cx < self.world_cx and 0 <= cy < self.world_cy

    def get_chunk(self, cx: int, cy: int) -> Optional[Chunk]:
        if not self._in_bounds(cx, cy):
            return None

        key = (cx, cy)
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]

        chunk = self._load_from_disk(cx, cy)
        if chunk is None:
            chunk = self._generate(cx, cy)

        self._cache[key] = chunk
        self._evict_if_needed()
        return chunk

    def _evict_if_needed(self):
        while len(self._cache) > self.cache_size:
            oldest_key, oldest_chunk = self._cache.popitem(last=False)
            if oldest_chunk.dirty:
                self._save_to_disk(oldest_chunk)
                oldest_chunk.dirty = False

    def mark_dirty(self, cx: int, cy: int):
        key = (cx, cy)
        if key in self._cache:
            self._cache[key].dirty = True

    def get_dirty_chunks(self) -> list[Chunk]:
        return [c for c in self._cache.values() if c.dirty]

    def flush(self):
        for chunk in self._cache.values():
            if chunk.dirty:
                self._save_to_disk(chunk)
                chunk.dirty = False
        log.debug(f"Flushed dirty chunks for world '{self.world_name}'")

    def evict(self, cx: int, cy: int):
        key = (cx, cy)
        if key not in self._cache:
            return
        chunk = self._cache[key]
        if chunk.dirty:
            self._save_to_disk(chunk)
            chunk.dirty = False
        del self._cache[key]

    def reset(self):
        self._cache.clear()

    def world_to_chunk(self, wx: int, wy: int) -> tuple[int, int, int, int]:
        cx = wx // self.chunk_size
        cy = wy // self.chunk_size
        lx = wx % self.chunk_size
        ly = wy % self.chunk_size
        return cx, cy, lx, ly
