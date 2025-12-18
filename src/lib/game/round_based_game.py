from abc import abstractmethod

from src.lib.game.game import Game


class RoundBasedGame(Game):
    """A game where each round follows the same structure."""

    async def _do_start(self):
        while True:
            await self.round()

    async def round(self):
        """Execute one round."""
        self.info("Beginning round.")
        await self._do_round()

    @abstractmethod
    async def _do_round(self): ...
