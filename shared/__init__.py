# shared/__init__.py
from shared.protocol import Message, encode, decode
from shared.serializers import Serializer, JsonSerializer
from shared.constants import (
    MsgType,
    DIRS,
    TILE_EMPTY,
    TILE_WALL,
    TILE_PLAYER,
)
