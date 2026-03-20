from enum import StrEnum

from src import env, log
from src.core.util import obj_id
from src.lib.rng.coin import CoinSide
from src.lib.rng.rng import RNG
from src.lib.rng.rng_init_params import RNGInitParams


class CoinRNG(RNG):
    """A coin: an RNG pre-loaded with heads and tails.

    Domain methods
    ~~~~~~~~~~~~~~
    ``flip()`` draws one side from the pool without replacement.

    Validation
    ~~~~~~~~~~
    ``load()`` is restricted to sequences of exactly 2 ``CoinSide`` items.
    """

    logspace_part = "coin"

    class _coke(StrEnum):
        FLIP = "flip"
        ERR_INVALID_COIN = obj_id(env.ERR_COKE_PREFIX, "invalid_coin")

    class _logmsg(StrEnum):
        COIN_INIT = "Coin created"
        FLIP = "Flipped: {side}"

    @log.input()
    def __init__(
        self,
        *args,
        seed: int | None = None,
        logname: str = "coin",
        **kwargs,
    ):
        pool = [CoinSide.HEADS, CoinSide.TAILS]
        params = RNGInitParams(seed=seed, pool=pool)
        super().__init__(params, *args, logname=logname, **kwargs)
        self.info(self.logmsg.COIN_INIT)

    def flip(self) -> CoinSide | None:
        """Flip the coin. Draws one side without replacement.

        Returns:
            A ``CoinSide`` value, or ``None`` if the pool is exhausted.
        """
        result = self.draw()
        if result is not None:
            self.incr(self.coke.FLIP)
            self.trace(self.logmsg.FLIP.format(side=result))
        return result

    def load(self, items):
        """Load sides into the coin. Must be exactly 2 CoinSide items.

        Args:
            items: Sequence of CoinSide objects (must have length 2).
        """
        items_list = list(items)
        if len(items_list) != 2:
            self.incr(self.coke.ERR_INVALID_COIN)
            self.warning(
                f"Coin requires exactly 2 items, got {len(items_list)}"
            )
            return
        for item in items_list:
            if not isinstance(item, CoinSide):
                self.incr(self.coke.ERR_INVALID_COIN)
                self.warning(
                    f"Cannot load non-CoinSide item: {type(item).__name__}"
                )
                return
        super().load(items_list)

    # CLEANUP ##################################################################

    def __del__(self):
        super().__del__()
