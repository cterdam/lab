from enum import StrEnum

from src import env, log
from src.core.util import obj_id
from src.lib.rng.rng import RNG
from src.lib.rng.rng_init_params import RNGInitParams


class DiceRNG(RNG):
    """A die: an RNG pre-loaded with integer faces [1..n_sides].

    Domain methods
    ~~~~~~~~~~~~~~
    ``roll()`` draws one face from the pool without replacement.

    Validation
    ~~~~~~~~~~
    ``load()`` is restricted to sequences of positive integers.
    """

    logspace_part = "dice"

    class _coke(StrEnum):
        ROLL = "roll"
        ERR_INVALID_FACE = obj_id(env.ERR_COKE_PREFIX, "invalid_face")

    class _logmsg(StrEnum):
        DICE_INIT = "Dice created: {n} sides"
        ROLL = "Rolled: {face}"

    @log.input()
    def __init__(
        self,
        n_sides: int = 6,
        *args,
        seed: int | None = None,
        logname: str = "dice",
        **kwargs,
    ):
        pool = list(range(1, n_sides + 1))
        params = RNGInitParams(seed=seed, pool=pool)
        super().__init__(params, *args, logname=logname, **kwargs)
        self._n_sides = n_sides
        self.info(self.logmsg.DICE_INIT.format(n=n_sides))

    @property
    def n_sides(self) -> int:
        """Number of faces on the die."""
        return self._n_sides

    def roll(self) -> int | None:
        """Roll the die. Draws one face without replacement.

        Returns:
            An integer face value, or ``None`` if the pool is exhausted.
        """
        result = self.draw()
        if result is not None:
            self.incr(self.coke.ROLL)
            self.trace(self.logmsg.ROLL.format(face=result))
        return result

    def load(self, items):
        """Load faces into the die. Must be positive integers.

        Args:
            items: Sequence of positive integers.
        """
        items_list = list(items)
        for item in items_list:
            if not isinstance(item, int) or item < 1:
                self.incr(self.coke.ERR_INVALID_FACE)
                self.warning(
                    f"Cannot load non-positive-int face: {item!r}"
                )
                return
        super().load(items_list)

    # CLEANUP ##################################################################

    def __del__(self):
        super().__del__()
