# tests/test_client.py
import pytest
from client.state import ClientGameState
from client.input_handler import InputHandler


class TestClientGameState:
    def test_initial_state(self):
        s = ClientGameState()
        assert s.map == []
        assert s.my_player_id == ""
        assert s.server_seq == 0
        assert s.player_positions == {}

    def test_apply_state_sync_sets_positions(self):
        s = ClientGameState()
        s.apply_state_sync({
            "seq": 5,
            "players": {"p1": {"x": 10, "y": 20}}
        })
        assert s.server_seq == 5
        assert s.player_positions["p1"] == (10, 20)

    def test_apply_state_sync_with_map(self):
        s = ClientGameState()
        payload = {
            "seq": 1,
            "players": {"p1": {"x": 5, "y": 5}},
            "map": {
                "width": 40,
                "height": 20,
                "tiles": [["."] * 40 for _ in range(20)]
            }
        }
        s.apply_state_sync(payload)
        assert s.map_width == 40
        assert s.map_height == 20
        assert s.map != []

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


class TestInputHandler:
    def test_key_to_dir_mapping(self):
        resolved = {"up": 259, "down": 258, "left": 260, "right": 261, "quit": 113, "chat": 116}
        h = InputHandler(resolved)
        assert h.key_to_dir[259] == "up"
        assert h.key_to_dir[258] == "down"
        assert h.key_to_dir[260] == "left"
        assert h.key_to_dir[261] == "right"

    def test_get_direction(self):
        resolved = {"up": 259, "down": 258, "quit": 113, "chat": 116}
        h = InputHandler(resolved)
        assert h.get_direction(259) == "up"
        assert h.get_direction(999) is None

    def test_get_move_delta(self):
        resolved = {"up": 259, "down": 258, "chat": 116}
        h = InputHandler(resolved)
        assert h.get_move_delta("up") == (0, -1)
        assert h.get_move_delta("down") == (0, 1)
        assert h.get_move_delta("right") == (1, 0)
        assert h.get_move_delta("left") == (-1, 0)
        assert h.get_move_delta("unknown") == (0, 0)
