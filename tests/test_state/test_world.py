import pytest
from server.state.world import GameWorldState, get_world
from server.state.models import Player, ChatMessage


class TestGameWorldState:
    def setup_method(self):
        GameWorldState.reset()

    # ── Singleton ────────────────────────────────────────────────

    def test_singleton_get_instance(self):
        w1 = GameWorldState.get_instance()
        w2 = GameWorldState.get_instance()
        assert w1 is w2

    def test_reset_clears_singleton(self):
        w1 = GameWorldState.get_instance()
        GameWorldState.reset()
        w2 = GameWorldState.get_instance()
        assert w1 is not w2

    # ── Player management ────────────────────────────────────────

    def test_add_player(self):
        world = GameWorldState()
        player = Player(id="p1", x=5, y=10)
        world.add_player(player)
        assert world.get_player("p1") is player

    def test_remove_player(self):
        world = GameWorldState()
        player = Player(id="p1", x=5, y=10)
        world.add_player(player)
        world.remove_player("p1")
        assert world.get_player("p1") is None

    def test_get_player_not_found(self):
        world = GameWorldState()
        assert world.get_player("ghost") is None

    # ── Map ─────────────────────────────────────────────────────

    def test_is_passable_empty(self):
        world = GameWorldState(width=10, height=10)
        assert world.is_passable(0, 0) is True
        assert world.is_passable(9, 9) is True

    def test_is_passable_wall(self):
        world = GameWorldState(width=10, height=10)
        world.set_wall(5, 5)
        assert world.is_passable(5, 5) is False

    def test_is_passable_out_of_bounds(self):
        world = GameWorldState(width=10, height=10)
        assert world.is_passable(-1, 0) is False
        assert world.is_passable(0, 10) is False
        assert world.is_passable(10, 0) is False

    # ── Chat ─────────────────────────────────────────────────────

    def test_add_chat_message(self):
        world = GameWorldState()
        msg = ChatMessage(player_id="p1", text="hello")
        world.add_chat_message(msg, max_lines=5)
        assert len(world.chat_messages) == 1
        assert world.chat_messages[0].text == "hello"

    def test_add_chat_message_trims(self):
        world = GameWorldState()
        for i in range(10):
            world.add_chat_message(
                ChatMessage(player_id=f"p{i}", text=f"msg{i}"), max_lines=5
            )
        assert len(world.chat_messages) == 5
        assert world.chat_messages[0].text == "msg5"

    # ── State snapshot ──────────────────────────────────────────

    def test_get_state_snapshot_no_map(self):
        world = GameWorldState(width=10, height=10)
        world.add_player(Player(id="p1", x=3, y=4))
        snap = world.get_state_snapshot(include_map=False)
        assert "players" in snap
        assert "map" not in snap
        assert snap["players"]["p1"] == {"x": 3, "y": 4}

    def test_get_state_snapshot_with_map(self):
        world = GameWorldState(width=3, height=2)
        world.set_wall(1, 0)
        snap = world.get_state_snapshot(include_map=True)
        assert "map" in snap
        assert snap["map"]["width"] == 3
        assert snap["map"]["height"] == 2
        tiles = snap["map"]["tiles"]
        assert tiles[0][1] == "#"
        assert tiles[0][0] == "."

    def test_get_state_snapshot_with_chat(self):
        world = GameWorldState()
        world.add_chat_message(ChatMessage(player_id="p1", text="hi"), max_lines=5)
        snap = world.get_state_snapshot()
        assert "chat" in snap
        assert snap["chat"][0]["text"] == "hi"

    def test_get_state_snapshot_seq_increments(self):
        world = GameWorldState()
        s1 = world.get_state_snapshot()
        world.seq += 1
        s2 = world.get_state_snapshot()
        assert s2["seq"] == 1
        assert s1["seq"] == 0
