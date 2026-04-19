# server/ecs/systems/chat.py
from dataclasses import dataclass
from server.ecs.system import System
from server.ecs.game_world import GameWorld
from shared.protocol import Message
from shared.constants import MsgType


@dataclass
class ChatMessage:
    player_id: str
    text: str


MAX_CHAT_LINES = 5


class ChatSystem(System):
    def __init__(self) -> None:
        self._messages: list[ChatMessage] = []

    def on_chat(self, world: GameWorld, player_id: str, text: str) -> None:
        """Store message, trim to last 5, broadcast to all players."""
        if not text.strip():
            return

        msg = ChatMessage(player_id=player_id, text=text[:200])
        self._messages.append(msg)

        # Keep only last 5
        if len(self._messages) > MAX_CHAT_LINES:
            self._messages = self._messages[-MAX_CHAT_LINES:]

        # Broadcast to all connected clients via STATE_SYNC
        # Server will send STATE_SYNC after this hook returns
