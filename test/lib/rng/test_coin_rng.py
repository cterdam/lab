import gc
import weakref

from src.lib.rng.coin import CoinSide
from src.lib.rng.coin_rng import CoinRNG
from src.lib.rng.rng import RNG


# INIT & TYPE ###################################################################


def test_is_rng_subclass():
    """CoinRNG is a subclass of RNG."""
    assert issubclass(CoinRNG, RNG)


def test_instance_of_rng():
    """CoinRNG instance is also an RNG."""
    c = CoinRNG(seed=1, logname="test_isinstance")
    assert isinstance(c, RNG)


def test_logspace():
    """logspace includes both 'rng' and 'coin'."""
    c = CoinRNG(seed=1, logname="test_logspace")
    assert "rng" in c.logspace
    assert "coin" in c.logspace


def test_pool_size():
    """Coin has exactly 2 items."""
    c = CoinRNG(seed=1, logname="test_pool")
    assert c.pool_size == 2
    assert c.remaining == 2


# FLIP METHOD ##################################################################


def test_flip_returns_coinside():
    """flip() returns a CoinSide value."""
    c = CoinRNG(seed=1, logname="test_flip")
    side = c.flip()
    assert isinstance(side, CoinSide)
    assert side in (CoinSide.HEADS, CoinSide.TAILS)


def test_flip_decrements_remaining():
    """flip() reduces remaining by 1."""
    c = CoinRNG(seed=1, logname="test_flip_rem")
    c.flip()
    assert c.remaining == 1


def test_flip_both_sides():
    """Two flips yield both sides."""
    c = CoinRNG(seed=1, logname="test_flip_both")
    sides = [c.flip(), c.flip()]
    assert set(sides) == {CoinSide.HEADS, CoinSide.TAILS}


def test_flip_exhausted():
    """flip() on exhausted coin returns None."""
    c = CoinRNG(seed=1, logname="test_flip_empty")
    c.flip()
    c.flip()
    assert c.remaining == 0
    assert c.flip() is None


def test_flip_after_reshuffle():
    """flip() works again after reshuffle."""
    c = CoinRNG(seed=1, logname="test_flip_resh")
    c.flip()
    c.flip()
    c.reshuffle()
    assert c.remaining == 2
    side = c.flip()
    assert isinstance(side, CoinSide)


# DETERMINISM ##################################################################


def test_deterministic():
    """Same seed produces same flip sequence."""
    c1 = CoinRNG(seed=42, logname="test_det1")
    c2 = CoinRNG(seed=42, logname="test_det2")
    assert c1.flip() == c2.flip()
    assert c1.flip() == c2.flip()


# VALIDATION ###################################################################


def test_load_rejects_wrong_count():
    """load() rejects sequences that aren't exactly 2 items."""
    c = CoinRNG(seed=1, logname="test_load_count")
    c.load([CoinSide.HEADS])
    # Pool should remain unchanged
    assert c.remaining == 2


def test_load_rejects_three_items():
    """load() rejects 3-item sequences."""
    c = CoinRNG(seed=1, logname="test_load_3")
    c.load([CoinSide.HEADS, CoinSide.TAILS, CoinSide.HEADS])
    assert c.remaining == 2


def test_load_rejects_non_coinside():
    """load() rejects non-CoinSide items."""
    c = CoinRNG(seed=1, logname="test_load_bad")
    c.load(["heads", "tails"])
    assert c.remaining == 2


def test_load_accepts_valid():
    """load() accepts exactly 2 CoinSide items."""
    c = CoinRNG(seed=1, logname="test_load_good")
    c.flip()
    c.flip()
    assert c.remaining == 0
    c.load([CoinSide.HEADS, CoinSide.TAILS])
    assert c.remaining == 2


# DRAW STILL WORKS #############################################################


def test_draw_works():
    """draw() still works on CoinRNG."""
    c = CoinRNG(seed=1, logname="test_draw")
    side = c.draw()
    assert isinstance(side, CoinSide)


# CLEANUP ######################################################################


def test_cleanup():
    """CoinRNG is garbage collected cleanly."""
    c = CoinRNG(seed=1, logname="test_gc")
    weak = weakref.ref(c)
    del c
    gc.collect()
    assert weak() is None
