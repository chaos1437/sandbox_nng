from dataclasses import dataclass

__all__ = ["Component"]


@dataclass(frozen=True)
class Component:
    """Base class for ECS components.

    Components are pure data - they hold no behavior.
    Subclasses should define typed fields for their data.
    """
    entity_id: str
