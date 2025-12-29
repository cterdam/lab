from src.lib.game.event.event import Event


class GameStart(Event):
    """Event emitted when the game starts."""


class GameEnd(Event):
    """Event emitted when the game ends."""
