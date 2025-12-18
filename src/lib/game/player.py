from src.core import Logger
from src.lib.game.action.speech import Speech


class Player(Logger):

    logspace_part = "player"

    async def _speak(self, speech: Speech):
        """Speak to other players in the game."""
        pass
