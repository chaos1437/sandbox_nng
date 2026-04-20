# tests/test_integration.py
"""Integration tests for multi-player server interactions."""
import asyncio
import subprocess
import sys
import time
from server.main import main as run_server
from server.registry import ConnectionRegistry
from shared.network import Connection
from shared.serializers import JsonSerializer
from shared.protocol import Message
from shared.constants import MsgType


def test_client_receives_other_player_move():
    """A moves → B receives broadcast without own action."""
    port = 9880

    # Start server with redirected output to prevent log corruption
    server_proc = subprocess.Popen(
        [sys.executable, '-m', 'server.main', '--port', str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.5)

    try:
        async def run():
            r1, w1 = await asyncio.open_connection('127.0.0.1', port)
            r2, w2 = await asyncio.open_connection('127.0.0.1', port)
            ser = JsonSerializer()

            # Client A joins and reads its JOIN response
            w1.write(ser.encode(Message(type=MsgType.JOIN, player_id='A', seq=0, payload={})) + b'\n')
            await w1.drain()
            resp1 = ser.decode((await r1.readline()).rstrip(b'\n'))
            assert resp1.type == MsgType.STATE_SYNC

            # Give tick_broadcast time to settle
            await asyncio.sleep(0.6)

            # Client B joins and reads its JOIN response
            w2.write(ser.encode(Message(type=MsgType.JOIN, player_id='B', seq=0, payload={})) + b'\n')
            await w2.drain()
            resp2 = ser.decode((await r2.readline()).rstrip(b'\n'))
            assert resp2.type == MsgType.STATE_SYNC

            # A moves
            w1.write(ser.encode(Message(type=MsgType.MOVE, player_id='A', seq=0, payload={'dx': 1, 'dy': 0})) + b'\n')
            await w1.drain()

            # Give server time to process MOVE and broadcast to B
            await asyncio.sleep(0.2)

            # Read all queued messages from B's perspective
            received = []
            for _ in range(10):
                try:
                    line = await asyncio.wait_for(r2.readline(), timeout=1.0)
                    if line:
                        received.append(ser.decode(line.rstrip(b'\n')))
                except asyncio.TimeoutError:
                    break

            state_syncs = [m for m in received if m.type == MsgType.STATE_SYNC]
            assert len(state_syncs) >= 1, f'No STATE_SYNC: {[m.type for m in received]}'

            latest = state_syncs[-1]
            players = latest.payload.get('players', {})
            assert 'A' in players, f'A not in players: {players}'
            # A spawns at center cell (20, 10), moves dx=1 → cell 21
            assert players['A']['x'] == 21, f'A.x expected 21, got {players["A"]["x"]}'

        asyncio.run(run())
    finally:
        server_proc.terminate()
        server_proc.wait(timeout=3)
