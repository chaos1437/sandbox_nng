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
  ecs/              # Entity-Component-System engine
    systems/        # MovementController, ChatSystem
    game_world.py   # entities + systems + map + seq
  registry.py       # ConnectionRegistry (server-only, owns all client connections)
  main.py           # wires network to ECS (no TCP primitives)

shared/             # protocol, config, logging, serializers, network primitives
  network.py        # Connection + read_message (shared TCP abstraction)
  serializers.py   # Serializer ABC + JsonSerializer
  protocol.py       # Message dataclass + MsgType enum
  constants.py      # tiles, directions, MsgType values
  config.py         # versioned YAML loading

config/             # YAML configs (auto-migrated on load)
tests/              # pytest
  test_client/       # client-specific tests (config, state, input)
```

## ECS

```
Entity  = ID + dict[Type[Component], Component]
Component = data (dataclass)
System   = behavior (hooks: on_player_join, on_before_move, on_before_move→bool, on_after_move, on_player_leave, update)
GameWorld = entities + systems + map + seq + handle_message()
```

New system = class extending `System`, register with `world.register_system()`.

## Network Layer

- `Connection` — single TCP abstraction for both client and server (connect/reader/writer/send/close)
- `ConnectionRegistry` — server-only, owns all live connections + broadcast logic
- `read_message` — shared helper for newline-delimited message framing
- `Message` — protocol unit (type, seq, player_id, payload)
- `Serializer` ABC — swap JsonSerializer → ProtobufSerializer

## Protocol

`MsgType`: `JOIN`, `MOVE`, `STATE_SYNC`, `LEAVE`, `CHAT`
Messages: newline-delimited JSON over TCP.

## Config

`shared/config.py` — versioned YAML loading. `version: 1` field. Auto-migrate on load.

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
4. Добавить продвинутую систему карты(разделение на чанки, подгрузка по мере видимости, генерация новых на ходу)
5. Бесконечный рефакторинг
6. Добавить NPC с pathfinding

Auto-update: git pull + Y/n dialog. Local configs preserved on conflict.
