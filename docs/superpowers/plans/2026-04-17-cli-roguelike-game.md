# CLI Roguelike Game - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prototype roguelike CLI game with Source Engine-style client-server architecture. Client sends player actions, renders game state. Future: client-side prediction with rollback.

**Architecture:** Client renders roguelike ASCII map from authoritative server state. Network layer is async (asyncio). Client uses fixed timestep game loop separate from render loop. Protocol: delta-state messages over WebSocket (or TCP). Shared `shared/` module contains all message types and protocol constants.

**Tech Stack:** Python 3.11+, asyncio, yaml, websockets (or asyncio TCP), standard library `curses` or `curses` wrapper for rendering.

---

## File Structure

```
/home/llh/proj/sandbox_nng/
├── SPEC.md                          # Living specification
├── client/
│   ├── __init__.py
│   ├── main.py                      # Entry point, curses wrapper, game loop
│   ├── config.py                    # Load YAML config
│   ├── renderer.py                  # ASCII roguelike render (curses)
│   ├── input_handler.py             # Keyboard capture, maps curses codes to dirs
│   ├── network.py                   # Async TCP client, send/receive loop
│   └── state.py                     # Local game state (positions, map)
├── server/
│   ├── __init__.py
│   ├── main.py                      # Entry point, asyncio server, client handler
│   ├── game_state.py                # Authoritative game state, player management
│   ├── player.py                    # Player entity, position, movement
│   ├── map.py                       # Map representation, collision
│   └── handlers.py                  # Handle join/move/leave, build responses
├── shared/
│   ├── __init__.py
│   ├── protocol.py                  # Message dataclass, encode/decode
│   └── constants.py                 # Protocol version, directions, tile types, msg types
└── config/
    ├── client.yaml                  # Server address, controls (curses key names), render fps
    └── server.yaml                  # Port, tick rate, map size
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
PROTOCOL_VERSION = "0.1.0"

# Directions for movement
DIR_NONE = (0, 0)
DIR_NORTH = (0, -1)
DIR_SOUTH = (0, 1)
DIR_EAST  = (1, 0)
DIR_WEST  = (-1, 0)

DIRS = {
    "north": DIR_NORTH,
    "south": DIR_SOUTH,
    "east":  DIR_EAST,
    "west":  DIR_WEST,
}

# Tile types (ASCII chars)
TILE_EMPTY  = "."
TILE_WALL   = "#"
TILE_PLAYER = "@"

# Message types
MSG_JOIN        = "join"
MSG_LEAVE       = "leave"
MSG_MOVE        = "move"
MSG_STATE_SYNC  = "state_sync"
MSG_MAP_SYNC    = "map_sync"
```

- [ ] **Step 2: Create shared/protocol.py**

```python
# shared/protocol.py
import dataclasses
from shared.constants import *

@dataclasses.dataclass
class Message:
    type: str
    seq: int = 0
    player_id: str = ""
    payload: dict = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "seq": self.seq,
            "player_id": self.player_id,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        return cls(
            type=d["type"],
            seq=d.get("seq", 0),
            player_id=d.get("player_id", ""),
            payload=d.get("payload", {}),
        )

def encode(msg: Message) -> bytes:
    import json
    return json.dumps(msg.to_dict()).encode("utf-8")

def decode(data: bytes) -> Message:
    import json
    return Message.from_dict(json.loads(data.decode("utf-8")))
```

- [ ] **Step 3: Commit**

```bash
git add shared/
git commit -m "feat: add shared protocol constants and message types"
```

---

## Task 2: Server - Map and Game State

**Files:**
- Create: `server/__init__.py`
- Create: `server/map.py`
- Create: `server/player.py`
- Create: `server/game_state.py`
- Create: `server/handlers.py`

- [ ] **Step 1: Create server/map.py**

```python
# server/map.py
from shared.constants import TILE_EMPTY, TILE_WALL

class GameMap:
    def __init__(self, width: int = 40, height: int = 20):
        self.width = width
        self.height = height
        # 2D grid, all empty by default
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

- [ ] **Step 2: Create server/player.py**

```python
# server/player.py
class Player:
    def __init__(self, player_id: str, x: int, y: int):
        self.player_id = player_id
        self.x = x
        self.y = y

    def move(self, dx: int, dy: int, game_map) -> bool:
        nx, ny = self.x + dx, self.y + dy
        if game_map.is_passable(nx, ny):
            self.x, self.y = nx, ny
            return True
        return False
```

- [ ] **Step 3: Create server/game_state.py**

```python
# server/game_state.py
import uuid
from server.map import GameMap
from server.player import Player

class GameState:
    def __init__(self):
        self.map = GameMap()
        self.players: dict[str, Player] = {}
        self.seq = 0

    def add_player(self, player_id: str = None) -> Player:
        if player_id is None:
            player_id = str(uuid.uuid4())[:8]
        # Spawn at center
        x, y = self.map.width // 2, self.map.height // 2
        player = Player(player_id, x, y)
        self.players[player_id] = player
        return player

    def remove_player(self, player_id: str):
        self.players.pop(player_id, None)

    def move_player(self, player_id: str, dx: int, dy: int) -> bool:
        player = self.players.get(player_id)
        if not player:
            return False
        return player.move(dx, dy, self.map)

    def get_state_snapshot(self) -> dict:
        return {
            "seq": self.seq,
            "players": {
                pid: {"x": p.x, "y": p.y}
                for pid, p in self.players.items()
            },
        }

    def get_map_snapshot(self) -> dict:
        return {
            "width": self.map.width,
            "height": self.map.height,
            "tiles": self.map.to_lines(),
        }
```

- [ ] **Step 4: Create server/handlers.py**

```python
# server/handlers.py
from shared.protocol import Message, encode
from shared.constants import MSG_JOIN, MSG_LEAVE, MSG_MOVE

def handle_message(state, msg: Message) -> Message | None:
    if msg.type == MSG_JOIN:
        player = state.add_player(msg.player_id or None)
        return Message(
            type="joined",
            seq=state.seq,
            player_id=player.player_id,
            payload={"x": player.x, "y": player.y},
        )
    elif msg.type == MSG_MOVE:
        dx = msg.payload.get("dx", 0)
        dy = msg.payload.get("dy", 0)
        state.move_player(msg.player_id, dx, dy)
        state.seq += 1
        return Message(
            type="state_sync",
            seq=state.seq,
            payload=state.get_state_snapshot(),
        )
    elif msg.type == MSG_LEAVE:
        state.remove_player(msg.player_id)
        return None
    return None
```

- [ ] **Step 5: Commit**

```bash
git add server/
git commit -m "feat(server): add map, player, game state, message handlers"
```

---

## Task 3: Server - Main Loop and Networking

**Files:**
- Create: `server/main.py`
- Modify: `server/__init__.py`

- [ ] **Step 1: Create server/main.py**

```python
# server/main.py
import asyncio
import argparse
from server.game_state import GameState
from server.handlers import handle_message
from shared.protocol import encode, decode
from shared.constants import MSG_JOIN, MSG_LEAVE

async def handle_client(reader, writer, state):
    addr = writer.get_extra_info("peername")
    print(f"[server] Client connected: {addr}")
    player_id = None

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            msg = decode(data)
            print(f"[server] Received: {msg.type} from {msg.player_id}")

            if msg.type == MSG_JOIN:
                player = state.add_player()
                player_id = player.player_id
                resp = Message(
                    type="joined",
                    seq=state.seq,
                    player_id=player_id,
                    payload={
                        "x": player.x,
                        "y": player.y,
                        "map": state.get_map_snapshot(),
                    },
                )
                writer.write(encode(resp))
                await writer.drain()

            elif player_id:
                resp = handle_message(state, msg)
                if resp:
                    writer.write(encode(resp))
                    await writer.drain()
    except Exception as e:
        print(f"[server] Error: {e}")
    finally:
        if player_id:
            state.remove_player(player_id)
        writer.close()
        await writer.wait_closed()
        print(f"[server] Client disconnected: {addr}")

async def main(port: int = 8765):
    state = GameState()
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, state), "0.0.0.0", port
    )
    print(f"[server] Listening on port {port}")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    asyncio.run(main(args.port))
```

Note: Server sends `joined` (with map) in one message — client doesn't need separate `map_sync`. State sync is sent on every move. For multi-client, broadcast added in future iteration.

- [ ] **Step 2: Commit**

```bash
git add server/main.py
git commit -m "feat(server): add TCP async server with client handling"
```

---

## Task 4: Client - Config and Shared Protocol

**Files:**
- Create: `config/client.yaml`
- Create: `config/server.yaml`
- Create: `client/__init__.py`
- Create: `client/config.py`

- [ ] **Step 1: Create config/client.yaml**

```yaml
server:
  host: "127.0.0.1"
  port: 8765

controls:
  up: "KEY_UP"
  down: "KEY_DOWN"
  left: "KEY_LEFT"
  right: "KEY_RIGHT"
  quit: "q"

render:
  fps: 30
```

Note: Key names match curses constants (`getattr(curses, name)`). Config drives all keybindings.

- [ ] **Step 2: Create config/server.yaml**

```yaml
server:
  port: 8765
  tick_rate: 60

map:
  width: 40
  height: 20
```

- [ ] **Step 3: Create client/config.py**

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
    """Resolve YAML string keys (e.g. "KEY_UP") to integer curses codes."""
    resolved = {}
    for action, key_name in controls.items():
        if isinstance(key_name, str) and hasattr(curses, key_name):
            resolved[action] = getattr(curses, key_name)
        else:
            resolved[action] = key_name
    return resolved
```

Remove `client/protocol.py` — import directly from `shared.protocol`.

- [ ] **Step 4: Commit**

```bash
git add config/ client/
git commit -m "feat: add config yaml and client config loader"
```

---

## Task 5: Client - Network Layer

**Files:**
- Create: `client/network.py`

- [ ] **Step 1: Create client/network.py**

```python
# client/network.py
import asyncio
from shared.protocol import encode, decode, Message

class NetworkClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.player_id: str = ""
        self.incoming: asyncio.Queue[Message] = asyncio.Queue()
        self._running = False

    async def connect(self) -> bool:
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            self._running = True
            return True
        except Exception as e:
            print(f"[network] Connection failed: {e}")
            return False

    async def send(self, msg: Message):
        if self.writer:
            self.writer.write(encode(msg))
            await self.writer.drain()

    async def receive_loop(self):
        while self._running:
            try:
                data = await self.reader.read(1024)
                if not data:
                    break
                msg = decode(data)
                await self.incoming.put(msg)
            except Exception as e:
                print(f"[network] Receive error: {e}")
                break

    async def disconnect(self):
        self._running = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
```

- [ ] **Step 2: Commit**

```bash
git add client/network.py
git commit -m "feat(client): add async TCP network client"
```

---

## Task 6: Client - Game State

**Files:**
- Create: `client/state.py`

- [ ] **Step 1: Create client/state.py**

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

    def apply_map_sync(self, payload: dict):
        self.map_width = payload["width"]
        self.map_height = payload["height"]
        self.map = [row[:] for row in payload["tiles"]]

    def apply_state_sync(self, payload: dict):
        self.server_seq = payload["seq"]
        self.player_positions = {
            pid: (data["x"], data["y"])
            for pid, data in payload.get("players", {}).items()
        }

    def set_player_id(self, pid: str):
        self.my_player_id = pid

    def get_my_position(self) -> Optional[tuple[int, int]]:
        return self.player_positions.get(self.my_player_id)
```

- [ ] **Step 2: Commit**

```bash
git add client/state.py
git commit -m "feat(client): add client-side game state"
```

---

## Task 7: Client - Input Handler

**Files:**
- Create: `client/input_handler.py`

- [ ] **Step 1: Create client/input_handler.py**

```python
# client/input_handler.py
from shared.constants import DIRS

class InputHandler:
    def __init__(self, resolved_controls: dict):
        # resolved_controls: {action: curses_key_int}
        self.key_to_dir = {}
        for action, key in resolved_controls.items():
            if action in DIRS:
                self.key_to_dir[key] = action

    def get_direction(self, key) -> str | None:
        return self.key_to_dir.get(key)

    def get_move_delta(self, direction: str) -> tuple[int, int]:
        return DIRS.get(direction, (0, 0))
```

- [ ] **Step 2: Commit**

```bash
git add client/input_handler.py
git commit -m "feat(client): add input handler with keybinding support"
```

---

## Task 8: Client - ASCII Renderer

**Files:**
- Create: `client/renderer.py`

- [ ] **Step 1: Create client/renderer.py**

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

        # Draw map
        for y, row in enumerate(state.map):
            for x, tile in enumerate(row):
                char = tile if tile != TILE_EMPTY else "."
                self.stdscr.addch(y, x, char)

        # Draw players (overwrite map tiles)
        for pid, (x, y) in state.player_positions.items():
            char = TILE_PLAYER if pid == state.my_player_id else "P"
            self.stdscr.addch(y, x, char)

        # Status line
        my_pos = state.get_my_position()
        status = f"Player: {state.my_player_id} | Pos: {my_pos} | Seq: {state.server_seq}"
        self.stdscr.addstr(state.map_height + 1, 0, status)

        self.stdscr.refresh()

    def get_key(self):
        return self.stdscr.getch()
```

- [ ] **Step 2: Commit**

```bash
git add client/renderer.py
git commit -m "feat(client): add curses-based roguelike renderer"
```

---

## Task 9: Client - Main Loop

**Files:**
- Create: `client/main.py`

- [ ] **Step 1: Create client/main.py**

```python
# client/main.py
import asyncio
import argparse
import curses
from client.config import load_client_config, resolve_controls
from client.network import NetworkClient
from client.state import ClientGameState
from client.input_handler import InputHandler
from client.renderer import RoguelikeRenderer
from shared.protocol import Message
from shared.constants import MSG_JOIN, MSG_MOVE, MSG_LEAVE

async def main(stdscr):
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    config = load_client_config()
    state = ClientGameState()
    network = NetworkClient(args.host, args.port)
    renderer = RoguelikeRenderer(stdscr)
    controls = resolve_controls(config.get("controls", {}))
    input_handler = InputHandler(controls)
    quit_key = controls.get("quit", ord('q'))

    if not await network.connect():
        return

    # Send join
    join_msg = Message(type=MSG_JOIN, player_id="")
    await network.send(join_msg)

    # Start receive loop
    receive_task = asyncio.create_task(network.receive_loop())

    running = True
    while running:
        # Process network messages
        try:
            while not network.incoming.empty():
                msg = await network.incoming.get()
                if msg.type == "joined":
                    state.set_player_id(msg.player_id)
                    network.player_id = msg.player_id
                    state.apply_map_sync(msg.payload["map"])
                elif msg.type == "state_sync":
                    state.apply_state_sync(msg.payload)
        except asyncio.QueueEmpty:
            pass

        # Render
        if state.map:
            renderer.render(state)

        # Input
        curses.napms(33)  # ~30fps
        key = renderer.get_key()
        if key != -1:
            if key == quit_key:
                running = False
            elif key in input_handler.key_to_dir:
                direction = input_handler.key_to_dir[key]
                dx, dy = input_handler.get_move_delta(direction)
                move_msg = Message(
                    type=MSG_MOVE,
                    seq=state.server_seq,
                    player_id=network.player_id,
                    payload={"dx": dx, "dy": dy},
                )
                await network.send(move_msg)

    receive_task.cancel()
    leave_msg = Message(type=MSG_LEAVE, player_id=network.player_id)
    await network.send(leave_msg)
    await network.disconnect()

if __name__ == "__main__":
    curses.wrapper(lambda stdscr: asyncio.run(main(stdscr)))
```

- [ ] **Step 2: Commit**

```bash
git add client/main.py
git commit -m "feat(client): add main game loop with async networking"
```

---

## Task 10: SPEC.md - Living Specification

**Files:**
- Create: `SPEC.md`

- [ ] **Step 1: Create SPEC.md**

```markdown
# CLI Roguelike Game - Specification

## Overview
Multiplayer roguelike game with CLI interface. Source Engine-style architecture:
client sends player actions, server broadcasts authoritative state.
Client renders roguelike ASCII map.

## Architecture

### Source Engine Parallels
| Source Engine | This Project |
|---------------|--------------|
| Client predicts player movement | Future: client applies move immediately, rolls back on server correction |
| Server is authoritative | Server validates all moves, broadcasts state |
| cl_delta | Delta-state messages (seq numbers) |
| Client hooks (CHud*) | Client render hooks on state change |

### Current Phase (Prototype)
- Client sends `move` action → server validates → server broadcasts `state_sync`
- Client has no prediction yet — renders server state directly
- Future: prediction/rollback will use `seq` for conflict detection

### Future Phase (Prediction)
- Client applies local move immediately (optimistic)
- Server sends `state_sync` with authoritative seq
- If server seq > local seq: roll back local prediction, apply server state
- Input buffer: store unacknowledged moves, replay on rollback

## Protocol

### Message Types
| Type | Direction | Description |
|------|----------|-------------|
| `join` | C→S | Player requests to join |
| `joined` | S→C | Server confirms with player_id, spawn pos, and full map |
| `move` | C→S | Player movement request with delta |
| `state_sync` | S→C | Authoritative state broadcast (seq, all player positions) |
| `leave` | C→S | Player disconnects |

### State Sync Format
```json
{
  "type": "state_sync",
  "seq": 42,
  "payload": {
    "players": {
      "player_id": {"x": 5, "y": 10}
    }
  }
}
```

## Config

### client.yaml
- `server.host`, `server.port` — connection
- `controls` — keybinding map (action → key name)
- `render.fps` — target render rate

### server.yaml
- `server.port` — listen port
- `server.tick_rate` — game tick rate (future)
- `map.width`, `map.height` — map dimensions

## Project Structure
```
client/       — rendering, input, network (stateless render from server state)
server/       — authoritative game state, player management, map, message handlers
shared/       — protocol messages, constants (single source of truth, no duplicates)
config/       — YAML configs (server address, controls, map size)
```

## Extensibility Points
1. **Prediction/Rollback** — use `seq` in state_sync to detect desync, replay input buffer
2. **Tile entities** — extend `TILE_*` constants, add to map renderer
3. **Server tick rate** — server.yaml tick_rate, client interpolation
4. **Entity system** — Player class becomes Entity, add components
5. **Map format** — load from file (future: procedural generation)
6. **Networking** — switch TCP → WebSocket for HTTP gateway compatibility
```

- [ ] **Step 2: Commit**

```bash
git add SPEC.md
git commit -m "docs: add SPEC.md architecture specification"
```

---

## Self-Review Checklist

- [ ] All 10 tasks have code, no TODOs/TBDs
- [ ] Every task has a commit step
- [ ] `shared/protocol.py` used by both client and server (single source of truth)
- [ ] Architecture supports prediction/rollback via `seq` field — not implemented yet, but hook is there
- [ ] Config in YAML, keybindings loaded at runtime
- [ ] Client renders from server state (no local simulation in prototype)
- [ ] Type consistency: `Message.to_dict()` / `Message.from_dict()` symmetric, `DIRS` dict used in both input_handler and player.move
