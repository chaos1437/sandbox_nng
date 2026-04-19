# client/state.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChatLine:
    player_id: str
    text: str


class ClientGameState:
    def __init__(self):
        self.map: list[list[str]] = []
        self.map_width: int = 0
        self.map_height: int = 0
        self.player_positions: dict[str, tuple[int, int]] = {}
        self.my_player_id: str = ""
        self.server_seq: int = 0
        # Chat
        self.chat_open: bool = False
        self.chat_input: str = ""
        self.chat_messages: list[ChatLine] = []

    def apply_state_sync(self, payload: dict):
        self.server_seq = payload["seq"]
        self.player_positions = {
            pid: (data["x"], data["y"])
            for pid, data in payload.get("players", {}).items()
        }
        # First sync may include map
        if "map" in payload:
            self.map_width = payload["map"]["width"]
            self.map_height = payload["map"]["height"]
            self.map = [row[:] for row in payload["map"]["tiles"]]
        # Chat messages
        if "chat" in payload:
            self.chat_messages = [
                ChatLine(player_id=m["player_id"], text=m["text"])
                for m in payload["chat"]
            ]

    def set_player_id(self, pid: str):
        self.my_player_id = pid

    def get_my_position(self) -> Optional[tuple[int, int]]:
        return self.player_positions.get(self.my_player_id)
