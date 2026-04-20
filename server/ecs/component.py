from dataclasses import dataclass

__all__ = ["Component", "PositionComponent"]


@dataclass
class Component:
    """Base class for ECS components.

    Components are pure data - they hold no behavior.
    Subclasses should define typed fields for their data.
    """
    entity_id: str = ""


@dataclass
class PositionComponent(Component):
    """Component holding a grid cell position (cell_x, cell_y)."""
    cell_x: int = 0
    cell_y: int = 0
