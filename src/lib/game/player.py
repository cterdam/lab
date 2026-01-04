from abc import ABC, abstractmethod

from src.core import Logger
from src.lib.game.event import GameEvent


class Player(ABC, Logger):

    logspace_part = "player"

    @abstractmethod
    async def ack_event(self, e: GameEvent, *, can_react: bool) -> list[GameEvent]:
        """Acknowledge and potentially react to an event.

        Args:
            e: The event to acknowledge.
            can_react: Whether the event can still accept reactions. If False,
                the player should not return any reaction events.
        """
        pass
