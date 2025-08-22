from abc import abstractmethod

from src.core.logger import Logger


class Game(Logger):

    logspace_part = "game"

    # Mapping from player's logid to player obj
    players: dict[str, Logger]

    @abstractmethod
    def start(self):
        """Start the game."""
        ...
