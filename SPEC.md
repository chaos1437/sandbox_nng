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
1. Добавить функциональных E2E тестов. Перейти на TDD подход.
2. Стандартизировать сетевые взаимодействия клиента и сервера, вынести классы в shared/
3. Добавить систему чата
4. Добавить продвинутую систему карты(разделение на чанки, подгрузка по мере видимости, генерация новых на ходу)
5. Бесконечный рефакторинг 
6. Добавить NPC с pathfinding

Auto-update: git pull + Y/n dialog. Local configs preserved on conflict.
