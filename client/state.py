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
