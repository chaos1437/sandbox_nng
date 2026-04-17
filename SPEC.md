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
