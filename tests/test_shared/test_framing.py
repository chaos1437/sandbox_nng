# tests/test_shared/test_framing.py
"""Tests for length-prefixed message framing."""

import pytest
from shared.protocol import Message
from shared.constants import MsgType
from shared.serializers import JsonSerializer
from shared.framing import (
    encode_message,
    decode_message,
    encode_messages,
    decode_messages,
)


class TestLengthPrefixFraming:
    def test_encode_message_adds_4byte_length_prefix(self):
        msg = Message(type=MsgType.JOIN, seq=1, player_id="p1", payload={})
        serializer = JsonSerializer()
        data = encode_message(msg, serializer)
        assert len(data) >= 5
        assert data[:4] == len(data[4:]).to_bytes(4, "big")

    def test_decode_message_strips_length_prefix(self):
        msg = Message(type=MsgType.JOIN, seq=1, player_id="p1", payload={})
        serializer = JsonSerializer()
        data = encode_message(msg, serializer)
        restored = decode_message(data, serializer)
        assert restored.type == MsgType.JOIN
        assert restored.seq == 1
        assert restored.player_id == "p1"

    def test_roundtrip_join_message(self):
        original = Message(type=MsgType.JOIN, seq=0, player_id="", payload={})
        serializer = JsonSerializer()
        data = encode_message(original, serializer)
        restored = decode_message(data, serializer)
        assert restored.type == original.type
        assert restored.seq == original.seq
        assert restored.player_id == original.player_id
        assert restored.payload == original.payload

    def test_roundtrip_move_message(self):
        original = Message(
            type=MsgType.MOVE, seq=5, player_id="abc", payload={"dx": 1, "dy": 0}
        )
        serializer = JsonSerializer()
        data = encode_message(original, serializer)
        restored = decode_message(data, serializer)
        assert restored.type == MsgType.MOVE
        assert restored.payload == {"dx": 1, "dy": 0}

    def test_roundtrip_large_payload(self):
        original = Message(
            type=MsgType.STATE_SYNC,
            seq=1,
            player_id="p1",
            payload={
                "full_chunks": [
                    {"cx": i, "cy": i, "tiles": [["."] * 32 for _ in range(32)]}
                    for i in range(9)
                ]
            },
        )
        serializer = JsonSerializer()
        data = encode_message(original, serializer)
        assert len(data) > 10000
        restored = decode_message(data, serializer)
        assert restored.type == MsgType.STATE_SYNC
        assert len(restored.payload["full_chunks"]) == 9

    def test_encode_decode_single_message(self):
        msg = Message(
            type=MsgType.CHAT, seq=2, player_id="user", payload={"text": "hello"}
        )
        serializer = JsonSerializer()
        data = encode_message(msg, serializer)
        restored = decode_message(data, serializer)
        assert restored.payload["text"] == "hello"

    def test_decode_truncated_raises(self):
        import struct

        serializer = JsonSerializer()

        with pytest.raises(Exception):
            decode_message(b"\x00\x00\x00\x05hello", serializer)

    def test_decode_empty_raises(self):
        import struct

        serializer = JsonSerializer()

        with pytest.raises(Exception):
            decode_message(b"", serializer)


class TestMultiMessage:
    def test_encode_messages_multiple(self):
        msgs = [
            Message(type=MsgType.JOIN, seq=1, player_id="p1", payload={}),
            Message(type=MsgType.MOVE, seq=2, player_id="p1", payload={"dx": 1}),
        ]
        serializer = JsonSerializer()
        data = encode_messages(msgs, serializer)
        restored = list(decode_messages(data, serializer))
        assert len(restored) == 2
        assert restored[0].type == MsgType.JOIN
        assert restored[1].type == MsgType.MOVE

    def test_encode_messages_empty(self):
        serializer = JsonSerializer()
        data = encode_messages([], serializer)
        assert data == b""
        restored = list(decode_messages(data, serializer))
        assert restored == []
