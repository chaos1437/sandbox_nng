# shared/protocol.py
import dataclasses
import json
from shared.constants import *


@dataclasses.dataclass
class Message:
    type: str
    seq: int = 0
    player_id: str = ""
    payload: dict = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "seq": self.seq,
            "player_id": self.player_id,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        return cls(
            type=d["type"],
            seq=d.get("seq", 0),
            player_id=d.get("player_id", ""),
            payload=d.get("payload", {}),
        )


def encode(msg: Message) -> bytes:
    return json.dumps(msg.to_dict()).encode("utf-8")


def decode(data: bytes) -> Message:
    return Message.from_dict(json.loads(data.decode("utf-8")))
