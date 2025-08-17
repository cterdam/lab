from abc import ABC, abstractmethod
from enum import StrEnum
from functools import cached_property
from typing import Sequence, final

from transitions import EventData
from transitions.extensions.diagrams import HierarchicalGraphMachine

from src.core.log_level import LogLevel
from src.core.logger import Logger
from src.core.util import multiline


class FSM(ABC, Logger):
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

    When subclassing:
    - Implement `_fsm_state` and `_fsm_transitions` before init, so the `_fsm`
      controller can be initialized with the correct structure.
    """

    # FSM logging
    _fsm_lvl = LogLevel(name="FSM", no=6, color="#4A90E2")  # pyright:ignore

    class logmsg(StrEnum):  # pyright: ignore

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

    # Avoid creating another layer in log output
    logspace_part = None

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Make sure the logger has the FSM log level
        Logger.add_lvl(FSM._fsm_lvl)

        # Create FSM controller
        self._fsm = HierarchicalGraphMachine(
            states=self._fsm_states,
            transitions=self._fsm_transitions,
            initial=self._fsm_states[0],
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
        # Add depth to skip all transitions internals
        self._log.opt(depth=12).log(
            FSM._fsm_lvl.name,
            FSM.logmsg.FSM_STATE_CHANGE.format(
                source=event.transition.source,  # pyright:ignore
                dest=event.transition.dest,  # pyright:ignore
            ),
        )

    @property
    def _logtag(self) -> str:
        """Always display the current state alongside logid in logs."""
        return self._fsm.state

    @final
    def trig(self, *args, **kwargs):
        """Trigger state change."""
        return self._fsm.trigger(*args, **kwargs)

    @cached_property
    @abstractmethod
    def _fsm_states(self) -> Sequence:
        """Return all states for the initialization of this FSM in a sequence.

        The initial state must be at index 0.
        """
        ...

    @cached_property
    @abstractmethod
    def _fsm_transitions(self) -> Sequence:
        """Return all transitions for the initialization of this FSM."""
        ...
