import uuid
from server.state.world import get_world
from server.state.models import Player
from server.services.state_sync import make_state_sync
from shared.protocol import Message

__all__ = ["JoinService"]


class JoinService:
    SHORT_ID_LEN = 8

    def handle(self, msg: Message) -> Message:
        world = get_world()

        player_id = uuid.uuid4().hex[: self.SHORT_ID_LEN]

        player = Player(
            id=player_id,
            x=world.width // 2,
            y=world.height // 2,
        )

        world.add_player(player)
        world.seq += 1

        return make_state_sync(player_id)
