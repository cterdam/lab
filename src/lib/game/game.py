from abc import ABC, abstractmethod

from src.core import Logger, logid


class Game(ABC, Logger):

    logspace_part = "game"

    # Mapping from player's logid to player obj
    players: dict[logid, Logger]

    async def start(self):
        """Start the game."""
        self.info("Starting game.")
        await self._do_start()

    @abstractmethod
    async def _do_start(self): ...
