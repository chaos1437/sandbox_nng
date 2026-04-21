from server.state.world import get_world
from shared.protocol import Message
from shared.constants import MsgType

__all__ = ["LeaveService"]


class LeaveService:
    """Handles player disconnection."""

    def handle(self, msg: Message) -> Message:
        """Handle a LEAVE message.

        Removes player from world. Returns STATE_SYNC with updated state.
        """
        world = get_world()
        player_id = msg.player_id

        world.remove_player(player_id)
        world.seq += 1

        return Message(
            type=MsgType.STATE_SYNC,
            seq=world.seq,
            payload=world.get_state_snapshot(),
        )
