# server/map.py
from shared.constants import TILE_EMPTY, TILE_WALL

class GameMap:
    def __init__(self, width: int = 40, height: int = 20):
        self.width = width
        self.height = height
        # 2D grid, all empty by default
        self.tiles = [[TILE_EMPTY for _ in range(width)] for _ in range(height)]

    def set_wall(self, x: int, y: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.tiles[y][x] = TILE_WALL

    def is_passable(self, x: int, y: int) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.tiles[y][x] != TILE_WALL

    def to_lines(self) -> list[list[str]]:
        return [row[:] for row in self.tiles]
