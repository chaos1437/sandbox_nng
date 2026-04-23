from server.state.models import Player


class FOVManager:
    def __init__(self, chunk_radius: int = 1, chunk_size: int = 32):
        self.chunk_radius = chunk_radius
        self.chunk_size = chunk_size
        self._player_fov: dict[str, set[tuple[int, int]]] = {}

    def compute_fov(self, player: Player) -> set[tuple[int, int]]:
        cx = player.x // self.chunk_size
        cy = player.y // self.chunk_size
        r = self.chunk_radius
        return {
            (cx + dx, cy + dy) for dx in range(-r, r + 1) for dy in range(-r, r + 1)
        }

    def update_fov(self, player: Player) -> set[tuple[int, int]]:
        fov = self.compute_fov(player)
        self._player_fov[player.id] = fov
        return fov

    def update_fov_with_delta(
        self, player: Player
    ) -> tuple[set[tuple[int, int]], set[tuple[int, int]], bool]:
        old_fov = self._player_fov.get(player.id, set())
        new_fov = self.compute_fov(player)
        self._player_fov[player.id] = new_fov
        crossed = old_fov != new_fov
        return old_fov, new_fov, crossed

    def get_players_in_chunks(self, chunks: set[tuple[int, int]]) -> list[str]:
        result = []
        for pid, pchunks in self._player_fov.items():
            if pchunks & chunks:
                result.append(pid)
        return result

    def should_send_to(self, recipient_id: str, mover_id: str) -> bool:
        recipient_fov = self._player_fov.get(recipient_id, set())
        mover_fov = self._player_fov.get(mover_id, set())
        return bool(recipient_fov & mover_fov)

    def get_player_chunk(self, player: Player) -> tuple[int, int]:
        return (player.x // self.chunk_size, player.y // self.chunk_size)

    def remove_player(self, player_id: str) -> None:
        self._player_fov.pop(player_id, None)
