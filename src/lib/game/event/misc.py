from src.core.util import Lid
from src.lib.game.event.event import Event


class GameStart(Event):
    pass


class GameEnd(Event):
    pass


class AddPlayer(Event):
    player_lid: Lid


class AddAsset(Event):
    asset_lid: Lid
