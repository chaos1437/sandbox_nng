from server.state.world import get_world
from server.state.models import ChatMessage
from shared.protocol import Message
from shared.constants import MsgType

__all__ = ["ChatService"]


class ChatService:
    """Handles chat messages with configurable limits."""

    def __init__(self, max_lines: int = 5, max_length: int = 200):
        self.max_lines = max_lines
        self.max_length = max_length

    def handle(self, msg: Message) -> Message:
        """Handle a CHAT message.

        Stores the message, trims history, returns STATE_SYNC.
        """
        world = get_world()
        player_id = msg.player_id
        text = msg.payload.get("text", "")

        if not text or not text.strip():
            return self._make_sync(world)

        text = text[: self.max_length]

        chat_msg = ChatMessage(player_id=player_id, text=text)
        world.add_chat_message(chat_msg, max_lines=self.max_lines)

        world.seq += 1
        return self._make_sync(world)

    def _make_sync(self, world) -> Message:
        return Message(
            type=MsgType.STATE_SYNC,
            seq=world.seq,
            payload=world.get_state_snapshot(),
        )
