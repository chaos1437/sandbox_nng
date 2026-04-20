# tests/test_component.py
import pytest
from server.ecs.component import Component, PositionComponent


class TestPositionComponent:
    def test_has_correct_cell_fields(self):
        pos = PositionComponent(entity_id="", cell_x=5, cell_y=10)
        assert pos.cell_x == 5
        assert pos.cell_y == 10
        assert pos.entity_id == ""

    def test_entity_id_is_settable(self):
        pos = PositionComponent(entity_id="", cell_x=5, cell_y=10)
        pos.entity_id = "new_id"
        assert pos.entity_id == "new_id"
