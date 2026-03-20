import random as _random
from collections.abc import Sequence
from enum import StrEnum
from typing import Any

from src import env, log
from src.core import Logger
from src.core.util import obj_id
from src.lib.rng.rng_init_params import RNGInitParams


class RNG(Logger):
    """A seeded random number generator with draw-without-replacement.

    Wraps Python's ``random.Random`` with logging, counters, and a
    built-in item pool for draw-without-replacement workflows. The pool
    is the fundamental primitive behind a deck of cards: load items,
    draw them one at a time (or in batches), and reshuffle when needed.

    Pool operations
    ~~~~~~~~~~~~~~~
    ``load(items)`` replaces the current pool and shuffles it.
    ``draw()`` removes and returns the top item from the pool.
    ``draw(n)`` removes and returns the top *n* items.
    ``remaining`` is the number of undrawn items.
    ``reshuffle()`` restores the pool to its full original contents
    and reshuffles.

    Plain random operations
    ~~~~~~~~~~~~~~~~~~~~~~~
    ``randint(a, b)`` returns a random integer in ``[a, b]``.
    ``uniform(a, b)`` returns a random float in ``[a, b]``.
    ``choice(seq)`` picks a random element from a non-empty sequence.
    ``sample(seq, k)`` picks *k* unique elements from a sequence.
    ``shuffle(seq)`` shuffles a mutable sequence in place.

    Error handling
    ~~~~~~~~~~~~~~
    Drawing from an empty or exhausted pool is a no-op: it logs a
    warning and increments ``ERR_POOL_EMPTY`` rather than raising.
    This matches the Graph convention of graceful degradation.

    Reproducibility
    ~~~~~~~~~~~~~~~
    When ``params.seed`` is set, all operations are deterministic.
    The seed is recorded at construction time and can be reapplied
    via ``reseed()``.

    Subclasses
    ~~~~~~~~~~
    ``Deck``, ``Coin``, and ``Dice`` extend this class with
    domain-specific methods (``deal()``, ``flip()``, ``roll()``),
    validation, and dedicated log spaces.
    """

    logspace_part = "rng"

    class _coke(StrEnum):
        DRAW = "draw"
        RESHUFFLE = "reshuffle"
        LOAD = "load"
        RANDINT = "randint"
        UNIFORM = "uniform"
        CHOICE = "choice"
        SAMPLE = "sample"
        SHUFFLE = "shuffle"
        ERR_POOL_EMPTY = obj_id(env.ERR_COKE_PREFIX, "pool_empty")
        ERR_POOL_NOT_LOADED = obj_id(env.ERR_COKE_PREFIX, "pool_not_loaded")
        ERR_DRAW_TOO_MANY = obj_id(env.ERR_COKE_PREFIX, "draw_too_many")
        ERR_EMPTY_SEQ = obj_id(env.ERR_COKE_PREFIX, "empty_seq")

    class _logmsg(StrEnum):
        INIT = "RNG created: seed={seed}"
        POOL_LOADED = "Pool loaded: {n} items"
        DRAW_ONE = "Drew 1 item ({remaining} remaining)"
        DRAW_MANY = "Drew {n} items ({remaining} remaining)"
        RESHUFFLE = "Pool reshuffled: {n} items"

    _rng: _random.Random
    _params: RNGInitParams

    # The original pool contents (for reshuffle)
    _pool_source: list[Any] | None

    # The current draw pile (items are popped from the end)
    _pool: list[Any] | None

    @log.input()
    def __init__(
        self,
        params: RNGInitParams,
        *args,
        logname: str = "rng",
        **kwargs,
    ):
        super().__init__(*args, logname=logname, **kwargs)
        self._params = params
        self._rng = _random.Random(params.seed)
        self._pool_source = None
        self._pool = None

        if params.pool is not None:
            self.load(params.pool)

        self.info(self._logmsg_seed())

    # PROPERTIES ###############################################################

    @property
    def _logtag(self) -> str:
        if self._pool is not None:
            return f"{len(self._pool)}p"
        return "no pool"

    @property
    def remaining(self) -> int:
        """Number of items left in the draw pile."""
        if self._pool is None:
            return 0
        return len(self._pool)

    @property
    def pool_size(self) -> int:
        """Total size of the full pool (before any draws)."""
        if self._pool_source is None:
            return 0
        return len(self._pool_source)

    @property
    def seed(self) -> int | None:
        """The seed used for this RNG, or None if unseeded."""
        return self._params.seed

    # POOL OPERATIONS ##########################################################

    @log.input()
    def load(self, items: Sequence[Any]) -> None:
        """Replace the pool with a copy of *items* and shuffle it.

        Args:
            items: Sequence of items to load into the pool.
        """
        self._pool_source = list(items)
        self._pool = list(items)
        self._rng.shuffle(self._pool)
        self.incr(self.coke.LOAD)
        self.debug(self.logmsg.POOL_LOADED.format(n=len(self._pool)))

    def draw(self, n: int = 1) -> Any | list[Any] | None:
        """Draw item(s) from the pool without replacement.

        Args:
            n: Number of items to draw. Defaults to 1.

        Returns:
            A single item when ``n=1``, a list when ``n>1``,
            or ``None`` if the pool is empty or not loaded.
        """
        if self._pool is None:
            self.incr(self.coke.ERR_POOL_NOT_LOADED)
            self.warning("Cannot draw: pool not loaded")
            return None

        if len(self._pool) == 0:
            self.incr(self.coke.ERR_POOL_EMPTY)
            self.warning("Cannot draw: pool is empty")
            return None

        if n > len(self._pool):
            self.incr(self.coke.ERR_DRAW_TOO_MANY)
            self.warning(
                f"Cannot draw {n} items: only {len(self._pool)} remaining"
            )
            return None

        if n == 1:
            item = self._pool.pop()
            self.incr(self.coke.DRAW)
            self.trace(
                self.logmsg.DRAW_ONE.format(remaining=len(self._pool))
            )
            return item

        drawn = [self._pool.pop() for _ in range(n)]
        self.incr(self.coke.DRAW, n)
        self.trace(
            self.logmsg.DRAW_MANY.format(n=n, remaining=len(self._pool))
        )
        return drawn

    @log.input()
    def reshuffle(self) -> None:
        """Restore the pool to its full original contents and reshuffle."""
        if self._pool_source is None:
            self.incr(self.coke.ERR_POOL_NOT_LOADED)
            self.warning("Cannot reshuffle: pool not loaded")
            return
        self._pool = list(self._pool_source)
        self._rng.shuffle(self._pool)
        self.incr(self.coke.RESHUFFLE)
        self.debug(self.logmsg.RESHUFFLE.format(n=len(self._pool)))

    # PLAIN RANDOM OPERATIONS ##################################################

    def randint(self, a: int, b: int) -> int:
        """Return a random integer N such that a <= N <= b."""
        result = self._rng.randint(a, b)
        self.incr(self.coke.RANDINT)
        return result

    def uniform(self, a: float, b: float) -> float:
        """Return a random float N such that a <= N <= b."""
        result = self._rng.uniform(a, b)
        self.incr(self.coke.UNIFORM)
        return result

    def choice(self, seq: Sequence[Any]) -> Any | None:
        """Pick a random element from a non-empty sequence.

        Returns None and logs a warning if the sequence is empty.
        """
        if not seq:
            self.incr(self.coke.ERR_EMPTY_SEQ)
            self.warning("Cannot choose from empty sequence")
            return None
        result = self._rng.choice(seq)
        self.incr(self.coke.CHOICE)
        return result

    def sample(self, seq: Sequence[Any], k: int) -> list[Any] | None:
        """Pick *k* unique elements from a sequence.

        Returns None and logs a warning if *k* exceeds the sequence length.
        """
        if k > len(seq):
            self.incr(self.coke.ERR_EMPTY_SEQ)
            self.warning(
                f"Cannot sample {k} items from sequence of length {len(seq)}"
            )
            return None
        result = self._rng.sample(list(seq), k)
        self.incr(self.coke.SAMPLE)
        return result

    def shuffle(self, seq: list[Any]) -> None:
        """Shuffle a mutable sequence in place."""
        self._rng.shuffle(seq)
        self.incr(self.coke.SHUFFLE)

    # SEED MANAGEMENT ##########################################################

    def reseed(self, seed: int | None = None) -> None:
        """Re-seed the PRNG.

        Args:
            seed: New seed. If None, uses the original seed from params.
        """
        s = seed if seed is not None else self._params.seed
        self._rng.seed(s)
        self.info(self._logmsg_seed(s))

    # INTERNALS ################################################################

    def _logmsg_seed(self, seed: int | None = None) -> str:
        s = seed if seed is not None else self._params.seed
        return self.logmsg.INIT.format(seed=s)

    # CLEANUP ##################################################################

    def __del__(self):
        super().__del__()
