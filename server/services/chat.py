from dataclasses import dataclass, field
from server.state.world import get_world
from server.state.models import ChatMessage
from server.services.state_sync import make_state_sync
from shared.protocol import Message
from shared.constants import MsgType

__all__ = ["ChatService"]


class ChatService:
    """Handles chat messages with configurable limits."""

    def __init__(self, max_lines: int = 5, max_length: int = 200):
        self.max_lines = max_lines
        self.max_length = max_length
        self.messages: list[ChatMessage] = []

    def handle(self, msg: Message) -> Message:
        world = get_world()
        player_id = msg.player_id
        text = msg.payload.get("text", "")

        if not text or not text.strip():
            return make_state_sync(player_id)

        text = text[: self.max_length]

        chat_msg = ChatMessage(player_id=player_id, text=text)
        self.messages.append(chat_msg)
        if len(self.messages) > self.max_lines:
            self.messages = self.messages[-self.max_lines:]

        return self.get_chat_state(world, player_id)

    def get_chat_state(self, world, player_id: str) -> Message:
        world.seq += 1
        return Message(
            type=MsgType.STATE_SYNC,
            seq=world.seq,
            player_id=player_id,
            payload={
                "seq": world.seq,
                "players": {pid: {"x": p.x, "y": p.y} for pid, p in world.players.items()},
                "full_chunks": [],
                "deltas": [],
                "chat": [{"player_id": m.player_id, "text": m.text} for m in self.messages],
            },
        )
