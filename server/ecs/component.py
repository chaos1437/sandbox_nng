from dataclasses import dataclass


@dataclass
class Component:
    """Base class for ECS components.

    Components are pure data - they hold no behavior.
    Subclasses should define typed fields for their data.
    """
    entity_id: str
