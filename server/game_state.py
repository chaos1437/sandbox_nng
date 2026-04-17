# server/game_state.py
import uuid
from server.map import GameMap
from server.ecs.entity import Entity
from server.ecs.component import PositionComponent


class GameState:
    def __init__(self):
        self.map = GameMap()
        self.entities: dict[str, Entity] = {}
        self.seq = 0

    def add_player(self, player_id: str = None) -> Entity:
        if player_id is None:
            player_id = str(uuid.uuid4())[:8]
        # Spawn at center
        x, y = self.map.width // 2, self.map.height // 2
        entity = Entity(player_id)
        entity.add_component(PositionComponent(entity_id=player_id, x=x, y=y))
        self.entities[player_id] = entity
        return entity

    def remove_player(self, player_id: str):
        self.entities.pop(player_id, None)

    def move_player(self, player_id: str, dx: int, dy: int) -> bool:
        entity = self.entities.get(player_id)
        if not entity:
            return False
        pos = entity.get_component(PositionComponent)
        if not pos:
            return False
        nx, ny = pos.x + dx, pos.y + dy
        if self.map.is_passable(nx, ny):
            # Replace with new PositionComponent (immutable dataclass)
            entity.remove_component(PositionComponent)
            entity.add_component(PositionComponent(entity_id=player_id, x=nx, y=ny))
            return True
        return False

    def get_state_snapshot(self, include_map: bool = False) -> dict:
        snap = {
            "seq": self.seq,
            "players": {
                eid: {"x": e.get_component(PositionComponent).x, "y": e.get_component(PositionComponent).y}
                for eid, e in self.entities.items()
            },
        }
        if include_map:
            snap["map"] = {
                "width": self.map.width,
                "height": self.map.height,
                "tiles": self.map.to_lines(),
            }
        return snap
