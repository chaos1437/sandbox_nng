# CLI Roguelike Game - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prototype roguelike CLI game with Source Engine-style client-server architecture. Client sends player actions, renders game state. Future: client-side prediction with rollback.

**Architecture:** Client renders roguelike ASCII map from authoritative server state. Network layer is async (asyncio TCP). Protocol: newline-delimited JSON messages. Server uses ECS pattern for extensibility. Shared `shared/` module contains protocol, config (versioned), logging, serializers.

**Tech Stack:** Python 3.11+, asyncio, yaml, standard library `curses`.

---

## File Structure

```
/home/llh/proj/sandbox_nng/
├── run.py                  # Auto-updating launcher (Y/n prompt)
├── requirements.txt         # pyyaml
├── docs/
│   └── superpowers/
│       └── plans/
│           └── 2026-04-17-cli-roguelike-game.md
├── config/
│   ├── client.yaml         # server host/port, controls, render fps
│   └── server.yaml         # port, tick_rate, map size, player speed
├── client/
│   ├── __init__.py
│   ├── main.py             # Entry point, curses wrapper, game loop
│   ├── config.py           # resolve_controls (YAML → curses codes)
│   ├── renderer.py         # ASCII roguelike render (curses)
│   ├── input_handler.py    # Keyboard capture, maps curses codes to dirs
│   ├── network.py          # Async TCP client, send/receive loop
│   └── state.py            # Local game state (positions, map)
├── server/
│   ├── __init__.py
│   ├── main.py             # Entry point, asyncio server, client handler
│   └── ecs/                # Entity-Component-System engine
│       ├── __init__.py     # Exports: System, Component, Entity, GameWorld
│       ├── system.py       # System ABC with lifecycle hooks
│       ├── component.py     # Component (data), PositionComponent
│       ├── entity.py        # Entity with component registry
│       ├── game_world.py   # GameWorld: entities + systems + map + message routing
│       ├── map.py          # GameMap: 2D grid of tiles
│       └── systems/
│           ├── __init__.py
│           └── movement_controller.py  # Rate-limits player movement
├── shared/
│   ├── __init__.py
│   ├── protocol.py         # Message dataclass, encode/decode
│   ├── constants.py        # MsgType enum, DIRS, TILE_* constants
│   ├── serializers.py       # Serializer ABC (JsonSerializer default)
│   ├── logging.py          # setup_logger (console, file)
│   └── config.py           # Versioned config loading with migration
└── tests/
    ├── __init__.py
    ├── test_client.py
    ├── test_server.py
    ├── test_shared.py
    ├── test_config.py
    └── test_ecs.py
```

---

## Task 1: Shared Protocol

**Files:**
- Create: `shared/__init__.py`
- Create: `shared/protocol.py`
- Create: `shared/constants.py`

- [ ] **Step 1: Create shared/constants.py**

```python
# shared/constants.py
from enum import StrEnum

class MsgType(StrEnum):
    JOIN = "join"
    LEAVE = "leave"
    MOVE = "move"
    STATE_SYNC = "state_sync"

# Directions for movement (up/down/left/right)
DIR_UP    = (0, -1)
DIR_DOWN  = (0, 1)
DIR_LEFT  = (-1, 0)
DIR_RIGHT = (1, 0)

DIRS = {
    "up": DIR_UP,
    "down": DIR_DOWN,
    "left": DIR_LEFT,
    "right": DIR_RIGHT,
}

# Tile types (ASCII chars)
TILE_EMPTY  = " "
TILE_WALL   = "#"
TILE_PLAYER = "@"
```

- [ ] **Step 2: Create shared/protocol.py**

```python
# shared/protocol.py
from dataclasses import dataclass
from shared.constants import MsgType

@dataclass
class Message:
    type: MsgType | str
    seq: int = 0
    player_id: str = ""
    payload: dict = None

    def __post_init__(self):
        if self.payload is None:
            self.payload = {}

    def to_dict(self) -> dict:
        return {
            "type": str(self.type),
            "seq": self.seq,
            "player_id": self.player_id,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        raw_type = d["type"]
        try:
            msg_type = MsgType(raw_type)
        except ValueError:
            msg_type = raw_type
        return cls(
            type=msg_type,
            seq=d.get("seq", 0),
            player_id=d.get("player_id", ""),
            payload=d.get("payload", {}),
        )
```

- [ ] **Step 3: Create shared/serializers.py**

```python
# shared/serializers.py
from abc import ABC, abstractmethod
from shared.protocol import Message
import json

class Serializer(ABC):
    @abstractmethod
    def encode(self, msg: Message) -> bytes: ...

    @abstractmethod
    def decode(self, data: bytes) -> Message: ...

class JsonSerializer(Serializer):
    def encode(self, msg: Message) -> bytes:
        return json.dumps(msg.to_dict()).encode("utf-8")

    def decode(self, data: bytes) -> Message:
        return Message.from_dict(json.loads(data.decode("utf-8")))
```

- [ ] **Step 4: Commit**

---

## Task 2: Server ECS Architecture

**Files:**
- Create: `server/__init__.py`
- Create: `server/ecs/__init__.py`
- Create: `server/ecs/system.py`
- Create: `server/ecs/component.py`
- Create: `server/ecs/entity.py`
- Create: `server/ecs/game_world.py`
- Create: `server/ecs/map.py`
- Create: `server/ecs/systems/__init__.py`
- Create: `server/ecs/systems/movement_controller.py`
- Create: `server/main.py`

- [ ] **Step 1: Create server/ecs/component.py**

```python
# server/ecs/component.py
from dataclasses import dataclass

__all__ = ["Component", "PositionComponent"]

@dataclass
class Component:
    """Base class for ECS components. Pure data, no behavior."""
    entity_id: str = ""

@dataclass
class PositionComponent(Component):
    """2D position."""
    x: int = 0
    y: int = 0
```

- [ ] **Step 2: Create server/ecs/entity.py**

```python
# server/ecs/entity.py
from typing import TypeVar, Type, Optional

from server.ecs.component import Component

__all__ = ["Entity"]

C = TypeVar("C", bound=Component)

class Entity:
    """An ECS entity - an ID with a collection of components."""

    def __init__(self, entity_id: str) -> None:
        self.id = entity_id
        self.components: dict[Type[Component], Component] = {}

    def add_component(self, component: Component) -> None:
        component.entity_id = self.id
        self.components[type(component)] = component

    def remove_component(self, component_type: Type[C]) -> None:
        self.components.pop(component_type, None)

    def has_component(self, component_type: Type[Component]) -> bool:
        return component_type in self.components

    def get_component(self, component_type: Type[C]) -> Optional[C]:
        return self.components.get(component_type)
```

- [ ] **Step 3: Create server/ecs/system.py**

```python
# server/ecs/system.py
from abc import ABC

__all__ = ["System"]

class System(ABC):
    """ECS system - behavior attached to entities."""

    def __init__(self) -> None:
        raise NotImplementedError("System is abstract")

    def on_player_join(self, world: "GameWorld", player_id: str) -> None:
        """Called when a player joins."""
        pass

    def on_before_move(self, world: "GameWorld", player_id: str, dx: int, dy: int) -> bool:
        """Called before move. Return False to block."""
        return True

    def on_after_move(self, world: "GameWorld", player_id: str, dx: int, dy: int) -> None:
        """Called after move."""
        pass

    def on_player_leave(self, world: "GameWorld", player_id: str) -> None:
        """Called when a player leaves."""
        pass

    def update(self, world: "GameWorld") -> None:
        """Called each tick."""
        pass
```

- [ ] **Step 4: Create server/ecs/map.py**

```python
# server/ecs/map.py
from shared.constants import TILE_EMPTY, TILE_WALL

class GameMap:
    def __init__(self, width: int = 40, height: int = 20):
        self.width = width
        self.height = height
        self.tiles = [[TILE_EMPTY for _ in range(width)] for _ in range(height)]

    def set_wall(self, x: int, y: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = TILE_WALL

    def is_passable(self, x: int, y: int) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tiles[y][x] != TILE_WALL

    def to_lines(self) -> list[list[str]]:
        return [row[:] for row in self.tiles]
```

- [ ] **Step 5: Create server/ecs/game_world.py**

```python
# server/ecs/game_world.py
import uuid
from typing import Optional

from server.ecs import System, Entity
from server.ecs.component import PositionComponent
from server.ecs.map import GameMap
from shared.protocol import Message
from shared.constants import MsgType

_SHORT_ID_LEN = 8

class GameWorld:
    """Game world: entities + systems + map + message routing."""

    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.systems: list[System] = []
        self.map: GameMap = GameMap()
        self.seq: int = 0

    def register_system(self, system: System) -> None:
        self.systems.append(system)

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def remove_entity(self, entity_id: str) -> None:
        self.entities.pop(entity_id, None)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def handle_message(self, msg: Message) -> Optional[Message]:
        if msg.type == MsgType.JOIN:
            return self._handle_join(msg)
        elif msg.type == MsgType.MOVE:
            return self._handle_move(msg)
        elif msg.type == MsgType.LEAVE:
            return self._handle_leave(msg)
        return None

    def _handle_join(self, msg: Message) -> Message:
        player_id = msg.player_id or uuid.uuid4().hex[:_SHORT_ID_LEN]
        for system in self.systems:
            system.on_player_join(self, player_id)
        entity = Entity(player_id)
        spawn_x = self.map.width // 2
        spawn_y = self.map.height // 2
        entity.add_component(PositionComponent(x=spawn_x, y=spawn_y))
        self.add_entity(entity)
        self.seq += 1
        return self._make_state_sync(include_map=True, player_id=player_id)

    def _handle_move(self, msg: Message) -> Message:
        player_id = msg.player_id
        dx = msg.payload.get("dx", 0)
        dy = msg.payload.get("dy", 0)
        if not isinstance(dx, int) or not isinstance(dy, int):
            return self._make_state_sync()
        for system in self.systems:
            if not system.on_before_move(self, player_id, dx, dy):
                return self._make_state_sync()
        entity = self.get_entity(player_id)
        if entity:
            pos = entity.get_component(PositionComponent)
            if pos:
                nx, ny = pos.x + dx, pos.y + dy
                if self.map.is_passable(nx, ny):
                    entity.remove_component(PositionComponent)
                    entity.add_component(PositionComponent(x=nx, y=ny))
        for system in self.systems:
            system.on_after_move(self, player_id, dx, dy)
        self.seq += 1
        return self._make_state_sync()

    def _handle_leave(self, msg: Message) -> None:
        player_id = msg.player_id
        for system in self.systems:
            system.on_player_leave(self, player_id)
        self.remove_entity(player_id)
        self.seq += 1

    def _make_state_sync(self, include_map: bool = False, player_id: str = "") -> Message:
        return Message(
            type=MsgType.STATE_SYNC,
            seq=self.seq,
            player_id=player_id,
            payload=self.get_state_snapshot(include_map),
        )

    def get_state_snapshot(self, include_map: bool = False) -> dict:
        snap = {
            "seq": self.seq,
            "players": {
                eid: {
                    "x": entity.get_component(PositionComponent).x,
                    "y": entity.get_component(PositionComponent).y,
                }
                for eid, entity in self.entities.items()
                if entity.has_component(PositionComponent)
            },
        }
        if include_map:
            snap["map"] = {
                "width": self.map.width,
                "height": self.map.height,
                "tiles": self.map.to_lines(),
            }
        return snap
```

- [ ] **Step 6: Create server/ecs/systems/movement_controller.py**

```python
# server/ecs/systems/movement_controller.py
from dataclasses import dataclass
import time
from server.ecs import System, GameWorld

__all__ = ["MovementController", "PlayerMoveRecord"]

@dataclass
class PlayerMoveRecord:
    last_move_time: float = 0.0
    violations: int = 0
    total_moves: int = 0

class MovementController(System):
    def __init__(self, max_speed_tiles_per_sec: float = 10.0) -> None:
        self.max_speed = max_speed_tiles_per_sec
        self._records: dict[str, PlayerMoveRecord] = {}

    def on_before_move(self, world: GameWorld, player_id: str, dx: int, dy: int) -> bool:
        now = time.time()
        record = self._records.setdefault(player_id, PlayerMoveRecord())
        min_interval = 1.0 / self.max_speed if self.max_speed > 0 else 0.0
        if now - record.last_move_time < min_interval:
            record.violations += 1
            return False
        record.last_move_time = now
        record.total_moves += 1
        return True

    def on_player_leave(self, world: GameWorld, player_id: str) -> None:
        self._records.pop(player_id, None)

    def get_stats(self, player_id: str) -> dict:
        record = self._records.get(player_id)
        if record is None:
            return {"total_moves": 0, "violations": 0}
        return {"total_moves": record.total_moves, "violations": record.violations}
```

- [ ] **Step 7: Create server/main.py**

```python
# server/main.py
import asyncio
import traceback
import argparse
from server.ecs.game_world import GameWorld
from server.ecs.systems.movement_controller import MovementController
from shared.protocol import Message
from shared.constants import MsgType
from shared.logging import setup_logger
from shared.serializers import Serializer
from shared.config import load_server_config

log = setup_logger("server", "server.log")

class ClientConnection:
    def __init__(self, reader, writer, serializer: Serializer):
        self.reader = reader
        self.writer = writer
        self.serializer = serializer
        self.player_id: str | None = None
        self.addr = writer.get_extra_info("peername")

    async def send(self, msg: Message):
        data = self.serializer.encode(msg) + b'\n'
        self.writer.write(data)
        await self.writer.drain()

async def broadcast(clients: list[ClientConnection], msg: Message):
    alive = []
    for conn in clients:
        try:
            await conn.send(msg)
            alive.append(conn)
        except Exception:
            conn.writer.close()
    return alive

async def handle_client(reader, writer, world: GameWorld, clients: list[ClientConnection], serializer: Serializer):
    conn = ClientConnection(reader, writer, serializer)
    clients.append(conn)
    log.info(f"Client connected: {conn.addr}")
    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            msg = serializer.decode(data.rstrip(b'\n'))
            msg = Message(type=msg.type, seq=msg.seq, player_id=conn.player_id or msg.player_id, payload=msg.payload)
            resp = world.handle_message(msg)
            if resp:
                if resp.player_id and not conn.player_id:
                    conn.player_id = resp.player_id
                    log.info(f"Player {conn.player_id} joined from {conn.addr}")
                resp = Message(type=resp.type, seq=resp.seq, player_id=conn.player_id, payload=resp.payload)
                clients[:] = await broadcast(clients, resp)
    except Exception as e:
        log.error(f"Error: {e}\n{traceback.format_exc()}")
    finally:
        if conn.player_id:
            world.remove_entity(conn.player_id)
        clients.remove(conn)
        conn.writer.close()
        await conn.writer.wait_closed()

async def main(port: int = 8765, serializer: Serializer | None = None):
    if serializer is None:
        from shared.serializers import JsonSerializer
        serializer = JsonSerializer()
    cfg = load_server_config()
    port = port or cfg.port
    world = GameWorld()
    world.register_system(MovementController(max_speed_tiles_per_sec=cfg.player_max_speed_tiles_per_sec))
    clients: list[ClientConnection] = []
    async def handler(reader, writer):
        await handle_client(reader, writer, world, clients, serializer)
    server = await asyncio.start_server(handler, "0.0.0.0", port)
    log.info(f"Listening on port {port}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    asyncio.run(main(args.port))
```

- [ ] **Step 8: Commit**

---

## Task 3: Client

**Files:**
- Create: `client/__init__.py`
- Create: `client/main.py`
- Create: `client/config.py`
- Create: `client/renderer.py`
- Create: `client/input_handler.py`
- Create: `client/network.py`
- Create: `client/state.py`

- [ ] **Step 1: Create client/config.py**

```python
# client/config.py
import yaml
import curses
from pathlib import Path

def load_client_config(path: str = "config/client.yaml") -> dict:
    full_path = Path(__file__).parent.parent / path
    with open(full_path) as f:
        return yaml.safe_load(f)

def resolve_controls(controls: dict) -> dict:
    """Resolve YAML string keys to integer curses codes."""
    resolved = {}
    for action, key_name in controls.items():
        if isinstance(key_name, str) and hasattr(curses, key_name):
            resolved[action] = getattr(curses, key_name)
        elif isinstance(key_name, str):
            stripped = key_name.strip("'\"")
            if len(stripped) == 1:
                resolved[action] = ord(stripped)
            else:
                resolved[action] = key_name
        else:
            resolved[action] = key_name
    return resolved
```

- [ ] **Step 2: Create client/network.py**

```python
# client/network.py
import asyncio
from shared.protocol import Message
from shared.serializers import Serializer
from shared.logging import setup_logger

log = setup_logger("network", "client.log", console=False)

class NetworkClient:
    def __init__(self, host: str, port: int, serializer: Serializer | None = None):
        self.host = host
        self.port = port
        self.serializer = serializer or JsonSerializer()
        self.reader = None
        self.writer = None
        self.incoming: asyncio.Queue[Message] = asyncio.Queue()
        self._running = False

    async def connect(self) -> bool:
        try:
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            self._running = True
            return True
        except Exception as e:
            log.error(f"Connection failed: {e}")
            return False

    async def send(self, msg: Message):
        if self.writer:
            self.writer.write(self.serializer.encode(msg) + b'\n')
            await self.writer.drain()

    async def receive_loop(self):
        while self._running:
            try:
                data = await self.reader.readline()
                if not data:
                    break
                msg = self.serializer.decode(data.rstrip(b'\n'))
                await self.incoming.put(msg)
            except Exception as e:
                log.error(f"Receive error: {e}")
                break

    async def disconnect(self):
        self._running = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
```

- [ ] **Step 3: Create client/state.py**

```python
# client/state.py
from typing import Optional

class ClientGameState:
    def __init__(self):
        self.map: list[list[str]] = []
        self.map_width: int = 0
        self.map_height: int = 0
        self.player_positions: dict[str, tuple[int, int]] = {}
        self.my_player_id: str = ""
        self.server_seq: int = 0

    def apply_state_sync(self, payload: dict):
        self.server_seq = payload["seq"]
        self.map_width = payload.get("map", {}).get("width", 0)
        self.map_height = payload.get("map", {}).get("height", 0)
        self.map = [row[:] for row in payload.get("map", {}).get("tiles", [])]
        self.player_positions = {
            pid: (data["x"], data["y"])
            for pid, data in payload.get("players", {}).items()
        }

    def set_player_id(self, pid: str):
        self.my_player_id = pid

    def get_my_position(self) -> Optional[tuple[int, int]]:
        return self.player_positions.get(self.my_player_id)
```

- [ ] **Step 4: Create client/input_handler.py**

```python
# client/input_handler.py
from shared.constants import DIRS

class InputHandler:
    def __init__(self, resolved_controls: dict):
        self.key_to_dir = {}
        for action, key in resolved_controls.items():
            if action in DIRS:
                self.key_to_dir[key] = action

    def get_direction(self, key) -> str | None:
        return self.key_to_dir.get(key)

    def get_move_delta(self, direction: str) -> tuple[int, int]:
        return DIRS.get(direction, (0, 0))
```

- [ ] **Step 5: Create client/renderer.py**

```python
# client/renderer.py
import curses
from client.state import ClientGameState
from shared.constants import TILE_EMPTY, TILE_WALL, TILE_PLAYER

class RoguelikeRenderer:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

    def render(self, state: ClientGameState):
        self.stdscr.clear()
        for y, row in enumerate(state.map):
            for x, tile in enumerate(row):
                char = tile if tile != TILE_EMPTY else "."
                self.stdscr.addch(y, x, char)
        for pid, (x, y) in state.player_positions.items():
            char = TILE_PLAYER if pid == state.my_player_id else "P"
            self.stdscr.addch(y, x, char)
        my_pos = state.get_my_position()
        status = f"Player: {state.my_player_id} | Pos: {my_pos} | Seq: {state.server_seq}"
        self.stdscr.addstr(state.map_height + 1, 0, status)
        self.stdscr.refresh()

    def get_key(self):
        return self.stdscr.getch()
```

- [ ] **Step 6: Create client/main.py**

```python
# client/main.py
import asyncio
import curses
from client.config import resolve_controls
from client.network import NetworkClient
from client.state import ClientGameState
from client.input_handler import InputHandler
from client.renderer import RoguelikeRenderer
from shared.protocol import Message
from shared.constants import MsgType
from shared.logging import setup_logger
from shared.serializers import JsonSerializer

log = setup_logger("client", "client.log", console=False)

async def main(stdscr, config):
    stdscr.keypad(True)
    state = ClientGameState()
    network = NetworkClient(config.host, config.port, JsonSerializer())
    renderer = RoguelikeRenderer(stdscr)
    controls = resolve_controls(config.controls)
    input_handler = InputHandler(controls)
    quit_key = controls.get("quit", ord('q'))

    if not await network.connect():
        return
    await network.send(Message(type=MsgType.JOIN, player_id=""))
    receive_task = asyncio.create_task(network.receive_loop())

    running = True
    while running:
        await asyncio.sleep(0)
        while True:
            try:
                msg = network.incoming.get_nowait()
                if msg.type == MsgType.STATE_SYNC:
                    state.apply_state_sync(msg.payload)
                    if not state.my_player_id and msg.player_id:
                        state.set_player_id(msg.player_id)
            except asyncio.QueueEmpty:
                break
        if state.map:
            renderer.render(state)
        curses.napms(16)
        key = renderer.get_key()
        if key != -1:
            if key == quit_key:
                running = False
            elif key in input_handler.key_to_dir:
                direction = input_handler.key_to_dir[key]
                dx, dy = input_handler.get_move_delta(direction)
                await network.send(Message(type=MsgType.MOVE, seq=state.server_seq, player_id=state.my_player_id, payload={"dx": dx, "dy": dy}))

    receive_task.cancel()
    await network.disconnect()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    from shared.config import load_client_config
    cfg = load_client_config()
    cfg.host = args.host
    cfg.port = args.port
    curses.wrapper(lambda stdscr: asyncio.run(main(stdscr, cfg)))
```

- [ ] **Step 7: Commit**

---

## Task 4: Config and Launcher

**Files:**
- Create: `config/client.yaml`
- Create: `config/server.yaml`
- Create: `shared/config.py`
- Create: `run.py`
- Create: `requirements.txt`

- [ ] **Step 1: Create shared/config.py**

```python
# shared/config.py
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

def _migrate(data: dict, path: Path) -> dict:
    version = data.get("version", 0)
    if version == 0:
        data["version"] = 1
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        log.info(f"Migrated config from v0 to v1: {path}")
    return data

def load_server_config(path: str = "config/server.yaml") -> ServerConfig:
    full_path = Path(__file__).parent.parent / path
    if not full_path.exists():
        return ServerConfig()
    with open(full_path) as f:
        data = yaml.safe_load(f) or {}
    data = _migrate(data, full_path)
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
    full_path = Path(__file__).parent.parent / path
    if not full_path.exists():
        return ClientConfig()
    with open(full_path) as f:
        data = yaml.safe_load(f) or {}
    data = _migrate(data, full_path)
    s = data.get("server", {})
    ctrl = data.get("controls", {})
    r = data.get("render", {})
    return ClientConfig(host=s.get("host", "127.0.0.1"), port=s.get("port", 8765), controls=ctrl, fps=r.get("fps", 30))
```

- [ ] **Step 2: Create config/client.yaml**

```yaml
version: 1
server:
  host: 127.0.0.1
  port: 8765
controls:
  up: w
  down: s
  left: a
  right: d
  quit: q
render:
  fps: 30
```

- [ ] **Step 3: Create config/server.yaml**

```yaml
version: 1
server:
  port: 8765
  tick_rate: 60
player:
  max_speed_tiles_per_sec: 10.0
map:
  width: 40
  height: 20
```

- [ ] **Step 4: Create run.py**

```python
#!/usr/bin/env python3
"""Auto-updating launcher."""
import asyncio
import subprocess
import sys
import argparse
from pathlib import Path

def check_for_updates():
    repo = Path(__file__).parent
    if not (repo / ".git").exists():
        return False
    subprocess.run(["git", "fetch"], cwd=repo, capture_output=True)
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD..origin/master"],
        cwd=repo, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return False
    try:
        return int(result.stdout.strip()) > 0
    except ValueError:
        return False

def update():
    repo = Path(__file__).parent
    configs = {}
    for f in ["config/server.yaml", "config/client.yaml"]:
        p = repo / f
        if p.exists():
            configs[f] = p.read_bytes()
    result = subprocess.run(["git", "pull"], cwd=repo, capture_output=True, text=True)
    if result.returncode != 0:
        for f, data in configs.items():
            (repo / f).write_bytes(data)
    if result.stdout.strip():
        print(result.stdout.rstrip())

def ask_update() -> bool:
    print("Updates available. Update? [Y/n]", end=" ")
    try:
        return input().strip().lower() in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False

def main():
    parser = argparse.ArgumentParser(description="Roguelike game launcher")
    subparsers = parser.add_subparsers(dest="mode", help="Launch mode")
    client_parser = subparsers.add_parser("client", help="Launch client")
    client_parser.add_argument("--host", default="127.0.0.1")
    client_parser.add_argument("--port", type=int, default=8765)
    server_parser = subparsers.add_parser("server", help="Launch server")
    server_parser.add_argument("--port", type=int, default=8765)
    args, _ = parser.parse_known_args()
    if args.mode is None:
        args.mode = "client"
    if check_for_updates():
        if ask_update():
            update()
        else:
            print("Skipping update, launching with current version...")
    if args.mode == "server":
        sys.argv = ["server"]
        if args.port != 8765:
            sys.argv.extend(["--port", str(args.port)])
        from server.main import main as server_main
        asyncio.run(server_main())
    else:
        from shared.config import load_client_config
        cfg = load_client_config()
        cfg.host = args.host
        cfg.port = args.port
        from client.main import main as client_main
        import curses
        def run(stdscr):
            asyncio.run(client_main(stdscr, cfg))
        curses.wrapper(run)

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Create requirements.txt**

```
pyyaml
```

- [ ] **Step 6: Commit**

---

## Task 5: Tests

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_client.py`
- Create: `tests/test_server.py`
- Create: `tests/test_shared.py`
- Create: `tests/test_config.py`
- Create: `tests/test_ecs.py`

- [ ] **Step 1: Create tests**

Test ECS: Entity, Component, System, GameWorld, MovementController.
Test protocol: Message encode/decode roundtrip.
Test config: load_server_config, load_client_config.
Test client: state, input_handler.

- [ ] **Step 2: Commit**

---

## Self-Review Checklist

- [ ] All tasks have code, no TODOs/TBDs
- [ ] Every task has a commit step
- [ ] `shared/protocol.py` used by both client and server (single source of truth)
- [ ] Architecture supports prediction/rollback via `seq` field — not implemented yet, but hook is there
- [ ] Config in YAML, keybindings loaded at runtime
- [ ] Client renders from server state (no local simulation in prototype)
- [ ] ECS architecture: Systems are pluggable, registered at startup
- [ ] MovementController blocks excessive speed via `on_before_move` hook
- [ ] run.py preserves local configs on git pull conflict
