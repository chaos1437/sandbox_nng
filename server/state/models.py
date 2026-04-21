from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class Player:
    id: str
    x: int = 0
    y: int = 0
    last_move_time: float = 0.0
    violations: int = 0
    total_moves: int = 0


@dataclass
class ChatMessage:
    player_id: str
    text: str


__all__ = ["Player", "ChatMessage"]
