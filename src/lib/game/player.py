from abc import ABC, abstractmethod

from src.core import Logger, logid
from src.lib.game.event import GameEvent, Interrupt, Speech


class Player(ABC, Logger):

    logspace_part = "player"

    @abstractmethod
    async def ack_event_before(self, e: GameEvent):
        """Acknowledge an event before it is handled."""
        pass

    @abstractmethod
    async def ack_event_after(self, e: GameEvent):
        """Acknowledge an event after it is handled."""
        pass

    async def speak(self, audience: list[logid], content: str):
        """Speak to other players in the game."""
        pass

    @abstractmethod
    async def hear(self, speech: Speech | Interrupt):
        """Hear another player's speech from the game."""
        pass

    @abstractmethod
    async def consider(self, speech: Speech | Interrupt) -> Interrupt | None:
        """Consider some speech and potentially decide to interrupt.

        Speech content received through this method is tentative, because it
        could be interrupted by other players as well.
        """
        pass
