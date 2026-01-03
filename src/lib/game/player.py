from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

from src.core import Logger
from src.lib.game.event import GameEvent


class Player(ABC, Logger):

    logspace_part = "player"

    @abstractmethod
    async def ack_event(self, e: GameEvent) -> list[GameEvent]:
        """Acknowledge and potentially react to an event."""
        pass
