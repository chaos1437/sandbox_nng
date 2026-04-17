# CLI Roguelike — Architecture

## Overview

Multiplayer roguelike, CLI, Source Engine-style: client sends actions, server authoritative, broadcasts state.

## Architecture

```
run.py              # launcher, auto-update (Y/n), starts client or server
requirements.txt    # pyyaml

client/             # async TCP, curses rendering, stateless
server/ecs/         # Entity-Component-System engine
  systems/          # pluggable: MovementController (anticheat)
shared/             # protocol, config (versioned), logging, serializers
config/             # YAML configs (auto-migrated on load)
tests/              # pytest
```

## ECS

```
Entity  = ID + dict[Type[Component], Component]
Component = data (dataclass)
System   = behavior (hooks: on_player_join, on_before_move, on_before_move→bool, on_after_move, on_player_leave, update)
GameWorld = entities + systems + map + seq + handle_message()
```

New system = class extending `System`, register with `world.register_system()`.

## Protocol

`MsgType`: `JOIN`, `MOVE`, `STATE_SYNC`, `LEAVE`
Messages: newline-delimited JSON over TCP.
`Serializer` ABC — swap JsonSerializer → ProtobufSerializer.

## Config

`shared/config.py` — versioned YAML loading. `version: 1` field. Auto-migrate on load.

## Launch

```bash
python run.py              # client (default)
python run.py client
python run.py server --port 9000
```

Auto-update: git pull + Y/n dialog. Local configs preserved on conflict.
