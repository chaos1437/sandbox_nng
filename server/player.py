# server/player.py
class Player:
    def __init__(self, player_id: str, x: int, y: int):
        self.player_id = player_id
        self.x = x
        self.y = y

    def move(self, dx: int, dy: int, game_map) -> bool:
        nx, ny = self.x + dx, self.y + dy
        if game_map.is_passable(nx, ny):
            self.x, self.y = nx, ny
            return True
        return False
