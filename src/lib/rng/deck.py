from enum import StrEnum

from src import env, log
from src.core.util import obj_id
from src.lib.rng.card import Card, Rank, Suit
from src.lib.rng.rng import RNG
from src.lib.rng.rng_init_params import RNGInitParams


class Deck(RNG):
    """A poker deck: an RNG pre-loaded with 52 (or 54) playing cards.

    Each card is a ``Card`` dataclass with ``rank`` and ``suit`` fields.
    Jokers have ``rank=Rank.JOKER`` and ``suit=None``.

    Domain methods
    ~~~~~~~~~~~~~~
    ``deal(n)`` is a semantic alias for ``draw(n)`` — it draws cards
    from the deck without replacement.

    Validation
    ~~~~~~~~~~
    ``load()`` is restricted to sequences of ``Card`` objects.
    Non-Card items are rejected with a warning.
    """

    logspace_part = "deck"

    class _coke(StrEnum):
        DEAL = "deal"
        ERR_INVALID_CARD = obj_id(env.ERR_COKE_PREFIX, "invalid_card")

    class _logmsg(StrEnum):
        DECK_INIT = "Deck created: {n} cards ({jokers} jokers)"

    @log.input()
    def __init__(
        self,
        *args,
        jokers: int = 0,
        seed: int | None = None,
        logname: str = "deck",
        **kwargs,
    ):
        deck: list[Card] = [
            Card(rank=r, suit=s)
            for s in Suit
            for r in Rank
            if r != Rank.JOKER
        ]
        for _ in range(jokers):
            deck.append(Card(rank=Rank.JOKER))
        params = RNGInitParams(seed=seed, pool=deck)
        super().__init__(params, *args, logname=logname, **kwargs)
        self._jokers = jokers
        self.info(
            self.logmsg.DECK_INIT.format(n=len(deck), jokers=jokers)
        )

    def deal(self, n: int = 1):
        """Deal card(s) from the deck. Alias for ``draw(n)``.

        Args:
            n: Number of cards to deal. Defaults to 1.

        Returns:
            A single Card when ``n=1``, a list when ``n>1``,
            or ``None`` if the deck is empty.
        """
        result = self.draw(n)
        if result is not None:
            self.incr(self.coke.DEAL, n if n > 1 else 1)
        return result

    def load(self, items):
        """Load cards into the deck. Only accepts Card instances.

        Args:
            items: Sequence of Card objects.
        """
        for item in items:
            if not isinstance(item, Card):
                self.incr(self.coke.ERR_INVALID_CARD)
                self.warning(
                    f"Cannot load non-Card item: {type(item).__name__}"
                )
                return
        super().load(items)

    # CLEANUP ##################################################################

    def __del__(self):
        super().__del__()
