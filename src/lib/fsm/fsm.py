from src.core import Logger


class Fsm(Logger):
    """Base class for finite-state machines."""

    # Do not create another layer in log output
    logspace_part = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
