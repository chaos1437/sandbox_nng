import pytest

from server.state.models import Player
from server.state.fov_manager import FOVManager


class TestFOVManager:
    @pytest.fixture
    def fov(self):
        return FOVManager(chunk_radius=1)

    # ── compute_fov ──────────────────────────────────────────────

    def test_compute_fov_returns_9_chunks_for_radius_1(self, fov):
        player = Player(id="p1", x=0, y=0)
        fov_chunks = fov.compute_fov(player)
        assert len(fov_chunks) == 9  # 3x3

    def test_compute_fov_centered_on_player_chunk(self, fov):
        player = Player(id="p1", x=50, y=50)
        fov_chunks = fov.compute_fov(player)
        assert (1, 1) in fov_chunks
        assert (0, 0) in fov_chunks
        assert (2, 2) in fov_chunks

    # ── update_fov ──────────────────────────────────────────────

    def test_update_fov_tracks_player(self, fov):
        p1 = Player(id="p1", x=0, y=0)
        p2 = Player(id="p2", x=200, y=200)
        fov.update_fov(p1)
        fov.update_fov(p2)
        assert len(fov._player_fov) == 2

    def test_update_fov_returns_fov_set(self, fov):
        player = Player(id="p1", x=0, y=0)
        result = fov.update_fov(player)
        assert len(result) == 9

    def test_update_fov_same_chunk_for_nearby_players(self, fov):
        p1 = Player(id="p1", x=0, y=0)
        p2 = Player(id="p2", x=10, y=10)
        f1 = fov.update_fov(p1)
        f2 = fov.update_fov(p2)
        assert f1 == f2

    def test_update_fov_detects_chunk_boundary_cross(self, fov):
        p1 = Player(id="p1", x=0, y=0)
        fov.update_fov(p1)
        p1.x = 33
        p1.y = 33
        old_fov, new_fov, crossed = fov.update_fov_with_delta(p1)
        assert crossed is True
        assert old_fov != new_fov

    def test_update_fov_no_boundary_cross(self, fov):
        p1 = Player(id="p1", x=0, y=0)
        fov.update_fov(p1)
        p1.x = 10
        p1.y = 10
        old_fov, new_fov, crossed = fov.update_fov_with_delta(p1)
        assert crossed is False
        assert old_fov == new_fov

    # ── get_players_in_chunks ────────────────────────────────────

    def test_get_players_in_chunks_returns_players(self, fov):
        p1 = Player(id="p1", x=0, y=0)
        p2 = Player(id="p2", x=200, y=200)
        fov.update_fov(p1)
        fov.update_fov(p2)
        result = fov.get_players_in_chunks({(0, 0), (0, 1), (1, 0)})
        assert "p1" in result
        assert "p2" not in result

    def test_get_players_in_chunks_empty_chunks(self, fov):
        result = fov.get_players_in_chunks({(0, 0)})
        assert len(result) == 0

    # ── should_send_to ──────────────────────────────────────────

    def test_should_send_to_true_when_fov_overlaps(self, fov):
        p1 = Player(id="p1", x=0, y=0)
        p2 = Player(id="p2", x=10, y=10)
        fov.update_fov(p1)
        fov.update_fov(p2)
        assert fov.should_send_to("p2", "p1") is True

    def test_should_send_to_false_when_fov_dont_overlap(self, fov):
        p1 = Player(id="p1", x=0, y=0)
        p2 = Player(id="p2", x=200, y=200)
        fov.update_fov(p1)
        fov.update_fov(p2)
        assert fov.should_send_to("p2", "p1") is False

    # ── get_player_chunk ───────────────────────────────────────

    def test_get_player_chunk(self, fov):
        player = Player(id="p1", x=100, y=100)
        assert fov.get_player_chunk(player) == (3, 3)
