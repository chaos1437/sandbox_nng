import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from server.state.chunk import Chunk
    from server.state.manifest import WorldManifest

log = logging.getLogger(__name__)


def serialize_chunk(chunk: "Chunk") -> dict:
    return chunk.to_dict()


def deserialize_chunk(data: dict) -> "Chunk":
    from server.state.chunk import Chunk

    return Chunk.from_dict(data)


def serialize_world(
    manifest: "WorldManifest",
    chunks: list["Chunk"],
) -> dict:
    return {
        "manifest": {
            "version": manifest.version,
            "name": manifest.name,
            "seed": manifest.seed,
            "chunk_size": manifest.chunk_size,
            "world_cx": manifest.world_cx,
            "world_cy": manifest.world_cy,
        },
        "chunks": [serialize_chunk(c) for c in chunks],
    }


def deserialize_world(data: dict) -> tuple["WorldManifest", list["Chunk"]]:
    from server.state.manifest import WorldManifest

    m_data = data.get("manifest", {})
    manifest = WorldManifest(
        version=m_data.get("version", 1),
        name=m_data.get("name", "unknown"),
        seed=m_data.get("seed", 42),
        chunk_size=m_data.get("chunk_size", 32),
        world_cx=m_data.get("world_cx", 16),
        world_cy=m_data.get("world_cy", 16),
    )
    chunks = [deserialize_chunk(c) for c in data.get("chunks", [])]
    return manifest, chunks


def save_world_archive(
    world_name: str,
    chunks: list["Chunk"],
    manifest: "WorldManifest",
    base_dir: str = "./server/worlds",
):
    world_dir = Path(base_dir) / world_name
    archive_path = world_dir / "world.json"
    data = serialize_world(manifest, chunks)
    with open(archive_path, "w") as f:
        json.dump(data, f)
    log.info(f"Saved world archive for '{world_name}' to {archive_path}")


def load_world_archive(
    world_name: str,
    base_dir: str = "./server/worlds",
) -> tuple["WorldManifest", list["Chunk"]] | None:
    world_dir = Path(base_dir) / world_name
    archive_path = world_dir / "world.json"
    if not archive_path.exists():
        return None
    try:
        with open(archive_path) as f:
            data = json.load(f)
        return deserialize_world(data)
    except (json.JSONDecodeError, KeyError) as e:
        log.warning(f"Failed to load world archive '{world_name}': {e}")
        return None
