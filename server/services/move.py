import time
from server.state.world import get_world
from server.state.models import Player
from server.services.state_sync import make_state_sync
from shared.protocol import Message

__all__ = ["MoveService"]


class MoveService:
    """Handles player movement with rate limiting from config."""

    def __init__(self, max_speed_tiles_per_sec: float = 10.0):
        self.max_speed_tiles_per_sec = max_speed_tiles_per_sec
        self._min_interval = (
            1.0 / max_speed_tiles_per_sec if max_speed_tiles_per_sec > 0 else 0.0
        )

    def handle(self, msg: Message) -> Message:
        """Handle a MOVE message.

        Rate limits moves. Validates bounds. Returns simple move event.
        """
        world = get_world()
        player_id = msg.player_id
        dx = msg.payload.get("dx", 0)
        dy = msg.payload.get("dy", 0)

        if not isinstance(dx, int) or not isinstance(dy, int):
            return make_state_sync(player_id)

        player = world.get_player(player_id)
        if not player:
            return make_state_sync(player_id)

        now = time.time()
        if self.max_speed_tiles_per_sec == 0:
            player.violations += 1
            return make_state_sync(player_id)
        elapsed = now - player.last_move_time
        if elapsed < self._min_interval:
            player.violations += 1
            return make_state_sync(player_id)

        nx = player.x + dx
        ny = player.y + dy

        if world.is_passable(nx, ny):
            player.x = nx
            player.y = ny

        player.last_move_time = now
        player.total_moves += 1

        world.seq += 1

        return make_state_sync(player_id)
