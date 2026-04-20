# server/ecs/game_world.py
"""Simple grid-based world — entities move cell-by-cell, no pixel coords."""
import uuid
from typing import Optional

from server.ecs import System, Entity
from server.ecs.component import PositionComponent
from shared.protocol import Message
from shared.constants import MsgType

_SHORT_ID_LEN = 8

_HANDLERS = {
    MsgType.JOIN: lambda w, m: w._handle_join(m),
    MsgType.MOVE: lambda w, m: w._handle_move(m),
    MsgType.LEAVE: lambda w, m: w._handle_leave(m),
    MsgType.CHAT: lambda w, m: w._handle_chat(m),
}


class GameWorld:
    def __init__(self, width: int = 40, height: int = 20) -> None:
        self.width = width
        self.height = height
        self.cells: list[list[bool]] = [
            [False for _ in range(width)] for _ in range(height)
        ]  # False = passable, True = wall
        self.entities: dict[str, Entity] = {}
        self.systems: list[System] = []
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
        handler = _HANDLERS.get(msg.type)
        if handler:
            return handler(self, msg)
        return None

    def set_wall(self, cell_x: int, cell_y: int) -> None:
        """Mark cell as wall."""
        if 0 <= cell_x < self.width and 0 <= cell_y < self.height:
            self.cells[cell_y][cell_x] = True

    def is_passable(self, cell_x: int, cell_y: int) -> bool:
        """Return True if cell is inside bounds and not a wall."""
        if not (0 <= cell_x < self.width and 0 <= cell_y < self.height):
            return False
        return not self.cells[cell_y][cell_x]

    def _handle_join(self, msg: Message) -> Message:
        player_id = msg.player_id or uuid.uuid4().hex[:_SHORT_ID_LEN]

        for system in self.systems:
            system.on_player_join(self, player_id)

        entity = Entity(player_id)
        entity.add_component(PositionComponent(
            cell_x=self.width // 2,
            cell_y=self.height // 2,
        ))
        self.add_entity(entity)

        self.seq += 1
        return self._make_state_sync(include_map=True, player_id=player_id)

    def _make_state_sync(self, include_map: bool = False, player_id: str = "") -> Message:
        return Message(type=MsgType.STATE_SYNC, seq=self.seq, player_id=player_id, payload=self.get_state_snapshot(include_map))

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
                nx = pos.cell_x + dx
                ny = pos.cell_y + dy
                if self.is_passable(nx, ny):
                    pos.cell_x = nx
                    pos.cell_y = ny

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

    def _handle_chat(self, msg: Message) -> Message:
        player_id = msg.player_id
        text = msg.payload.get("text", "")

        for system in self.systems:
            if hasattr(system, "on_chat"):
                system.on_chat(self, player_id, text)

        self.seq += 1
        return self._make_state_sync()

    def get_state_snapshot(self, include_map: bool = False) -> dict:
        snap = {
            "seq": self.seq,
            "players": {
                eid: {
                    "x": entity.get_component(PositionComponent).cell_x,
                    "y": entity.get_component(PositionComponent).cell_y,
                }
                for eid, entity in self.entities.items()
                if entity.has_component(PositionComponent)
            },
        }
        if include_map:
            snap["map"] = {
                "width": self.width,
                "height": self.height,
                "tiles": self._grid_to_strings(),
            }

        for system in self.systems:
            if hasattr(system, "_messages"):
                snap["chat"] = [
                    {"player_id": m.player_id, "text": m.text}
                    for m in system._messages
                ]
                break

        return snap

    def _grid_to_strings(self) -> list[list[str]]:
        """Return map as 2D grid of tile chars."""
        from server.ecs.map import TILE_EMPTY, TILE_WALL
        result = []
        for row in self.cells:
            result.append([TILE_WALL if cell else TILE_EMPTY for cell in row])
        return result