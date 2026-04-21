# tests/test_integration/test_server_client.py
"""Integration tests for server-client connection."""

import asyncio
import pytest
from server.state.world import GameWorldState
from server.main import main as server_main
from client.network import NetworkClient
from shared.protocol import Message
from shared.constants import MsgType
from shared.framing import encode_message, read_message as framing_read_message
from shared.serializers import JsonSerializer


@pytest.fixture
def world():
    GameWorldState.reset()
    return GameWorldState.get_instance()


@pytest.fixture
async def server_port():
    import socket

    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


@pytest.mark.asyncio
async def test_server_starts_and_accepts_client(server_port):
    GameWorldState.reset()

    server = await asyncio.start_server(lambda r, w: None, "127.0.0.1", server_port)
    await server.started

    try:
        client = NetworkClient("127.0.0.1", server_port)
        connected = await client.connect()
        assert connected is True
        await client.disconnect()
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_client_can_join_and_receive_state(server_port):
    GameWorldState.reset()

    received = []

    async def handle_client(reader, writer):
        from server.network.handlers import ServiceRegistry
        from server.network.connections import Connections
        from server.state.world import get_world

        serializer = JsonSerializer()
        conn = type(
            "Conn",
            (),
            {
                "reader": reader,
                "writer": writer,
                "player_id": None,
                "is_alive": True,
                "addr": writer.get_extra_info("peername"),
                "send": lambda msg: writer.write(encode_message(msg, serializer)),
                "close": lambda: writer.close(),
                "wait_closed": lambda: writer.wait_closed(),
            },
        )()

        msg = await framing_read_message(reader, serializer)
        if msg and msg.type == "join":
            from server.services.join import JoinService

            svc = JoinService()
            resp = svc.handle(msg)
            conn.player_id = resp.player_id
            await conn.send(resp)

    server = await asyncio.start_server(handle_client, "127.0.0.1", server_port)
    await server.started

    try:
        client = NetworkClient("127.0.0.1", server_port)
        await client.connect()

        join_msg = Message(type=MsgType.JOIN, player_id="", payload={})
        await client.send(join_msg)

        msg = await asyncio.wait_for(client.incoming.get(), timeout=3.0)
        assert msg.type == MsgType.STATE_SYNC
        assert msg.player_id != ""

        await client.disconnect()
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_client_receives_chunk_data_on_join(server_port):
    GameWorldState.reset()

    async def handle_client(reader, writer):
        from server.services.join import JoinService

        serializer = JsonSerializer()
        msg = await framing_read_message(reader, serializer)
        if msg and msg.type == "join":
            svc = JoinService()
            resp = svc.handle(msg, suggested_id="test_player")
            await writer.write(encode_message(resp, serializer))
            await writer.drain()

    server = await asyncio.start_server(handle_client, "127.0.0.1", server_port)
    await server.started

    try:
        client = NetworkClient("127.0.0.1", server_port)
        await client.connect()

        join_msg = Message(type=MsgType.JOIN, player_id="test_player", payload={})
        await client.send(join_msg)

        msg = await asyncio.wait_for(client.incoming.get(), timeout=3.0)
        assert msg.type == MsgType.STATE_SYNC
        assert "full_chunks" in msg.payload
        assert "deltas" in msg.payload
        assert len(msg.payload["full_chunks"]) > 0

        await client.disconnect()
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_client_can_send_move_and_receive_near(server_port):
    GameWorldState.reset()

    async def handle_client(reader, writer):
        from server.services.join import JoinService
        from server.services.move import MoveService
        from shared.constants import MsgType

        serializer = JsonSerializer()
        msg = await framing_read_message(reader, serializer)
        if msg.type == "join":
            svc = JoinService()
            resp = svc.handle(msg, suggested_id="p1")
            await writer.write(encode_message(resp, serializer))
            await writer.drain()
        elif msg.type == "move":
            svc = MoveService(max_speed_tiles_per_sec=100.0)
            resp = svc.handle(msg)
            await writer.write(encode_message(resp, serializer))
            await writer.drain()

    server = await asyncio.start_server(handle_client, "127.0.0.1", server_port)
    await server.started

    try:
        client = NetworkClient("127.0.0.1", server_port)
        await client.connect()

        join_msg = Message(type=MsgType.JOIN, player_id="p1", payload={})
        await client.send(join_msg)
        await asyncio.wait_for(client.incoming.get(), timeout=3.0)

        move_msg = Message(
            type=MsgType.MOVE, player_id="p1", payload={"dx": 1, "dy": 0}
        )
        await client.send(move_msg)

        msg = await asyncio.wait_for(client.incoming.get(), timeout=3.0)
        assert msg.type == MsgType.MOVE_NEAR
        assert "mover_id" in msg.payload

        await client.disconnect()
    finally:
        server.close()
        await server.wait_closed()
