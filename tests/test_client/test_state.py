# tests/test_client/test_state.py
import pytest
from client.state import ClientGameState


class TestClientGameState:
    def test_initial_state(self):
        s = ClientGameState()
        assert s.chunks == {}
        assert s.my_player_id == ""
        assert s.server_seq == 0
        assert s.player_positions == {}

    def test_apply_state_sync_sets_positions(self):
        s = ClientGameState()
        s.apply_state_sync({"seq": 5, "players": {"p1": {"x": 10, "y": 20}}})
        assert s.server_seq == 5
        assert s.player_positions["p1"] == (10, 20)

    def test_apply_state_sync_with_full_chunks(self):
        s = ClientGameState()
        s.chunk_size = 32
        payload = {
            "seq": 1,
            "players": {"p1": {"x": 5, "y": 5}},
            "full_chunks": [
                {"cx": 0, "cy": 0, "tiles": [["."] * 32 for _ in range(32)]}
            ],
            "deltas": [],
        }
        s.apply_state_sync(payload)
        assert "0,0" in s.chunks

    def test_apply_state_sync_with_deltas(self):
        s = ClientGameState()
        s.chunk_size = 32
        s.chunks["0,0"] = [["."] * 32 for _ in range(32)]
        payload = {
            "seq": 2,
            "players": {},
            "full_chunks": [],
            "deltas": [[0, 0, "#"], [1, 1, "#"]],
        }
        s.apply_state_sync(payload)
        assert s.chunks["0,0"][0][0] == "#"
        assert s.chunks["0,0"][1][1] == "#"

    def test_get_tile(self):
        s = ClientGameState()
        s.chunk_size = 32
        s.chunks["0,0"] = [["#"] * 32 for _ in range(32)]
        assert s.get_tile(0, 0) == "#"
        assert s.get_tile(31, 31) == "#"
        assert s.get_tile(32, 0) is None

    def test_set_player_id(self):
        s = ClientGameState()
        s.set_player_id("abc")
        assert s.my_player_id == "abc"

    def test_get_my_position_not_set(self):
        s = ClientGameState()
        assert s.get_my_position() is None

    def test_get_my_position_set(self):
        s = ClientGameState()
        s.player_positions = {"p1": (10, 20)}
        s.set_player_id("p1")
        assert s.get_my_position() == (10, 20)
