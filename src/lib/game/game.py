import asyncio
import random

from src import log
from src.core import Logger, logid
from src.core.util import multiline
from src.lib.data import PriorityQueue
from src.lib.game.event import GameEnd, GameEvent, GameStart, Interrupt, Speech
from src.lib.game.game_init_params import GameInitParams
from src.lib.game.game_state import GameState
from src.lib.game.player import Player


class Game(Logger):

    logspace_part = "game"

    # Internal states
    state: GameState

    # Mapping from player's logid to player obj
    players: dict[logid, Player]

    # Event queue
    _eq: PriorityQueue
    PRIO = 10

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
            max_successive_interrupt=params.max_successive_interrupt,
        )
        self.players = dict()
        self._eq = PriorityQueue(logname=f"{logname}_eq")

    @log.input()
    def add_player(self, player: Player):
        """Add a player and wire the event sink into it."""
        self.players[player.logid] = player

    async def start(self):
        """Start the game."""
        self.info("Game starting")
        await self._enq(GameStart(src=self.logid))
        while self.state.ongoing:
            _, _, e = await self._eq.get()
            await self._process_event(e)

    # EVENT PROCESSING #########################################################

    @log.input()
    async def _process_event(self, e: GameEvent):
        """Process an event end-to-end.

        This includes both generic processing logic and event-specific handling.
        """
        await self._announce_event_tentative(e)
        await self._handle_event(e)
        await self._announce_event_finalized(e)

    async def _handle_event(self, e: GameEvent):
        """Pick a handler function for event-specific handling."""
        match e:
            case GameStart():
                await self._handle_GameStart(e)
            case GameEnd():
                await self._handle_GameEnd(e)
            case _:
                await self._handle_unknown(e)

    async def _announce_event_tentative(self, e: GameEvent):
        """Announce an event to all visible players before it is handled."""

        viewer2reactions = await self._collect_reactions(e)
        await self._process_reactions(e, viewer2reactions)

    async def _announce_event_finalized(self, e: GameEvent):
        """Announce an event to all visible players after it is handled."""
        viewers = await self.event2viewers(e)
        tasks = []
        for player_logid, player in self.players.items():
            if player_logid in viewers:
                tasks.append(player.ack_event_finalized(e))
        await asyncio.gather(*tasks)

    async def _collect_reactions(self, e: GameEvent) -> dict[logid, list[GameEvent]]:
        """Collect reaction events from eligible players.

        Returns:
            A dict mapping each viewer logid to a list of their reactions.
        """

        # Get reactions
        viewer_logids = await self.event2viewers(e)
        tasks = [
            self.players[viewer_logid].ack_event_tentative(e)
            for viewer_logid in viewer_logids
        ]
        reaction_lists = await asyncio.gather(*tasks)

        # Validate reactions
        viewer2reactions = dict(zip(viewer_logids, reaction_lists))
        for viewer_logid, reactions in viewer2reactions.items():
            for reaction in reactions:
                self._validate_reaction(e, reaction, viewer_logid)

        return viewer2reactions

    async def _process_reactions(
        self, e: GameEvent, viewer2reactions: dict[logid, list[GameEvent]]
    ) -> None:
        """Given an event and viewer reactions, select and process reactions.

        Args:
            e (GameEvent): The event invoking viewer reactions.
            viewer2reactions (dict): A mapping from each viewer's logid to a
                list of their reaction events.
        """

        all_reactions = [
            reaction for reactions in reaction_lists for reaction in reactions
        ]

        match e:

            case Speech():

                # Categorize reactions
                interrupts, speeches, other_reactions = [], [], []
                for reaction in all_reactions:
                    if isinstance(reaction, Interrupt):
                        interrupts.append(reaction)
                    elif isinstance(reaction, Speech):
                        speeches.append(reaction)
                    else:
                        other_reactions.append(reaction)

                # Process interrupts or speeches
                if interrupts:
                    # Choose minimal interrupt
                    selected_interrupt = min(
                        interrupts, key=lambda i: len(i.target_speech_content)
                    )
                    e.content = selected_interrupt.target_speech_content
                    e.requires.append(selected_interrupt.geid)
                    await self._process_event(selected_interrupt)
                elif speeches:
                    # Choose 1 speech, discard the rest
                    selected_speech = random.choice(speeches)
                    e.requires.append(selected_speech.geid)
                    await self._process_event(selected_speech)

                # Process all other reactions regardless
                for reaction in other_reactions:
                    e.requires.append(reaction.geid)
                    await self._process_event(reaction)

            case _:
                max_react = self.state.max_react_per_event
                if max_react == -1 or len(all_reactions) <= max_react:
                    selected_reactions = all_reactions
                else:
                    one_per_player = []
                    for reactions in viewer2reactions.values():
                        if reactions:
                            one_per_player.append(reactions[0])
                    if len(one_per_player) <= max_react:
                        selected_reactions = one_per_player
                    else:
                        random.shuffle(one_per_player)
                        selected_reactions = one_per_player[:max_react]
                for reaction in selected_reactions:
                    await self._process_event(reaction)

    # HANDLER FUNCS ############################################################

    async def _handle_GameStart(self, _: GameStart):
        pass

    async def _handle_GameEnd(self, _: GameEnd):
        self.state.ongoing = False
        self.info("Game ending")

    async def _handle_unknown(self, e: GameEvent):
        raise ValueError(f"Unknown event: {e}")

    # UTILS ####################################################################

    def _validate_reaction(
        self,
        e: GameEvent,
        reaction: GameEvent,
        viewer_logid: logid,
    ):
        """Validate that a reaction has correct fields.

        Args:
            event: The original event that the reaction is responding to.
            reaction: The reaction event to validate.
            viewer_logid: The logid of the player who returned this reaction.
        """

        assert reaction.src == viewer_logid, multiline(
            f"""
            Reaction src mismatch:
            reaction.src={reaction.src} != player.logid={viewer_logid}
            """
        )

        assert e.geid in reaction.blocks, multiline(
            f"""
            Reaction blocks mismatch:
            event.geid={e.geid} not in reaction.blocks={reaction.blocks}
            """
        )

        if isinstance(reaction, Interrupt):
            assert isinstance(e, Speech), multiline(
                f"""
                Interrupt can only react to Speech events:
                reaction is Interrupt but event is {type(e).__name__}
                """
            )
            assert e.content.startswith(reaction.target_speech_content), multiline(
                f"""
                Interrupt target_speech_content must be a prefix of original speech:
                event.content={e.content!r}
                interrupt.target_speech_content={reaction.target_speech_content!r}
                """
            )

    async def _enq(self, e: GameEvent):
        """Enqueue an event."""
        await self._eq.put((Game.PRIO, e.geid, e))

    async def event2viewers(self, e: GameEvent) -> list[logid]:
        """Given an event, return the list of player logids who can see it."""
        if e.visible is None:
            return list(self.players.keys())
        else:
            return e.visible
