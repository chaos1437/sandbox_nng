# tests/test_shared/test_framing.py
"""Tests for length-prefixed message framing."""

import pytest
from shared.protocol import Message
from shared.constants import MsgType
from shared.framing import (
    encode_message,
    decode_message,
    encode_messages,
    decode_messages,
)


class TestLengthPrefixFraming:
    def test_encode_message_adds_4byte_length_prefix(self):
        msg = Message(type=MsgType.JOIN, seq=1, player_id="p1", payload={})
        data = encode_message(msg)
        assert len(data) >= 5
        assert data[:4] == len(data[4:]).to_bytes(4, "big")

    def test_decode_message_strips_length_prefix(self):
        msg = Message(type=MsgType.JOIN, seq=1, player_id="p1", payload={})
        data = encode_message(msg)
        restored = decode_message(data)
        assert restored.type == MsgType.JOIN
        assert restored.seq == 1
        assert restored.player_id == "p1"

    def test_roundtrip_join_message(self):
        original = Message(type=MsgType.JOIN, seq=0, player_id="", payload={})
        data = encode_message(original)
        restored = decode_message(data)
        assert restored.type == original.type
        assert restored.seq == original.seq
        assert restored.player_id == original.player_id
        assert restored.payload == original.payload

    def test_roundtrip_move_message(self):
        original = Message(
            type=MsgType.MOVE, seq=5, player_id="abc", payload={"dx": 1, "dy": 0}
        )
        data = encode_message(original)
        restored = decode_message(data)
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
        data = encode_message(original)
        assert len(data) > 10000
        restored = decode_message(data)
        assert restored.type == MsgType.STATE_SYNC
        assert len(restored.payload["full_chunks"]) == 9

    def test_encode_decode_single_message(self):
        msg = Message(
            type=MsgType.CHAT, seq=2, player_id="user", payload={"text": "hello"}
        )
        data = encode_message(msg)
        restored = decode_message(data)
        assert restored.payload["text"] == "hello"

    def test_decode_truncated_raises(self):
        import struct

        with pytest.raises(Exception):
            decode_message(b"\x00\x00\x00\x05hello")

    def test_decode_empty_raises(self):
        with pytest.raises(Exception):
            decode_message(b"")


class TestMultiMessage:
    def test_encode_messages_multiple(self):
        msgs = [
            Message(type=MsgType.JOIN, seq=1, player_id="p1", payload={}),
            Message(type=MsgType.MOVE, seq=2, player_id="p1", payload={"dx": 1}),
        ]
        data = encode_messages(msgs)
        restored = list(decode_messages(data))
        assert len(restored) == 2
        assert restored[0].type == MsgType.JOIN
        assert restored[1].type == MsgType.MOVE

    def test_encode_messages_empty(self):
        data = encode_messages([])
        assert data == b""
        restored = list(decode_messages(data))
        assert restored == []
