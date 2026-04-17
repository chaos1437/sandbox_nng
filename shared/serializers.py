# shared/serializers.py
"""Serializer protocol and implementations. Swap JSON for protobuf."""

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


class JsonSerializer(Serializer):
    """JSON serializer using standard library json."""

    def encode(self, msg: Message) -> bytes:
        import json
        return json.dumps(msg.to_dict()).encode("utf-8")

    def decode(self, data: bytes) -> Message:
        import json
        return Message.from_dict(json.loads(data.decode("utf-8")))
