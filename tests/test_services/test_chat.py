import pytest
from server.services.chat import ChatService
from server.services.join import JoinService
from server.state.world import GameWorldState
from shared.protocol import Message
from shared.constants import MsgType


class TestChatService:
    def setup_method(self):
        GameWorldState.reset()

    def _join_player(self, player_id: str = "p1") -> None:
        JoinService().handle(Message(type=MsgType.JOIN, player_id=player_id))

    # ── Basic chat ──────────────────────────────────────────────

    def test_chat_stores_message(self):
        self._join_player()
        svc = ChatService(max_lines=5, max_length=200)

        result = svc.handle(
            Message(type=MsgType.CHAT, player_id="p1", payload={"text": "Hello world"})
        )

        assert "chat" in result.payload
        assert result.payload["chat"][0]["text"] == "Hello world"
        assert result.payload["chat"][0]["player_id"] == "p1"

    def test_chat_increments_seq(self):
        self._join_player()
        svc = ChatService(max_lines=5, max_length=200)

        r1 = svc.handle(
            Message(type=MsgType.CHAT, player_id="p1", payload={"text": "a"})
        )
        r2 = svc.handle(
            Message(type=MsgType.CHAT, player_id="p1", payload={"text": "b"})
        )

        assert r2.payload["seq"] == r1.payload["seq"] + 1

    # ── Limits ───────────────────────────────────────────────────

    def test_chat_truncates_long_message(self):
        self._join_player()
        svc = ChatService(max_lines=5, max_length=10)

        result = svc.handle(
            Message(
                type=MsgType.CHAT,
                player_id="p1",
                payload={"text": "this is a very long message"},
            )
        )

        msg_text = result.payload["chat"][0]["text"]
        assert len(msg_text) == 10

    def test_chat_trims_to_max_lines(self):
        self._join_player()
        svc = ChatService(max_lines=3, max_length=200)

        for i in range(10):
            svc.handle(
                Message(type=MsgType.CHAT, player_id="p1", payload={"text": f"msg{i}"})
            )

        world = GameWorldState.get_instance()
        assert len(world.chat_messages) == 3
        # 10 messages (msg0..msg9) trimmed to last 3 → msg7 is the oldest (index 0)
        assert world.chat_messages[0].text == "msg7"

    # ── Edge cases ───────────────────────────────────────────────

    def test_chat_empty_text_ignored(self):
        self._join_player()
        world = GameWorldState.get_instance()
        seq_before = world.seq

        svc = ChatService(max_lines=5, max_length=200)
        result = svc.handle(
            Message(type=MsgType.CHAT, player_id="p1", payload={"text": "   "})
        )

        assert world.seq == seq_before

    def test_chat_whitespace_only_ignored(self):
        self._join_player()
        world = GameWorldState.get_instance()
        seq_before = world.seq

        svc = ChatService(max_lines=5, max_length=200)
        result = svc.handle(
            Message(type=MsgType.CHAT, player_id="p1", payload={"text": "\t\n"})
        )

        assert world.seq == seq_before
