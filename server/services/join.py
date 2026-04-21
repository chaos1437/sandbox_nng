import uuid
from server.state.world import get_world
from server.state.models import Player
from shared.protocol import Message
from shared.constants import MsgType

__all__ = ["JoinService"]


class JoinService:
    SHORT_ID_LEN = 8

    def handle(self, msg: Message, suggested_id: str | None = None) -> Message:
        world = get_world()

        player_id = (
            suggested_id or msg.player_id or uuid.uuid4().hex[: self.SHORT_ID_LEN]
        )

        player = Player(
            id=player_id,
            x=world.width // 2,
            y=world.height // 2,
        )

        world.add_player(player)
        world.seq += 1

        return Message(
            type=MsgType.STATE_SYNC,
            seq=world.seq,
            player_id=player_id,
            payload=world.get_state_snapshot(include_map=True),
        )
