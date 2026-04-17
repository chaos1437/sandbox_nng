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

    def get_state_snapshot(self, include_map: bool = False) -> dict:
        snap = {
            "seq": self.seq,
            "players": {
                pid: {"x": p.x, "y": p.y}
                for pid, p in self.players.items()
            },
        }
        if include_map:
            snap["map"] = {
                "width": self.map.width,
                "height": self.map.height,
                "tiles": self.map.to_lines(),
            }
        return snap
