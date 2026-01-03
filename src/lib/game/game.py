import asyncio
import heapq
import random
from contextlib import asynccontextmanager

from src import log
from src.core import Logger, logid
from src.core.util import multiline
from src.lib.game.event import (
    GameEnd,
    GameEvent,
    GameEventStage,
    GameStart,
    Interrupt,
    Speech,
)
from src.lib.game.game_init_params import GameInitParams
from src.lib.game.game_state import GameStage, GameState
from src.lib.game.player import Player


class Game(Logger):
    """Async-safe game."""

    logspace_part = "game"

    # Internal states
    _state_lock: asyncio.Lock
    _state: GameState

    # Mapping from player's logid to player obj
    players: dict[logid, Player]

    @asynccontextmanager
    async def state(self):
        """Context manager to access the game state.

        This is the public API for accessing game state. All state modifications
        should go through this context manager to ensure concurrency safety.

        Usage:
            async with self.state() as state:
                # Do something with state
        """
        async with self._state_lock:
            yield self._state

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

        self._state_lock = asyncio.Lock()
        self._state = GameState(
            stage=GameStage.WAITING,
            max_react_per_event=params.max_react_per_event,
            max_successive_interrupt=params.max_successive_interrupt,
        )
        self.players = dict()

    def add_player(self, player: Player):
        """Add a player and wire the event sink into it."""
        self.players[player.logid] = player

    async def start(self):
        """Enter the event loop."""
        async with self.state() as state:
            if state.stage == GameStage.WAITING:
                await self._add_event(GameStart())
        while True:
            async with self.state() as state:
                if state.stage != GameStage.ONGOING:
                    break
            e = await self._pop_event()
            await self._process_event(e)

    # EVENT PROCESSING #########################################################

    async def _process_event(self, e: GameEvent):
        """Process an event end-to-end.

        This includes both generic processing logic and event-specific handling.
        """

        # Gather tentative reacts
        e.stage = GameEventStage.TENTATIVE
        await self._record_event(e)
        await self._announce_event(e)

        # Start handling
        e.stage = GameEventStage.HANDLING
        await self._record_event(e)
        await self._handle_event(e)

        # Gather finishing reacts
        e.stage = GameEventStage.HANDLED
        await self._record_event(e)
        await self._announce_event(e)

        # Finalize record
        e.stage = GameEventStage.FINAL
        await self._record_event(e)

    async def _announce_event(self, e: GameEvent):
        """Announce an event to all visible players."""

        viewer2reacts = await self._collect_reacts(e)
        await self._process_reacts(e, viewer2reacts)

    async def _handle_event(self, e: GameEvent):
        """Pick a handler function for event-specific handling."""
        match e:
            case GameStart():
                await self._handle_GameStart(e)
            case GameEnd():
                await self._handle_GameEnd(e)
            case _:
                await self._handle_unknown(e)

    async def _collect_reacts(self, e: GameEvent) -> dict[logid, list[GameEvent]]:
        """Collect react events from eligible players.

        Returns:
            A dict mapping each viewer logid to a list of their reacts.
        """

        # Get reacts
        viewer_logids = await self.event2viewers(e)
        tasks = [
            self.players[viewer_logid].ack_event(e) for viewer_logid in viewer_logids
        ]
        react_lists = await asyncio.gather(*tasks)
        viewer2reacts = dict(zip(viewer_logids, react_lists))

        # Validate reacts
        for viewer_logid, reacts in viewer2reacts.items():
            for react in reacts:
                self._validate_react(e, react, viewer_logid)

        return viewer2reacts

    async def _process_reacts(
        self, e: GameEvent, viewer2reacts: dict[logid, list[GameEvent]]
    ) -> None:
        """Given an event and viewer reacts, select and process reacts.

        Args:
            e (GameEvent): The event invoking viewer reacts.
            viewer2reacts (dict): A mapping from each viewer's logid to a list
            of their react events.
        """

        match e:

            case Speech():
                interrupts = [
                    react
                    for reacts in viewer2reacts.values()
                    for react in reacts
                    if isinstance(react, Interrupt)
                ]
                if interrupts:
                    selected_interrupt = min(
                        interrupts, key=lambda i: len(i.target_speech_content)
                    )
                    e.content = selected_interrupt.target_speech_content
                    selected_reacts = [selected_interrupt]
                else:
                    selected_reacts = await self._sample_reacts(viewer2reacts)

            case _:
                selected_reacts = await self._sample_reacts(viewer2reacts)

        for react in selected_reacts:
            e.requires.append(react.geid)
            await self._process_event(react)

    async def _sample_reacts(
        self,
        viewer2reacts: dict[logid, list[GameEvent]],
    ) -> list[GameEvent]:
        """Select reacts based on the limit.

        Args:
            viewer2reacts: Mapping from viewer logid to their reacts.

        Returns:
            Selected reacts.
        """
        all_reacts = [react for reacts in viewer2reacts.values() for react in reacts]

        async with self.state() as state:
            max_react = state.max_react_per_event

        # Try selecting all
        if max_react == -1 or len(all_reacts) <= max_react:
            return all_reacts

        # Too many, try limiting to one per player
        one_per_player = []
        for reacts in viewer2reacts.values():
            if reacts:
                one_per_player.append(reacts[0])
        if len(one_per_player) <= max_react:
            return one_per_player

        # Still too many, sample from one per player
        return random.sample(one_per_player, max_react)

    # HANDLER FUNCS ############################################################

    async def _handle_GameStart(self, _: GameStart):
        async with self.state() as state:
            state.stage = GameStage.ONGOING
        self.info("Game starting")

    async def _handle_GameEnd(self, _: GameEnd):
        async with self.state() as state:
            state.stage = GameStage.ENDED
        self.info("Game ending")

    async def _handle_unknown(self, e: GameEvent):
        raise ValueError(f"Unknown event: {e}")

    # UTILS ####################################################################

    def _validate_react(
        self,
        e: GameEvent,
        react: GameEvent,
        viewer_logid: logid,
    ):
        """Validate that a react has correct fields.

        Args:
            event: The original event that the react is responding to.
            react: The react event to validate.
            viewer_logid: The logid of the player who returned this react.
        """

        assert react.src == viewer_logid, multiline(
            f"""
            React src mismatch:
            react.src={react.src} != player.logid={viewer_logid}
            """
        )
        assert e.geid in react.blocks, multiline(
            f"""
            React blocks mismatch:
            event.geid={e.geid} not in react.blocks={react.blocks}
            """
        )
        if isinstance(react, Interrupt):
            assert isinstance(e, Speech), multiline(
                f"""
                Interrupt can only react to Speech events:
                react is Interrupt but event is {type(e).__name__}
                """
            )
            assert e.content.startswith(react.target_speech_content), multiline(
                f"""
                Interrupt target_speech_content must be a prefix of original speech:
                event.content={e.content!r}
                interrupt.target_speech_content={react.target_speech_content!r}
                """
            )

    async def _add_event(self, e: GameEvent):
        """Add an event to the queue."""
        if e.src is None:
            e.src = self.logid
        async with self.state() as state:
            heapq.heappush(
                state.event_queue,
                (state.default_event_priority, e.geid, e),
            )

    async def _pop_event(self) -> GameEvent:
        """Pop the next event from the queue or get GameEnd."""
        async with self.state() as state:
            if len(state.event_queue) == 0:
                await self._add_event(GameEnd())
            _, _, event = heapq.heappop(state.event_queue)
            return event

    @log.input()
    async def _record_event(self, e: GameEvent):
        """Record the snapshot of an event in the game history."""
        async with self.state() as state:
            state.history.append(e.model_copy(deep=True))

    async def event2viewers(self, e: GameEvent) -> list[logid]:
        """Given an event, return the list of player logids who can see it."""
        if e.visible is None:
            return list(self.players.keys())
        else:
            return e.visible
