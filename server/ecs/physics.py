# server/ecs/physics.py
"""Shared movement math used by server and client prediction."""
from server.ecs.chunk import ChunkManager


def can_apply_move(
    world: ChunkManager,
    current_x: int,
    current_y: int,
    delta_tiles_x: int,
    delta_tiles_y: int,
) -> bool:
    """Return True if entity at (current_x, current_y) can move delta tiles without hitting a wall."""
    target_x = current_x + delta_tiles_x * world.tile_size
    target_y = current_y + delta_tiles_y * world.tile_size
    return world.is_passable(target_x, target_y)


def try_move(
    world: ChunkManager,
    current_x: int,
    current_y: int,
    delta_tiles_x: int,
    delta_tiles_y: int,
) -> tuple[int, int, bool]:
    """Attempt to move by delta tiles. Returns (new_x, new_y, moved).

    moved is True if the step was applied, False if blocked by wall.
    """
    if can_apply_move(world, current_x, current_y, delta_tiles_x, delta_tiles_y):
        new_x = current_x + delta_tiles_x * world.tile_size
        new_y = current_y + delta_tiles_y * world.tile_size
        return (new_x, new_y, True)
    return (current_x, current_y, False)
