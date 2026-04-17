# shared/__init__.py
from shared.protocol import Message
from shared.serializers import Serializer, JsonSerializer, encode, decode
from shared.constants import (
    MsgType,
    DIRS,
    TILE_EMPTY,
    TILE_WALL,
    TILE_PLAYER,
)
