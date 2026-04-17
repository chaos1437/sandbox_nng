# tests/test_shared.py
import pytest
from shared.protocol import Message, encode, decode
from shared.constants import DIRS, TILE_EMPTY, TILE_WALL, TILE_PLAYER


class TestMessage:
    def test_to_dict_roundtrip(self):
        msg = Message(type="state_sync", seq=5, player_id="abc", payload={"x": 1})
        d = msg.to_dict()
        restored = Message.from_dict(d)
        assert restored.type == msg.type
        assert restored.seq == msg.seq
        assert restored.player_id == msg.player_id
        assert restored.payload == msg.payload

    def test_encode_decode_roundtrip(self):
        msg = Message(type="move", seq=10, player_id="xyz", payload={"dx": 1, "dy": 0})
        data = encode(msg)
        restored = decode(data)
        assert restored.type == msg.type
        assert restored.seq == msg.seq
        assert restored.player_id == msg.player_id
        assert restored.payload == msg.payload

    def test_from_dict_missing_optional_fields(self):
        d = {"type": "join"}
        msg = Message.from_dict(d)
        assert msg.type == "join"
        assert msg.seq == 0
        assert msg.player_id == ""
        assert msg.payload == {}


class TestConstants:
    def test_dirs_values(self):
        assert DIRS["up"] == (0, -1)
        assert DIRS["down"] == (0, 1)
        assert DIRS["right"] == (1, 0)
        assert DIRS["left"] == (-1, 0)

    def test_tile_chars(self):
        assert TILE_EMPTY == "."
        assert TILE_WALL == "#"
        assert TILE_PLAYER == "@"
