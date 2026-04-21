import json
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

MANIFEST_VERSION = 1


@dataclass
class WorldManifest:
    version: int = MANIFEST_VERSION
    name: str = "default"
    seed: int = 42
    chunk_size: int = 32
    world_cx: int = 16
    world_cy: int = 16


def get_world_dir(base_dir: str = "./server/worlds") -> Path:
    return Path(base_dir)


def ensure_world_dir(world_name: str, base_dir: str = "./server/worlds") -> Path:
    world_dir = get_world_dir(base_dir) / world_name
    (world_dir / "chunks").mkdir(parents=True, exist_ok=True)
    return world_dir


def load_manifest(
    world_name: str, base_dir: str = "./server/worlds"
) -> WorldManifest | None:
    world_dir = get_world_dir(base_dir) / world_name
    manifest_path = world_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        with open(manifest_path) as f:
            data = json.load(f)
        return WorldManifest(
            version=data.get("version", 0),
            name=data.get("name", world_name),
            seed=data.get("seed", 42),
            chunk_size=data.get("chunk_size", 32),
            world_cx=data.get("world_cx", 16),
            world_cy=data.get("world_cy", 16),
        )
    except (json.JSONDecodeError, KeyError) as e:
        log.warning(f"Failed to load manifest for world '{world_name}': {e}")
        return None


def save_manifest(manifest: WorldManifest, base_dir: str = "./server/worlds"):
    world_dir = ensure_world_dir(manifest.name, base_dir)
    manifest_path = world_dir / "manifest.json"
    data = {
        "version": manifest.version,
        "name": manifest.name,
        "seed": manifest.seed,
        "chunk_size": manifest.chunk_size,
        "world_cx": manifest.world_cx,
        "world_cy": manifest.world_cy,
    }
    with open(manifest_path, "w") as f:
        json.dump(data, f)
    log.info(f"Saved manifest for world '{manifest.name}'")


def create_default_manifest(
    world_name: str,
    seed: int = 42,
    chunk_size: int = 32,
    world_cx: int = 16,
    world_cy: int = 16,
    base_dir: str = "./server/worlds",
) -> WorldManifest:
    manifest = WorldManifest(
        name=world_name,
        seed=seed,
        chunk_size=chunk_size,
        world_cx=world_cx,
        world_cy=world_cy,
    )
    save_manifest(manifest, base_dir)
    return manifest


def get_or_create_manifest(
    world_name: str,
    seed: int = 42,
    chunk_size: int = 32,
    world_cx: int = 16,
    world_cy: int = 16,
    base_dir: str = "./server/worlds",
) -> WorldManifest:
    manifest = load_manifest(world_name, base_dir)
    if manifest is None:
        manifest = create_default_manifest(
            world_name, seed, chunk_size, world_cx, world_cy, base_dir
        )
    return manifest


def get_or_create_manifest(
    world_name: str,
    seed: int = 42,
    chunk_size: int = 32,
    world_cx: int = 16,
    world_cy: int = 16,
    base_dir: str = "./server/worlds",
) -> WorldManifest:
    manifest = load_manifest(world_name, base_dir)
    if manifest is None:
        manifest = create_default_manifest(
            world_name, seed, chunk_size, world_cx, world_cy, base_dir
        )
    return manifest
