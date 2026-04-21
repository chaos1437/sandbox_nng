# shared/config.py
"""Config loading."""

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = __import__("logging").getLogger(__name__)


@dataclass
class ServerConfig:
    port: int = 8765
    tick_rate: int = 60
    player_max_speed_tiles_per_sec: float = 10.0
    map_width: int = 40
    map_height: int = 20
    chat_max_lines: int = 5
    chat_max_length: int = 200
    state_sync_interval: float = 0.5
    world_name: str = "default"
    world_cx: int = 16
    world_cy: int = 16
    chunk_size: int = 32
    cache_size: int = 64
    world_seed: int = 42


@dataclass
class ClientConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    controls: dict[str, Any] | None = None
    fps: int = 30
    fov_radius: int = 8
    viewport_width: int = 32
    viewport_height: int = 32


def load_server_config(path: str = "config/server.yaml") -> ServerConfig:
    full_path = Path(__file__).parent.parent / path
    if not full_path.exists():
        log.warning(f"Server config not found: {full_path}, using defaults")
        return ServerConfig()

    with open(full_path) as f:
        data = yaml.safe_load(f) or {}

    s = data.get("server", {})
    p = data.get("player", {})
    m = data.get("map", {})
    c = data.get("chat", {})
    w = data.get("world", {})

    return ServerConfig(
        port=s.get("port", 8765),
        tick_rate=s.get("tick_rate", 60),
        player_max_speed_tiles_per_sec=p.get("max_speed_tiles_per_sec", 10.0),
        map_width=m.get("width", 40),
        map_height=m.get("height", 20),
        chat_max_lines=c.get("max_lines", 5),
        chat_max_length=c.get("max_length", 200),
        state_sync_interval=s.get("state_sync_interval", 0.5),
        world_name=w.get("name", "default"),
        world_cx=w.get("cx", 16),
        world_cy=w.get("cy", 16),
        chunk_size=w.get("chunk_size", 32),
        cache_size=w.get("cache_size", 64),
        world_seed=w.get("seed", 42),
    )


def load_client_config(path: str = "config/client.yaml") -> ClientConfig:
    full_path = Path(__file__).parent.parent / path
    if not full_path.exists():
        log.warning(f"Client config not found: {full_path}, using defaults")
        return ClientConfig()

    with open(full_path) as f:
        data = yaml.safe_load(f) or {}

    s = data.get("server", {})
    ctrl = data.get("controls", {})
    r = data.get("render", {})

    return ClientConfig(
        host=s.get("host", "127.0.0.1"),
        port=s.get("port", 8765),
        controls=ctrl,
        fps=r.get("fps", 30),
        fov_radius=r.get("fov_radius", 8),
        viewport_width=r.get("viewport_width", 32),
        viewport_height=r.get("viewport_height", 32),
    )
