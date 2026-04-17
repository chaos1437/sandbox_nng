from abc import ABC


class System(ABC):
    """Abstract base class for ECS systems.

    Systems contain the behavior/logic layer of the game engine.
    They receive lifecycle hooks and can be queried by the world.
    """

    def on_player_join(self, world, player_id: str) -> None:
        """Called when a player joins the game."""
        pass

    def on_before_move(self, world, player_id: str, dx: int, dy: int) -> bool:
        """Called before a player moves.

        Args:
            world: The game world.
            player_id: The ID of the player moving.
            dx: Delta x of the move.
            dy: Delta y of the move.

        Returns:
            True to allow the move, False to block it.
        """
        return True

    def on_after_move(self, world, player_id: str, dx: int, dy: int) -> None:
        """Called after a player moves.

        Args:
            world: The game world.
            player_id: The ID of the player who moved.
            dx: Delta x of the move.
            dy: Delta y of the move.
        """
        pass

    def on_player_leave(self, world, player_id: str) -> None:
        """Called when a player leaves the game."""
        pass

    def update(self, world) -> None:
        """Called every game tick."""
        pass
