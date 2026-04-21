import pytest
import tempfile
import shutil
from pathlib import Path

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

    # ── Map (chunk-based) ───────────────────────────────────────

    def test_is_passable_empty(self):
        world = GameWorldState()
        assert world.is_passable(0, 0) is True
        assert world.is_passable(100, 100) is True

    def test_is_passable_wall(self):
        world = GameWorldState()
        world.set_wall(5, 5)
        assert world.is_passable(5, 5) is False

    def test_is_passable_out_of_world(self):
        world = GameWorldState(world_cx=2, world_cy=2)
        assert world.is_passable(-1, 0) is False
        assert world.is_passable(64, 0) is False

    def test_set_wall_sets_dirty(self):
        world = GameWorldState()
        world.set_wall(5, 5)
        dirty = world.chunk_manager.get_dirty_chunks()
        assert len(dirty) == 1

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

    # ── State snapshot ───────────────────────────────────────────

    def test_get_state_snapshot_no_map(self):
        world = GameWorldState()
        world.add_player(Player(id="p1", x=3, y=4))
        snap = world.get_state_snapshot(include_map=False)
        assert "players" in snap
        assert "map" not in snap
        assert snap["players"]["p1"] == {"x": 3, "y": 4}

    def test_get_state_snapshot_with_map(self):
        world = GameWorldState()
        snap = world.get_state_snapshot(include_map=True)
        assert "map" in snap
        assert snap["map"]["chunk_size"] == 32
        assert snap["map"]["world_cx"] == 16
        assert snap["map"]["world_cy"] == 16
        tiles = snap["map"]["tiles"]
        assert len(tiles) == 32
        assert len(tiles[0]) == 32

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

    # ── Chunk Manager integration ───────────────────────────────

    def test_world_uses_chunk_manager(self):
        world = GameWorldState()
        assert world.chunk_manager is not None

    def test_chunk_manager_has_world_name(self):
        world = GameWorldState(world_name="myworld")
        assert world.chunk_manager.world_name == "myworld"

    def test_chunk_manager_has_correct_size(self):
        world = GameWorldState(world_cx=8, world_cy=8)
        assert world.chunk_manager.world_cx == 8
        assert world.chunk_manager.world_cy == 8

    # ── Flush ────────────────────────────────────────────────────

    def test_flush_flushes_dirty_chunks(self):
        world = GameWorldState()
        world.set_wall(5, 5)
        world.flush()
        chunk = world.chunk_manager.get_chunk(0, 0)
        assert chunk.dirty is False

    # ── World with temp directory ──────────────────────────────

    def test_world_with_temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        try:
            world = GameWorldState(world_name="test", world_dir=temp_dir)
            world.set_wall(10, 10)
            world.flush()

            chunk_file = Path(temp_dir) / "test" / "chunks" / "0_0.json"
            assert chunk_file.exists()
        finally:
            shutil.rmtree(temp_dir)
