# tests/test_chat_system.py
import pytest
from server.ecs.systems.chat import ChatSystem


class TestChatSystem:
    def test_stores_message(self, world):
        chat = ChatSystem()
        world.register_system(chat)

        chat.on_chat(world, "player1", "hello")

        assert len(chat._messages) == 1
        assert chat._messages[0].player_id == "player1"
        assert chat._messages[0].text == "hello"

    def test_trims_to_last_5(self, world):
        chat = ChatSystem()
        world.register_system(chat)

        for i in range(7):
            chat.on_chat(world, f"player{i}", f"msg{i}")

        assert len(chat._messages) == 5
        assert chat._messages[0].text == "msg2"

    def test_ignores_empty_text(self, world):
        chat = ChatSystem()
        world.register_system(chat)

        chat.on_chat(world, "player1", "   ")

        assert len(chat._messages) == 0

    def test_truncates_long_messages(self, world):
        chat = ChatSystem()
        world.register_system(chat)

        long_text = "x" * 300
        chat.on_chat(world, "player1", long_text)

        assert len(chat._messages[0].text) == 200
