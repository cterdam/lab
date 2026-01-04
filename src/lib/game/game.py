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
    geid_t,
)
from src.lib.game.game_init_params import GameInitParams
from src.lib.game.game_state import GameStage, GameState
from src.lib.game.player import Player


class Game(Logger):
    """Async-safe event loop."""

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
        super().__init__(*args, logname=logname, **kwargs)

        self._state_lock = asyncio.Lock()
        self._state = GameState(
            max_react_per_event=params.max_react_per_event,
            max_successive_interrupt=params.max_successive_interrupt,
        )
        self.players = dict()

    def add_player(self, player: Player):
        self.players[player.logid] = player

    async def start(self):
        """Enter the event loop."""

        # Add GameStart event if needed
        async with self.state() as state:
            waiting = state.stage == GameStage.WAITING
        if waiting:
            await self._add_event(GameStart())

        ongoing = True
        while ongoing:
            # Add GameEnd event if needed
            try:
                e = await self._pop_event()
            except ValueError:
                await self._add_event(GameEnd())
                e = await self._pop_event()
            await self._process_event(e)
            async with self.state() as state:
                ongoing = state.stage == GameStage.ONGOING

    # EVENT PROCESSING #########################################################

    async def _process_event(self, e: GameEvent):
        """Process an event end-to-end.

        This includes both generic processing logic and event-specific handling.
        """

        # Gather tentative reacts
        e.stage = GameEventStage.TENTATIVE
        await self._record_event(e)
        await self._notify_event(e)

        # Start handling
        e.stage = GameEventStage.HANDLING
        await self._record_event(e)
        await self._handle_event(e)

        # Gather finishing reacts
        e.stage = GameEventStage.HANDLED
        await self._record_event(e)
        await self._notify_event(e)

        # Finalize record
        e.stage = GameEventStage.FINAL
        await self._record_event(e)

    async def _notify_event(self, e: GameEvent):
        """Notify an event to all visible players."""

        viewer2reacts = await self._send_notif(e)
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

    async def _send_notif(self, e: GameEvent) -> dict[logid, list[GameEvent]]:
        """Send notification of an event to players and collect reacts.

        Returns:
            A dict mapping each viewer logid to a list of their reacts.
        """

        # Determine if the event can still accept reacts
        async with self.state() as state:
            can_react = (
                state.max_react_per_event == -1
                or self._n_reacts_to_event(state.history, e.geid)
                < state.max_react_per_event
            )

        # Send notif
        viewer_logids = await self.event2viewers(e)
        tasks = [
            self.players[viewer_logid].ack_event(e, can_react=can_react)
            for viewer_logid in viewer_logids
        ]
        react_lists = await asyncio.gather(*tasks)
        if not can_react:
            react_lists = []

        # Validate any reacts
        viewer2reacts = dict(zip(viewer_logids, react_lists))
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
                async with self.state() as state:
                    can_interrupt = (
                        state.max_successive_interrupt == -1
                        or self._n_tail_interrupts(state.history)
                        < state.max_successive_interrupt
                    )
                if interrupts and can_interrupt:
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

        Returns: A list of selected reacts.
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

    def _n_tail_interrupts(self, history: list[GameEvent]) -> int:
        """Count distinct successive interrupts at the end of history.

        Finds the contiguous block of Interrupt events at the end of history,
        then counts distinct event IDs (geids) from that block.

        Args:
            history: The event history list to check.

        Returns:
            The number of distinct Interrupt events at the end of history.
        """
        interrupt_geids = set()
        for event in reversed(history):
            if isinstance(event, Interrupt):
                interrupt_geids.add(event.geid)
            else:
                break
        return len(interrupt_geids)

    def _n_reacts_to_event(self, history: list[GameEvent], target_geid: geid_t) -> int:
        """Count distinct reactions to a given event.

        Finds all events in history that react to the target event (i.e., have
        target_geid in their blocks field), then counts distinct reaction event IDs.

        Args:
            history: The event history list to check.
            target_geid: The geid of the event to count reactions for.

        Returns:
            The number of distinct reactions to the target event.
        """
        react_geids = set()
        for event in history:
            if target_geid in event.blocks:
                react_geids.add(event.geid)
        return len(react_geids)

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
        if not e.src:
            e.src = self.logid

        async with self.state() as state:
            heapq.heappush(
                state.event_queue,
                (state.default_event_priority, e.geid, e),
            )

    async def _pop_event(self) -> GameEvent:
        """Pop the next event from the queue.

        Returns:
            The next event to process.

        Raises:
            ValueError: If the queue is empty.
        """
        async with self.state() as state:
            if not state.event_queue:
                raise ValueError("Event queue is empty")
            _, _, event = heapq.heappop(state.event_queue)
        return event

    @log.input()
    async def _record_event(self, e: GameEvent):
        """Record the snapshot of an event in the game history.

        Args:
            e: The event to record.
        """
        async with self.state() as state:
            state.history.append(e.model_copy(deep=True))

    async def event2viewers(self, e: GameEvent) -> list[logid]:
        """Given an event, return the list of player logids who can see it."""
        if e.visible is None:
            return list(self.players.keys())
        else:
            return e.visible
