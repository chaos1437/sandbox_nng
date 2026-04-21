# CLI Roguelike — Architecture

## Overview

Multiplayer roguelike, CLI, Source Engine-style: client sends actions, server authoritative, broadcasts state.

## Architecture

```
run.py              # launcher, auto-update (Y/n), starts client or server
requirements.txt    # pyyaml

client/             # async TCP, curses rendering, stateless
  network.py         # uses shared/Connection
  config.py          # resolve_controls() only
  main.py            # game loop + input handling
  state.py           # ClientGameState (map, players, chat)

server/
  network/          # network layer (connections, client handler)
    connections.py   # Connections (manages all client connections + broadcast)
    handlers.py      # handle_client (TCP session) + ServiceRegistry
  services/         # event-driven message handlers
    join.py          # JOIN → STATE_SYNC (player at center)
    move.py          # MOVE → STATE_SYNC (rate limiting, wall collision)
    chat.py          # CHAT → STATE_SYNC (configurable limits)
    leave.py         # LEAVE → STATE_SYNC (cleanup)
  state/            # game state singleton
    models.py        # Player, ChatMessage dataclasses
    world.py         # GameWorldState singleton (players, map, chat, seq)
  main.py           # entry point, wires network + services

shared/             # protocol, config, logging, serializers, network primitives
  network.py        # Connection + read_message (shared TCP abstraction)
  serializers.py   # Serializer ABC + JsonSerializer
  protocol.py       # Message dataclass + MsgType enum
  constants.py      # tiles, directions, MsgType values
  config.py         # versioned YAML loading (ServerConfig, ClientConfig)

config/             # YAML configs (auto-migrated on load)
tests/              # pytest
  test_client/      # client-specific tests (config, state, input)
  test_services/    # join, move, chat, leave service tests
  test_state/       # GameWorldState singleton tests
  test_shared/     # constants, protocol tests
```

## Event-Driven Architecture

```
Message → ServiceRegistry.dispatch() → [JoinService|MoveService|ChatService|LeaveService]
                                                    ↓
                                              GameWorldState (singleton)
                                                    ↓
                                              STATE_SYNC broadcast
```

### Services

Each service is a simple class with a `handle(msg: Message) -> Message | None` method:

- **JoinService**: generates player ID, places player at map center, includes map in first response
- **MoveService**: validates types, enforces rate limiting from config, checks wall collision
- **ChatService**: truncates to max_length, trims history to max_lines, both from config
- **LeaveService**: removes player, broadcasts updated state

### GameWorldState Singleton

Single source of truth for all game state:
- `players: dict[str, Player]` — active players
- `cells: list[list[bool]]` — map grid (False=passable, True=wall)
- `chat_messages: list[ChatMessage]` — recent chat history
- `seq: int` — monotonically increasing state version

Extensible via `get_instance()` / `reset()` pattern (swap for test doubles).

## Network Layer

- `Connection` — single TCP abstraction (connect/reader/writer/send/close)
- `Connections` (was ConnectionRegistry) — owns all live connections + broadcast logic
- `ServiceRegistry` — wires network messages to services
- `read_message` — shared helper for newline-delimited message framing
- `Message` — protocol unit (type, seq, player_id, payload)
- `Serializer` ABC — swap JsonSerializer → ProtobufSerializer

## Protocol

`MsgType`: `JOIN`, `MOVE`, `STATE_SYNC`, `LEAVE`, `CHAT`
Messages: newline-delimited JSON over TCP.

## Config

`shared/config.py` — versioned YAML loading. `version: 1` field. Auto-migrate on load.

`ServerConfig` fields:
- `port`, `tick_rate`, `host`
- `player_max_speed_tiles_per_sec` (rate limiting)
- `map_width`, `map_height`
- `chat_max_lines` (default 5)
- `chat_max_length` (default 200)
- `state_sync_interval` (default 0.5s)

`ClientConfig` fields:
- `host`, `port`, `controls`, `fps`

## Launch with run.py

```bash
python run.py              # client (default)
python run.py client
python run.py server --port 9000
```


## Launch directly without autoupdate
```bash
python -m client.main
python -m server.main
python -m client.main --host 1.2.3.4 --port 9000
```

## TODO
1. Добавить функциональных E2E тестов. Перейти на TDD подход. ✅
2. Стандартизировать сетевые взаимодействия клиента и сервера, вынести классы в shared/ ✅
3. Добавить систему чата ✅
4. Добавить систему карты (пока простая grid, future: chunked) ✅
5. Рефакторинг: ECS → Event-Driven ✅
6. Добавить NPC с pathfinding

Auto-update: git pull + Y/n dialog. Local configs preserved on conflict.