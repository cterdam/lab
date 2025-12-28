from abc import ABC, abstractmethod

from src.core import Logger, logid
from src.lib.game.event.speech import Interrupt, Speech


class Player(ABC, Logger):

    logspace_part = "player"

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
