# server/network/connections.py
import asyncio
from shared.network import Connection
from shared.protocol import Message
from shared.logging import setup_logger

log = setup_logger(__name__, "server.log", console=False)

__all__ = ["Connections"]


class Connections:
    def __init__(self):
        self._connections: list[Connection] = []

    def add(self, conn: Connection):
        self._connections.append(conn)
        log.info(f"Client connected: {conn.addr}")

    def remove(self, conn: Connection):
        self._connections.remove(conn)
        if conn.player_id:
            log.info(f"Client disconnected: {conn.addr}")

    async def broadcast(self, msg: Message):
        alive = []
        for conn in self._connections:
            if conn.is_alive:
                try:
                    await conn.send(msg)
                    alive.append(conn)
                except Exception:
                    conn.close()
            else:
                conn.close()
        self._connections = alive
        return self._connections

    def by_player(self, player_id: str) -> Connection | None:
        for conn in self._connections:
            if conn.player_id == player_id:
                return conn
        return None

    def all(self) -> list[Connection]:
        return list(self._connections)
