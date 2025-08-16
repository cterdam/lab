from abc import ABC, abstractmethod
from functools import cached_property
from typing import Sequence

from transitions.extensions.diagrams import HierarchicalGraphMachine

from src.core.logger import Logger
from src.core.util import multiline


class FSM(ABC, Logger):
    """Base class for finite-state machines."""

    # Avoid creating another layer in log output
    logspace_part = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fsm = HierarchicalGraphMachine(
            states=self._fsm_states,
            transitions=self._fsm_transitions,
            initial=self._fsm_states[0],
            auto_transitions=False,
            ordered_transitions=False,
            ignore_invalid_triggers=False,
        )
        self.info(
            multiline(
                """
                FSM created. Paste this block in Markdown to see the graph.
                ```mermaid
                {graphtxt}
                ```
                """,
                oneline=False,
            ).format(graphtxt=self._fsm.get_graph().draw(None))
        )

    @property
    def _logtag(self) -> str:
        """Always display the current state alongside logid in logs."""
        return self._fsm.state

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
