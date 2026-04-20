# tests/test_entity.py
import pytest
from server.ecs.entity import Entity
from server.ecs.component import PositionComponent


class TestEntity:
    def test_add_component_sets_entity_id(self):
        e = Entity("player1")
        comp = PositionComponent(entity_id="player1", cell_x=10, cell_y=20)
        e.add_component(comp)
        assert comp.entity_id == "player1"

    def test_add_component_get_component(self):
        e = Entity("player1")
        comp = PositionComponent(entity_id="player1", cell_x=10, cell_y=20)
        e.add_component(comp)
        retrieved = e.get_component(PositionComponent)
        assert retrieved is comp
        assert retrieved.cell_x == 10
        assert retrieved.cell_y == 20

    def test_get_component_returns_none_for_missing_type(self):
        e = Entity("player1")
        result = e.get_component(PositionComponent)
        assert result is None

    def test_has_component_returns_true_when_present(self):
        e = Entity("player1")
        comp = PositionComponent(entity_id="player1", cell_x=10, cell_y=20)
        e.add_component(comp)
        assert e.has_component(PositionComponent) is True

    def test_has_component_returns_false_when_missing(self):
        e = Entity("player1")
        assert e.has_component(PositionComponent) is False

    def test_remove_component(self):
        e = Entity("player1")
        comp = PositionComponent(entity_id="player1", cell_x=10, cell_y=20)
        e.add_component(comp)
        assert e.has_component(PositionComponent) is True
        e.remove_component(PositionComponent)
        assert e.has_component(PositionComponent) is False
        assert e.get_component(PositionComponent) is None
