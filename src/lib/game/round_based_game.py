from abc import abstractmethod

from src.lib.game.game import Game


class RoundBasedGame(Game):
    """A game where each round follows the same structure."""

    def _do_start(self):
        while True:
            self.round()

    def round(self):
        """Execute one round."""
        self.info("Beginning round.")
        self._do_round()

    @abstractmethod
    def _do_round(self): ...
