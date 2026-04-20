from server.ecs import System, GameWorld
from dataclasses import dataclass
import time


@dataclass
class PlayerMoveRecord:
    last_move_time: float = 0.0
    violations: int = 0
    total_moves: int = 0


class MovementController(System):
    def __init__(self, max_speed_tiles_per_sec: float = 10.0) -> None:
        self.max_speed = max_speed_tiles_per_sec
        self._records: dict[str, PlayerMoveRecord] = {}

    def on_before_move(self, world: GameWorld, player_id: str, dx: int, dy: int) -> bool:
        """Rate limit check — return False to block move."""
        now = time.time()
        record = self._records.setdefault(player_id, PlayerMoveRecord())

        elapsed = now - record.last_move_time
        min_interval = 1.0 / self.max_speed if self.max_speed > 0 else 0.0

        if elapsed < min_interval:
            record.violations += 1
            return False

        record.last_move_time = now
        record.total_moves += 1
        return True

    def on_player_leave(self, world: GameWorld, player_id: str) -> None:
        self._records.pop(player_id, None)

    def get_stats(self, player_id: str) -> dict:
        record = self._records.get(player_id)
        if record is None:
            return {"total_moves": 0, "violations": 0}
        return {
            "total_moves": record.total_moves,
            "violations": record.violations,
        }
