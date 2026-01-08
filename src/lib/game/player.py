from abc import ABC, abstractmethod

from src.core import Logger
from src.lib.game.event import Event


class Player(ABC, Logger):

    logspace_part = "player"

    @abstractmethod
    async def ack_event(
        self, e: Event, *, can_react: bool, can_interrupt: bool
    ) -> list[Event]:
        """Acknowledge and potentially react to an event.

        Args:
            e: The event to acknowledge.
            can_react: Whether the event can still accept reactions. If False,
                the player should not return any reaction events.
            can_interrupt: Whether interrupts are allowed. This is only True for
                Speech events that can still accept interrupts. If False, the
                player should not return any Interrupt events.
        """
        pass
