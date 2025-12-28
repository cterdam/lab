import asyncio

from src.core import Logger, logid
from src.lib.game.event.event import Event
from src.lib.game.game_init_params import GameInitParams
from src.lib.game.player import Player


class Game(Logger):

    logspace_part = "game"

    # Mapping from player's logid to player obj
    players: dict[logid, Player]

    # Event queue
    _event_queue: asyncio.PriorityQueue[Event]

    def __init__(
        self,
        logname: str,
        params: GameInitParams,
        *args,
        **kwargs,
    ):
        """Initialize the game."""
        super().__init__(logname=logname, *args, **kwargs)
        self.debug(f"Initializing game: {params}")

        self.players = dict()
        self.params = params
        self._event_queue = asyncio.PriorityQueue()

    def add_player(self, player: Player):
        """Add a player."""
        self.info(f"Added player '{player.logid}'")
        self.players[player.logid] = player

    async def start(self):
        """Start the game."""
        self.info("Game starting")
        while True:
            event = await self._event_queue.get()
            await self._process_event(event)

    async def _process_event(self, e: Event):
        pass
