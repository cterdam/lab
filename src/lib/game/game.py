from abc import ABC, abstractmethod

from src.core import Logger


class Game(ABC, Logger):

    logspace_part = "game"

    # Mapping from player's logid to player obj
    players: dict[str, Logger]

    def start(self):
        """Start the game."""
        self.info("Starting game.")
        self._do_start()

    @abstractmethod
    def _do_start(self): ...
