# shared/framing.py
"""Length-prefixed message framing for protocol.

Wire format: [4 bytes big-endian length][N bytes JSON]
"""

import json
import struct
from shared.protocol import Message
from shared.constants import MsgType


def encode_message(msg: Message) -> bytes:
    """Encode a single message with length prefix."""
    payload = json.dumps(
        {
            "type": msg.type.value if isinstance(msg.type, MsgType) else msg.type,
            "seq": msg.seq,
            "player_id": msg.player_id,
            "payload": msg.payload,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    return struct.pack(">I", len(payload)) + payload


def decode_message(data: bytes) -> Message:
    """Decode a single message from length-prefixed data."""
    if len(data) < 4:
        raise ValueError("Data too short for length prefix")
    length = struct.unpack(">I", data[:4])[0]
    if len(data) < 4 + length:
        raise ValueError(
            f"Data truncated: expected {length} bytes, got {len(data) - 4}"
        )
    payload = json.loads(data[4 : 4 + length].decode("utf-8"))
    return Message.from_dict(payload)


def encode_messages(msgs: list[Message]) -> bytes:
    """Encode multiple messages sequentially."""
    return b"".join(encode_message(m) for m in msgs)


def decode_messages(data: bytes):
    """Yield messages from sequential length-prefixed data."""
    offset = 0
    while offset < len(data):
        if offset + 4 > len(data):
            raise ValueError("Truncated length prefix at end of data")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        offset += 4
        if offset + length > len(data):
            raise ValueError(f"Truncated message body at offset {offset}")
        payload = json.loads(data[offset : offset + length].decode("utf-8"))
        yield Message.from_dict(payload)
        offset += length


async def read_message(reader, writer) -> Message:
    """Read a single length-prefixed message from a stream."""
    header = await reader.readexactly(4)
    length = struct.unpack(">I", header)[0]
    data = await reader.readexactly(length)
    return decode_message(header + data)


async def write_message(writer, msg: Message) -> None:
    """Write a single length-prefixed message to a stream."""
    data = encode_message(msg)
    writer.write(data)
    await writer.drain()
