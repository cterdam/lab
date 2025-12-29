from src import log
from src.core import Logger, logid
from src.lib.data import PriorityQueue
from src.lib.game.event import Event, GameEnd, GameStart
from src.lib.game.game_config import GameConfig
from src.lib.game.game_init_params import GameInitParams
from src.lib.game.player import Player


class Game(Logger):

    logspace_part = "game"

    # Internal config
    cfg: GameConfig

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

        self.cfg = GameConfig(
            max_speech_per_event=params.max_speech_per_event,
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
        await self._eq.put(GameStart(src=self.logid))
        while True:
            e = await self._eq.get()
            await self._handle_event(e)
            if isinstance(e, GameEnd):
                break

    # - EVENT HANDLING ---------------------------------------------------------

    @log.input()
    async def _handle_event(self, e: Event):
        await self._do_handle_event(e)

    @log.input()
    async def _do_handle_event(self, e: Event):
        match e:
            case GameStart():
                await self._handle_GameStart(e)
            case GameEnd():
                await self._handle_GameEnd(e)
            case _:
                await self._handle_unknown_event(e)

    async def _handle_GameStart(self, e: GameStart):
        pass

    async def _handle_GameEnd(self, e: GameEnd):
        self.info("Game ending")

    async def _handle_unknown_event(self, e: Event):
        raise ValueError(f"Unknown event: {e}")
