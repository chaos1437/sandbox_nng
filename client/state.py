# client/state.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChatLine:
    player_id: str
    text: str


class ClientGameState:
    def __init__(self):
        self.chunks: dict[str, list[list[str]]] = {}
        self.chunk_size: int = 32
        self.player_positions: dict[str, tuple[int, int]] = {}
        self.my_player_id: str = ""
        self.server_seq: int = 0
        self.chat_open: bool = False
        self.chat_input: str = ""
        self.chat_messages: list[ChatLine] = []

    def apply_state_sync(self, payload: dict):
        self.server_seq = payload["seq"]
        self.player_positions = {
            pid: (data["x"], data["y"])
            for pid, data in payload.get("players", {}).items()
        }
        if "full_chunks" in payload:
            for chunk_data in payload["full_chunks"]:
                key = f"{chunk_data['cx']},{chunk_data['cy']}"
                self.chunks[key] = chunk_data["tiles"]
        if "deltas" in payload:
            self._apply_deltas(payload["deltas"])
        if "chat" in payload:
            self.chat_messages = [
                ChatLine(player_id=m["player_id"], text=m["text"])
                for m in payload["chat"]
            ]

    def _apply_deltas(self, deltas: list):
        for wx, wy, tile in deltas:
            cx = wx // self.chunk_size
            cy = wy // self.chunk_size
            lx = wx % self.chunk_size
            ly = wy % self.chunk_size
            key = f"{cx},{cy}"
            if key in self.chunks:
                if 0 <= ly < len(self.chunks[key]) and 0 <= lx < len(
                    self.chunks[key][ly]
                ):
                    self.chunks[key][ly][lx] = tile

    def get_tile(self, wx: int, wy: int) -> Optional[str]:
        cx = wx // self.chunk_size
        cy = wy // self.chunk_size
        lx = wx % self.chunk_size
        ly = wy % self.chunk_size
        key = f"{cx},{cy}"
        if key not in self.chunks:
            return None
        chunk = self.chunks[key]
        if 0 <= ly < len(chunk) and 0 <= lx < len(chunk[ly]):
            return chunk[ly][lx]
        return None

    def set_player_id(self, pid: str):
        self.my_player_id = pid

    def get_my_position(self) -> Optional[tuple[int, int]]:
        return self.player_positions.get(self.my_player_id)
