import pytest
from server.ecs.chunk import ChunkManager
from server.ecs.physics import can_apply_move, try_move

TILE = 16


class TestPhysics:
    def test_can_apply_move_empty_chunk(self):
        world = ChunkManager(tiles_per_chunk=16, tile_size=TILE)
        # no walls anywhere → any move passes
        assert can_apply_move(world, 0, 0, 1, 0) is True
        assert can_apply_move(world, 0, 0, 0, 1) is True
        assert can_apply_move(world, 100, 100, 1, 0) is True

    def test_can_apply_move_into_wall(self):
        world = ChunkManager(tiles_per_chunk=16, tile_size=TILE)
        # wall at tile (5, 5) = pixel (80, 80)
        world.get_chunk(0, 0).set_wall(5 * TILE, 5 * TILE)
        # from (64, 80) moving +1 tile → lands on wall at (80, 80) → blocked
        assert can_apply_move(world, 64, 80, 1, 0) is False
        # from (80, 64) moving +1 tile vertically → blocked
        assert can_apply_move(world, 80, 64, 0, 1) is False
        # to adjacent free tiles → passes
        assert can_apply_move(world, 64, 80, 0, 1) is True
        assert can_apply_move(world, 80, 64, 1, 0) is True

    def test_try_move_allowed(self):
        world = ChunkManager(tiles_per_chunk=16, tile_size=TILE)
        x, y = 100, 100
        new_x, new_y, moved = try_move(world, x, y, 1, 0)
        assert moved is True
        assert new_x == x + TILE
        assert new_y == y

    def test_try_move_blocked(self):
        world = ChunkManager(tiles_per_chunk=16, tile_size=TILE)
        world.get_chunk(0, 0).set_wall(5 * TILE, 5 * TILE)
        x, y = 64, 80  # adjacent to wall
        new_x, new_y, moved = try_move(world, x, y, 1, 0)
        assert moved is False
        assert new_x == x
        assert new_y == y
