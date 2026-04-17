# shared/config.py
"""Unified config loading with auto-migration support."""
import yaml
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

CURRENT_VERSION = 1


@dataclass
class ServerConfig:
    port: int = 8765
    tick_rate: int = 60
    player_max_speed_tiles_per_sec: float = 10.0
    map_width: int = 40
    map_height: int = 20


@dataclass
class ClientConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    controls: dict[str, Any] = field(default_factory=dict)
    fps: int = 30


def _migrate_server(data: dict, path: Path) -> dict:
    """Migrate server config to current version."""
    version = data.get("version", 0)

    if version == 0:
        # v0 -> v1: add version field
        data["version"] = 1
        log.info(f"Migrated server config from v0 to v1: {path}")
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    # Future migrations here:
    # if version < 2:
    #     ... migrate v1 -> v2
    #     version = 2

    return data


def _migrate_client(data: dict, path: Path) -> dict:
    """Migrate client config to current version."""
    version = data.get("version", 0)

    if version == 0:
        # v0 -> v1: add version field
        data["version"] = 1
        log.info(f"Migrated client config from v0 to v1: {path}")
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    return data


def load_server_config(path: str = "config/server.yaml") -> ServerConfig:
    """Load and migrate server config."""
    full_path = Path(__file__).parent.parent / path
    if not full_path.exists():
        log.warning(f"Server config not found: {full_path}, using defaults")
        return ServerConfig()

    with open(full_path) as f:
        data = yaml.safe_load(f)

    if data is None:
        data = {}

    data = _migrate_server(data, full_path)

    s = data.get("server", {})
    p = data.get("player", {})
    m = data.get("map", {})

    return ServerConfig(
        port=s.get("port", 8765),
        tick_rate=s.get("tick_rate", 60),
        player_max_speed_tiles_per_sec=p.get("max_speed_tiles_per_sec", 10.0),
        map_width=m.get("width", 40),
        map_height=m.get("height", 20),
    )


def load_client_config(path: str = "config/client.yaml") -> ClientConfig:
    """Load and migrate client config."""
    full_path = Path(__file__).parent.parent / path
    if not full_path.exists():
        log.warning(f"Client config not found: {full_path}, using defaults")
        return ClientConfig()

    with open(full_path) as f:
        data = yaml.safe_load(f)

    if data is None:
        data = {}

    data = _migrate_client(data, full_path)

    s = data.get("server", {})
    ctrl = data.get("controls", {})
    r = data.get("render", {})

    return ClientConfig(
        host=s.get("host", "127.0.0.1"),
        port=s.get("port", 8765),
        controls=ctrl,
        fps=r.get("fps", 30),
    )
