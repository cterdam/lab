from abc import ABC, abstractmethod
from functools import cached_property
from typing import Sequence, final

from transitions import EventData
from transitions.extensions.diagrams import HierarchicalGraphMachine

from src.core.logger import Logger
from src.core.util import multiline


class FSM(ABC, Logger):
    """Base class for finite-state machines.

    Descendants need to implement `_fsm_state` and `_fsm_transitions` before
    init, so the `_fsm` controller can be initialized with the correct
    structure.

    Descendants will automatically log a state graph and every state transition.
    """

    # FSM log level
    _FSM_LVL_NAME = "FSM"
    _FSM_LVL_NO = 6
    _FSM_LVL_COLOR = "#4A90E2"
    _FSM_INIT_MSG = multiline(
        """
        FSM created. Paste this block in Markdown to see the graph.
        ```mermaid
        {graphtxt}
        ```
        """,
        oneline=False,
    )
    _FSM_STATE_CHANGE_MSG = "[{source}] -> [{dest}]"

    _fsm_log_level_registered = False

    # Avoid creating another layer in log output
    logspace_part = None

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Make sure the underlying logger has the FSM log level
        if not FSM._fsm_log_level_registered:
            Logger.register_log_level(
                name=FSM._FSM_LVL_NAME,
                no=FSM._FSM_LVL_NO,
                color=FSM._FSM_LVL_COLOR,
            )
            FSM._fsm_log_level_registered = True

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
            FSM._FSM_LVL_NAME,
            FSM._FSM_INIT_MSG.format(graphtxt=self._fsm.get_graph().draw(None)),
        )

    def _log_state_change(self, event: EventData) -> None:
        """Automatically log state changes."""
        self._log.log(
            FSM._FSM_LVL_NAME,
            FSM._FSM_STATE_CHANGE_MSG.format(
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
