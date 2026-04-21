# shared/framing.py
"""Length-prefixed message framing for protocol.

Wire format: [4 bytes big-endian length][N bytes serialized payload]
"""

import struct
from shared.protocol import Message
from shared.serializers import Serializer

MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB max message size


def encode_message(msg: Message, serializer: Serializer) -> bytes:
    """Encode a single message with length prefix."""
    payload = serializer.encode(msg)
    return struct.pack(">I", len(payload)) + payload


def decode_message(data: bytes, serializer: Serializer) -> Message:
    """Decode a single message from length-prefixed data."""
    if len(data) < 4:
        raise ValueError("Data too short for length prefix")
    length = struct.unpack(">I", data[:4])[0]
    if length > MAX_MESSAGE_SIZE:
        raise ValueError(f"Message too large: {length} bytes (max {MAX_MESSAGE_SIZE})")
    if len(data) < 4 + length:
        raise ValueError(
            f"Data truncated: expected {length} bytes, got {len(data) - 4}"
        )
    payload = data[4 : 4 + length]
    return serializer.decode(payload)


def encode_messages(msgs: list[Message], serializer: Serializer) -> bytes:
    """Encode multiple messages sequentially."""
    return b"".join(encode_message(m, serializer) for m in msgs)


def decode_messages(data: bytes, serializer: Serializer):
    """Yield messages from sequential length-prefixed data."""
    offset = 0
    while offset < len(data):
        if offset + 4 > len(data):
            raise ValueError("Truncated length prefix at end of data")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        if length > MAX_MESSAGE_SIZE:
            raise ValueError(
                f"Message too large: {length} bytes (max {MAX_MESSAGE_SIZE})"
            )
        offset += 4
        if offset + length > len(data):
            raise ValueError(f"Truncated message body at offset {offset}")
        payload = data[offset : offset + length]
        yield serializer.decode(payload)
        offset += length


async def read_message(reader, serializer: Serializer) -> Message:
    """Read a single length-prefixed message from a stream."""
    header = await reader.readexactly(4)
    length = struct.unpack(">I", header)[0]
    if length > MAX_MESSAGE_SIZE:
        raise ValueError(f"Message too large: {length} bytes (max {MAX_MESSAGE_SIZE})")
    data = await reader.readexactly(length)
    return decode_message(header + data, serializer)


async def write_message(writer, msg: Message, serializer: Serializer) -> None:
    """Write a single length-prefixed message to a stream."""
    data = encode_message(msg, serializer)
    writer.write(data)
    await writer.drain()
