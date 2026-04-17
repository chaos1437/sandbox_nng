from typing import TypeVar, Type, Optional

from server.ecs.component import Component

C = TypeVar("C", bound=Component)


class Entity:
    """An ECS entity - an ID with a collection of components."""

    def __init__(self, entity_id: str) -> None:
        self.id = entity_id
        self.components: dict[Type[Component], Component] = {}

    def add_component(self, component: Component) -> None:
        """Add a component to this entity."""
        self.components[type(component)] = component

    def get_component(self, component_type: Type[C]) -> Optional[C]:
        """Get a component of the given type from this entity.

        Returns the component if found, None otherwise.
        """
        return self.components.get(component_type)
