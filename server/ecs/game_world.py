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
    """Game world holding entities, systems, and the game map."""

    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.systems: list[System] = []
        self.map: GameMap = GameMap()
        self.seq: int = 0

    def register_system(self, system: System) -> None:
        """Add a system to the ordered list."""
        self.systems.append(system)

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the registry."""
        self.entities[entity.id] = entity

    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity from the registry."""
        self.entities.pop(entity_id, None)

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID, or None if not found."""
        return self.entities.get(entity_id)

    def handle_message(self, msg: Message) -> Optional[Message]:
        """Handle a message and return a response Message or None."""
        if msg.type == MsgType.JOIN:
            return self._handle_join(msg)
        elif msg.type == MsgType.MOVE:
            return self._handle_move(msg)
        elif msg.type == MsgType.LEAVE:
            return self._handle_leave(msg)
        return None

    def _handle_join(self, msg: Message) -> Message:
        """Handle a JOIN message."""
        player_id = msg.player_id or uuid.uuid4().hex[:_SHORT_ID_LEN]

        # Notify systems
        for system in self.systems:
            system.on_player_join(self, player_id)

        # Create entity with PositionComponent at spawn point
        entity = Entity(player_id)
        spawn_x = self.map.width // 2
        spawn_y = self.map.height // 2
        entity.add_component(PositionComponent(x=spawn_x, y=spawn_y))
        self.add_entity(entity)

        self.seq += 1
        return self._make_state_sync(include_map=True, player_id=player_id)

    def _make_state_sync(self, include_map: bool = False, player_id: str = "") -> Message:
        return Message(type=MsgType.STATE_SYNC, seq=self.seq, player_id=player_id, payload=self.get_state_snapshot(include_map))

    def _handle_move(self, msg: Message) -> Message:
        """Handle a MOVE message."""
        player_id = msg.player_id
        dx = msg.payload.get("dx", 0)
        dy = msg.payload.get("dy", 0)

        if not isinstance(dx, int) or not isinstance(dy, int):
            return self._make_state_sync()

        # Check with all systems before move
        for system in self.systems:
            if not system.on_before_move(self, player_id, dx, dy):
                # Blocked - return current state
                return self._make_state_sync()

        # Perform the move
        entity = self.get_entity(player_id)
        if entity:
            pos = entity.get_component(PositionComponent)
            if pos:
                nx = pos.x + dx
                ny = pos.y + dy
                if self.map.is_passable(nx, ny):
                    # Replace position component with new values
                    entity.remove_component(PositionComponent)
                    entity.add_component(PositionComponent(x=nx, y=ny))

        # Notify systems after move
        for system in self.systems:
            system.on_after_move(self, player_id, dx, dy)

        self.seq += 1
        return self._make_state_sync()

    def _handle_leave(self, msg: Message) -> None:
        """Handle a LEAVE message."""
        player_id = msg.player_id

        # Notify systems
        for system in self.systems:
            system.on_player_leave(self, player_id)

        # Remove entity
        self.remove_entity(player_id)
        self.seq += 1

    def get_state_snapshot(self, include_map: bool = False) -> dict:
        """Get a snapshot of the current game state."""
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
