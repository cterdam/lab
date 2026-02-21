import asyncio
import heapq
import random
from contextlib import asynccontextmanager
from enum import StrEnum
from typing import AsyncIterator

from src import env, log
from src.core import Gid, Lid, Logger, group
from src.core.util import obj_subkey, toGid
from src.lib.game.event import (
    AddPlayer,
    Event,
    EventStage,
    GameEnd,
    GameStart,
    Interrupt,
    Speech,
)
from src.lib.game.game_init_params import GameInitParams
from src.lib.game.game_state import GameStage, GameState
from src.lib.game.player import Player


class Game(Logger):
    """Async-safe event loop."""

    logspace_part = "game"

    class _gona(StrEnum):
        ALL_PLAYERS = "all_players"

    # Mapping from player's lid to player object
    players: dict[Lid, Player]

    # The game state should contain enough information to reconstruct the game.
    # It should only be accessed via state(), not directly.
    _state_lock: asyncio.Lock
    _state: GameState

    @log.input()
    def __init__(
        self,
        params: GameInitParams,
        *args,
        logname: str = "game",
        **kwargs,
    ):
        super().__init__(*args, logname=logname, **kwargs)
        self.players = dict()
        self._state_lock = asyncio.Lock()
        self._state = GameState(
            max_react_per_event=params.max_react_per_event,
            max_successive_interrupt=params.max_successive_interrupt,
        )

    @asynccontextmanager
    async def state(self) -> AsyncIterator[GameState]:
        """Context manager to access the game state.

        This is the public API for accessing game state. All state modifications
        should go through this context manager to ensure concurrency safety.

        Usage:
            async with self.state() as state:
                # Do something with state
        """
        async with self._state_lock:
            yield self._state

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
                self.warning("Event queue drained, game ending")
                await self._add_event(GameEnd())
                e = await self._pop_event()
            await self._process_event(e)
            async with self.state() as state:
                ongoing = state.stage == GameStage.ONGOING

    async def add_player(self, player: Player):
        """Add a player to the game.

        If the game loop is already rolling, the event is enqueued.
        Otherwise, the event is processed immediately.
        """
        e = AddPlayer(player_lid=player.lid)

        async with self.state() as state:
            ongoing = state.stage == GameStage.ONGOING

        if ongoing:
            await self._add_event(e)
        else:
            await self._process_event(e)

    # EVENT PROCESSING #########################################################

    async def _process_event(self, e: Event):
        """Process an event end-to-end.

        This includes both generic processing logic and event-specific handling.
        """

        # Gather tentative reacts
        e.stage = EventStage.TENTATIVE
        await self._record_event(e)
        await self._notify_event(e)

        # Start handling
        e.stage = EventStage.HANDLING
        await self._record_event(e)
        await self._handle_event(e)

        # Gather finishing reacts
        e.stage = EventStage.HANDLED
        await self._record_event(e)
        await self._notify_event(e)

        # Finalize record
        e.stage = EventStage.FINAL
        await self._record_event(e)

    async def _notify_event(self, e: Event):
        """Notify an event to all visible players."""

        viewer2reacts = await self._send_notif(e)
        await self._process_reacts(e, viewer2reacts)

    async def _handle_event(self, e: Event):
        """Pick a handler function for event-specific handling."""
        match e:
            case AddPlayer():
                await self._handle_AddPlayer(e)
            case GameStart():
                await self._handle_GameStart(e)
            case GameEnd():
                await self._handle_GameEnd(e)
            case _:
                raise ValueError(f"Unknown event: {e}")

    async def _send_notif(self, e: Event) -> dict[Lid, list[Event]]:
        """Send notification of an event to players and collect valid reacts.

        Returns:
            A dict mapping each viewer lid to a list of their reacts. Note the
            list could be empty if the reacts returned by the viewer are all
            invalid and are filtered out.
        """

        # Determine the event's eligibility for reacts
        async with self.state() as state:
            can_react = state.max_react_per_event != 0
            can_interrupt = (
                state.max_successive_interrupt == -1
                or self._n_tail_interrupts(state.history)
                < state.max_successive_interrupt
            )

        # Send notif
        viewer_lids = await self.event2viewers(e)
        tasks = [
            self.players[viewer_lid].ack_event(
                e, can_react=can_react, can_interrupt=can_interrupt
            )
            for viewer_lid in viewer_lids
        ]
        react_lists = await asyncio.gather(*tasks)

        # Filter out wrong reacts
        filtered_reacts = []
        for viewer_lid, react_list in zip(viewer_lids, react_lists):
            filtered = []
            for react in react_list:
                if not can_react:
                    continue
                if react.src != viewer_lid:
                    continue
                if e.sid not in react.blocks:
                    continue
                if isinstance(react, Interrupt):
                    if not isinstance(e, Speech):
                        continue
                    if not can_interrupt:
                        continue
                    if not e.content.startswith(react.target_speech_content):
                        continue
                filtered.append(react)
            filtered_reacts.append(filtered)

        viewer2reacts = dict(zip(viewer_lids, filtered_reacts))
        return viewer2reacts

    async def _process_reacts(
        self, e: Event, viewer2reacts: dict[Lid, list[Event]]
    ) -> None:
        """Given an event and viewer reacts, select and process reacts.

        Args:
            e (GameEvent): The event invoking viewer reacts.
            viewer2reacts (dict): A mapping from each viewer's lid to a list
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
            e.requires.append(react.sid)
            await self._process_event(react)

    # HANDLER FUNCS ############################################################

    async def _handle_AddPlayer(self, e: AddPlayer):
        player = env.loggers[e.player_lid]
        self.players[player.lid] = player
        self.grpadd(self.gona.ALL_PLAYERS, player.lid)
        self.info(f"Added player: {player.lid}")

    async def _handle_GameStart(self, _: GameStart):
        async with self.state() as state:
            state.stage = GameStage.ONGOING
        self.info("Game starting")

    async def _handle_GameEnd(self, _: GameEnd):
        async with self.state() as state:
            state.stage = GameStage.ENDED
        self.info("Game ending")

    # OBJ GROUPING #############################################################

    def _getgid(self, name: str) -> Gid:
        """Derive the GID for a group."""
        return toGid(obj_subkey(self.lid, name))

    def grpadd(self, groupname: str, obj: Lid):
        """Add an obj to a group."""
        group.add(self._getgid(groupname), obj)

    def grprm(self, groupname: str, obj: Lid):
        """Remove an obj from a group."""
        group.rm(self._getgid(groupname), obj)

    # UTILS ####################################################################

    async def _sample_reacts(
        self,
        viewer2reacts: dict[Lid, list[Event]],
    ) -> list[Event]:
        """Select reacts based on the limit.

        Args:
            e: The event being reacted to.
            viewer2reacts: Mapping from viewer lid to their reacts.

        Returns: A list of selected reacts.
        """

        # Get the max number of reacts allowed
        async with self.state() as state:
            max_reacts = state.max_react_per_event

        # If no reactions allowed, return empty
        if max_reacts == 0:
            return []

        # Try selecting all
        all_reacts = [react for reacts in viewer2reacts.values() for react in reacts]
        if max_reacts == -1 or len(all_reacts) <= max_reacts:
            return all_reacts

        # Too many, try limiting to one per player
        one_per_player = [reacts[0] for reacts in viewer2reacts.values() if reacts]
        if len(one_per_player) <= max_reacts:
            return one_per_player

        # Still too many, sample from one per player
        return random.sample(one_per_player, max_reacts)

    def _n_tail_interrupts(self, history: list[Event]) -> int:
        """Count distinct successive interrupts at the end of history.

        Finds the contiguous block of Interrupt events at the end of history,
        then counts distinct events by sids from that block.

        Args:
            history: The event history list to check.

        Returns:
            The number of distinct Interrupt events at the end of history.
        """
        interrupt_sids = set()
        for event in reversed(history):
            if isinstance(event, Interrupt):
                interrupt_sids.add(event.sid)
            else:
                break
        return len(interrupt_sids)

    async def _add_event(self, e: Event):
        """Add an event to the queue."""
        if not e.src:
            e.src = self.lid

        async with self.state() as state:
            heapq.heappush(
                state.event_queue,
                (state.default_event_priority, e.sid, e),
            )

    async def _pop_event(self) -> Event:
        """Pop the next event from the queue.

        Returns:
            The next event to process.

        Raises:
            ValueError: If the queue is empty.
        """
        async with self.state() as state:
            if not state.event_queue:
                raise ValueError("Event queue empty")
            _, _, event = heapq.heappop(state.event_queue)

        return event

    @log.input()
    async def _record_event(self, e: Event):
        """Record the snapshot of an event in the game history.

        Args:
            e: The event to record.
        """
        async with self.state() as state:
            state.history.append(e.model_copy(deep=True))

    async def event2viewers(self, e: Event) -> list[Lid]:
        """Given an event, return the list of player lids who can see it."""
        if e.visible is None:
            return list(self.players.keys())
        else:
            return e.visible
