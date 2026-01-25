from enum import StrEnum
from typing import Sequence, final

from transitions import EventData, State
from transitions.extensions.diagrams import HierarchicalGraphMachine

from src.core.logger import Logger, LogLevel
from src.core.util import multiline


class FSM(Logger):
    """Base class for finite-state machines.

    Descendants own:

    - attributes:
        - _fsm (transitions HierarchicalGraphMachine):
            Underlying FSM controlling states and transitions.

    - methods:
        - trig
            Trigger a transition.

    Descendants will automatically log a state graph upon init and every state
    change upon calling triggers.
    """

    # Avoid creating another layer in log output
    logspace_part = None

    # FSM logging level
    _fsm_lvl = LogLevel(name="FSM", no=6, color="#4A90E2")  # type: ignore

    # Add depth to skip all transitions internals when logging
    _FSM_LOG_DEPTH_PAD = 12

    class logmsg(StrEnum):  # type: ignore

        FSM_INIT = multiline(
            """
            FSM created. Paste this block in Markdown to see the graph.
            ```mermaid
            {graphtxt}
            ```
            """,
            oneline=False,
        )

        FSM_STATE_CHANGE = "[{source}] -> [{dest}]"

    def __init__(
        self,
        fsm_states: Sequence[State],
        fsm_transitions: Sequence[dict],
        *args,
        **kwargs,
    ):
        """Initialize the FSM.

        The initial state must be at index 0 of fsm_states.
        """

        super().__init__(*args, **kwargs)

        # Make sure the logger has the FSM log level
        Logger.add_lvl(FSM._fsm_lvl)

        # Create FSM controller
        self._fsm = HierarchicalGraphMachine(
            states=fsm_states,
            transitions=fsm_transitions,
            initial=fsm_states[0],
            auto_transitions=False,
            ordered_transitions=False,
            ignore_invalid_triggers=False,
            before_state_change=self._log_state_change,
            send_event=True,
        )

        # Save graph txt repr of FSM structure
        self._log.log(
            FSM._fsm_lvl.name,
            FSM.logmsg.FSM_INIT.format(graphtxt=self._fsm.get_graph().draw(None)),
        )

    def _log_state_change(self, event: EventData) -> None:
        """Automatically log state changes."""
        self._log.opt(depth=FSM._FSM_LOG_DEPTH_PAD).log(
            FSM._fsm_lvl.name,
            FSM.logmsg.FSM_STATE_CHANGE.format(
                source=event.transition.source,  # type: ignore
                dest=event.transition.dest,  # type: ignore
            ),
        )

    @property
    def _logtag(self) -> str:
        """Always display the current state alongside lid in logs."""
        return self._fsm.state

    @final
    def trig(self, *args, **kwargs):
        """Trigger state change."""
        return self._fsm.trigger(*args, **kwargs)
