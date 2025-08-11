from functools import cached_property

from src.core import FSM
from src.core.logger import Logger


class Game(FSM):

    logspace_part = "game"

    # Mapping from player's logid to player obj
    players: dict[str, Logger]

    @cached_property
    def _fsm_states(self):
        return ["A", "B"]

    @cached_property
    def _fsm_transitions(self):
        return [["normal", "A", "B"], ["again", "B", "A"]]
