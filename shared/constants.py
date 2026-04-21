# shared/constants.py
from enum import StrEnum


class MsgType(StrEnum):
    JOIN = "join"
    LEAVE = "leave"
    MOVE = "move"
    MOVE_NEAR = "move_near"
    CHAT = "chat"
    STATE_SYNC = "state_sync"


# Directions
DIR_NONE = (0, 0)
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_RIGHT = (1, 0)
DIR_LEFT = (-1, 0)

DIRS = {
    "up": DIR_UP,
    "down": DIR_DOWN,
    "left": DIR_LEFT,
    "right": DIR_RIGHT,
}

# Tiles
TILE_EMPTY = "."
TILE_WALL = "#"
TILE_PLAYER = "@"
