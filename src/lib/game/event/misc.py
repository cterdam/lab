from src.lib.game.event.game_event import GameEvent


class GameStart(GameEvent):
    """Event emitted when the game starts."""


class GameEnd(GameEvent):
    """Event emitted when the game ends."""
