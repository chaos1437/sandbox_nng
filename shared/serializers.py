# shared/serializers.py
"""Serializer protocol and implementations. Swap JSON for protobuf."""

import json
from abc import ABC, abstractmethod
from shared.protocol import Message


class Serializer(ABC):
    """Abstract serializer for messages."""

    @abstractmethod
    def encode(self, msg: Message) -> bytes:
        """Encode Message to bytes."""
        raise NotImplementedError

    @abstractmethod
    def decode(self, data: bytes) -> Message:
        """Decode bytes to Message."""
        raise NotImplementedError


def encode(msg: Message) -> bytes:
    return JsonSerializer().encode(msg)


def decode(data: bytes) -> Message:
    return JsonSerializer().decode(data)


class JsonSerializer(Serializer):
    """JSON serializer using standard library json."""

    def encode(self, msg: Message) -> bytes:
        return json.dumps({
            "type": msg.type,
            "seq": msg.seq,
            "player_id": msg.player_id,
            "payload": msg.payload,
        }).encode("utf-8")

    def decode(self, data: bytes) -> Message:
        return Message.from_dict(json.loads(data.decode("utf-8")))
