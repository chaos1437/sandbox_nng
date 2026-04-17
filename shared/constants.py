# shared/constants.py
PROTOCOL_VERSION = "0.1.0"

# Directions for movement
DIR_NONE = (0, 0)
DIR_NORTH = (0, -1)
DIR_SOUTH = (0, 1)
DIR_EAST  = (1, 0)
DIR_WEST  = (-1, 0)

DIRS = {
    "up":    DIR_NORTH,
    "down":  DIR_SOUTH,
    "left":  DIR_WEST,
    "right": DIR_EAST,
}

# Tile types (ASCII chars)
TILE_EMPTY  = "."
TILE_WALL   = "#"
TILE_PLAYER = "@"

# Message types
MSG_JOIN        = "join"
MSG_LEAVE       = "leave"
MSG_MOVE        = "move"
MSG_STATE_SYNC  = "state_sync"
