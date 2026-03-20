from typing import Any

from pydantic import Field

from src.core import Dataclass
from src.core.util import multiline


class RNGInitParams(Dataclass):
    """Initialization params for a random number generator.

    This is the sole configuration object for ``RNG.__init__`` (besides
    ``logname``). The optional ``seed`` makes runs reproducible.
    ``pool`` pre-loads items for sampling without replacement — the
    fundamental operation behind a deck of cards.
    """

    seed: int | None = Field(
        default=None,
        description=multiline("""
            Seed for the underlying PRNG. When set, all operations are
            deterministic. When None, the PRNG is seeded from system
            entropy.
        """),
    )

    pool: list[Any] | None = Field(
        default=None,
        description=multiline("""
            Initial pool of items for draw-without-replacement operations.
            Items are copied on construction. When None, draw operations
            are unavailable until load() is called.
        """),
    )
