from abc import ABC, abstractmethod

from pydantic import PositiveInt

from src.core import Logger


class Game(ABC, Logger):
    """Base class for turn-based games."""

    logspace_part = "game"

    # GAME METHODS #############################################################

    def turn(self, n: PositiveInt):
        """Execute the nth turn."""
        self._do_turn(n)

    @abstractmethod
    def _do_turn(self, n: PositiveInt):
        pass

    def start(self):
        """Start the game."""
        self._do_start()

    @abstractmethod
    def _do_start(self):
        pass

    def end(self):
        """End the game."""
        self._do_end()

    @abstractmethod
    def _do_end(self):
        pass
