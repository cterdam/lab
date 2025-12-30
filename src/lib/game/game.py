import asyncio
from enum import IntEnum

from src import log
from src.core import Logger, logid
from src.lib.data import PriorityQueue
from src.lib.game.event import GameEnd, GameEvent, GameStart
from src.lib.game.game_init_params import GameInitParams
from src.lib.game.game_state import GameState
from src.lib.game.player import Player


class Game(Logger):

    logspace_part = "game"

    class prio(IntEnum):
        REACT = 0
        NORMAL = 10

    # Internal states
    state: GameState

    # Mapping from player's logid to player obj
    players: dict[logid, Player]

    # Event queue
    _eq: PriorityQueue

    @log.input()
    def __init__(
        self,
        params: GameInitParams,
        *args,
        logname: str = "game",
        **kwargs,
    ):
        """Initialize the game."""
        super().__init__(*args, logname=logname, **kwargs)

        self.state = GameState(
            ongoing=True,
            max_react_per_event=params.max_react_per_event,
            max_interrupt_per_speech=params.max_interrupt_per_speech,
        )
        self.players = dict()
        self._eq = PriorityQueue(logname=f"{logname}_eq")

    @log.input()
    def add_player(self, player: Player):
        """Add a player."""
        self.players[player.logid] = player

    async def start(self):
        """Start the game."""
        self.info("Game starting")

        game_start = GameStart(src=self.logid)
        await self._eq.put(
            (
                Game.prio.NORMAL,
                game_start.event_id,
                game_start,
            )
        )

        while self.state.ongoing:
            _, _, e = await self._eq.get()
            if e.announce_before:
                await self._announce_event_before(e)
            await self._handle_event(e)
            if e.announce_after:
                await self._announce_event_after(e)

    # EVENT HANDLING ###########################################################

    async def _announce_event_before(self, e: GameEvent):
        """Announce an event to all visible players before it is handled."""
        audience = await self.event2audience(e)
        tasks = []
        for player_logid, player in self.players.items():
            if player_logid in audience:
                tasks.append(player.ack_event_before(e))
        await asyncio.gather(*tasks)

    async def _announce_event_after(self, e: GameEvent):
        """Announce an event to all visible players after it is handled."""
        audience = await self.event2audience(e)
        tasks = []
        for player_logid, player in self.players.items():
            if player_logid in audience:
                tasks.append(player.ack_event_after(e))
        await asyncio.gather(*tasks)

    @log.input()
    async def _handle_event(self, e: GameEvent):
        """Handle an event."""
        match e:
            case GameStart():
                await self._handle_GameStart(e)
            case GameEnd():
                await self._handle_GameEnd(e)
            case _:
                await self._handle_unknown(e)

    async def _handle_GameStart(self, _: GameStart):
        pass

    async def _handle_GameEnd(self, _: GameEnd):
        self.state.ongoing = False
        self.info("Game ending")

    async def _handle_unknown(self, e: GameEvent):
        raise ValueError(f"Unknown event: {e}")

    # UTILS ####################################################################

    async def event2audience(self, e: GameEvent) -> list[logid]:
        """Given an event, return the list of player logids who can see it."""
        if e.visible is None:
            return list(self.players.keys())
        else:
            return e.visible
