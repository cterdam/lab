import gc
import weakref

from src.lib.rng.rng import RNG
from src.lib.rng.rng_init_params import RNGInitParams


# INIT & LIFECYCLE #############################################################


def test_empty_rng():
    """An RNG with no pool is valid."""
    r = RNG(RNGInitParams(), logname="test_empty")
    assert r.remaining == 0
    assert r.pool_size == 0


def test_init_with_seed():
    """Seed is stored."""
    r = RNG(RNGInitParams(seed=42), logname="test_seed")
    assert r.seed == 42


def test_init_no_seed():
    """No seed defaults to None."""
    r = RNG(RNGInitParams(), logname="test_no_seed")
    assert r.seed is None


def test_init_with_pool():
    """Pool from params is loaded at construction."""
    r = RNG(RNGInitParams(seed=1, pool=[10, 20, 30]), logname="test_pool")
    assert r.remaining == 3
    assert r.pool_size == 3


def test_logtag_no_pool():
    """_logtag shows 'no pool' when pool not loaded."""
    r = RNG(RNGInitParams(), logname="test_logtag_none")
    assert r._logtag == "no pool"


def test_logtag_with_pool():
    """_logtag shows item count when pool is loaded."""
    r = RNG(RNGInitParams(pool=[1, 2, 3]), logname="test_logtag_pool")
    assert r._logtag == "3p"


def test_logspace():
    """logspace_part is 'rng'."""
    r = RNG(RNGInitParams(), logname="test_logspace")
    assert "rng" in r.logspace


def test_cleanup():
    """RNG instance is garbage collected cleanly."""
    r = RNG(RNGInitParams(), logname="test_gc")
    weak = weakref.ref(r)
    del r
    gc.collect()
    assert weak() is None


# POOL OPERATIONS ##############################################################


def test_load():
    """load() sets the pool."""
    r = RNG(RNGInitParams(seed=1), logname="test_load")
    r.load([1, 2, 3, 4, 5])
    assert r.remaining == 5
    assert r.pool_size == 5


def test_load_replaces():
    """load() replaces existing pool."""
    r = RNG(RNGInitParams(seed=1), logname="test_load_replace")
    r.load([1, 2, 3])
    r.load(["a", "b"])
    assert r.remaining == 2
    assert r.pool_size == 2


def test_draw_one():
    """draw() returns a single item."""
    r = RNG(RNGInitParams(seed=42, pool=[10, 20, 30]), logname="test_draw1")
    item = r.draw()
    assert item in [10, 20, 30]
    assert r.remaining == 2


def test_draw_many():
    """draw(n) returns a list of n items."""
    r = RNG(
        RNGInitParams(seed=42, pool=[1, 2, 3, 4, 5]),
        logname="test_draw_many",
    )
    items = r.draw(3)
    assert isinstance(items, list)
    assert len(items) == 3
    assert r.remaining == 2


def test_draw_all():
    """Drawing all items empties the pool."""
    r = RNG(RNGInitParams(seed=1, pool=[1, 2, 3]), logname="test_draw_all")
    r.draw()
    r.draw()
    r.draw()
    assert r.remaining == 0


def test_draw_exhausted():
    """Drawing from empty pool is a no-op."""
    r = RNG(RNGInitParams(seed=1, pool=[1]), logname="test_draw_empty")
    r.draw()
    result = r.draw()
    assert result is None
    assert r.remaining == 0


def test_draw_not_loaded():
    """Drawing without a pool is a no-op."""
    r = RNG(RNGInitParams(), logname="test_draw_no_pool")
    result = r.draw()
    assert result is None


def test_draw_too_many():
    """Drawing more than remaining is a no-op."""
    r = RNG(RNGInitParams(seed=1, pool=[1, 2, 3]), logname="test_draw_too_many")
    result = r.draw(5)
    assert result is None
    assert r.remaining == 3


def test_draw_without_replacement():
    """Drawn items do not reappear."""
    r = RNG(RNGInitParams(seed=42, pool=[1, 2, 3, 4, 5]), logname="test_no_rep")
    drawn = []
    for _ in range(5):
        drawn.append(r.draw())
    assert sorted(drawn) == [1, 2, 3, 4, 5]


def test_reshuffle():
    """reshuffle() restores the full pool."""
    r = RNG(RNGInitParams(seed=1, pool=[1, 2, 3, 4, 5]), logname="test_resh")
    r.draw(3)
    assert r.remaining == 2
    r.reshuffle()
    assert r.remaining == 5


def test_reshuffle_not_loaded():
    """reshuffle() without a pool is a no-op."""
    r = RNG(RNGInitParams(), logname="test_resh_none")
    r.reshuffle()  # should not raise


def test_reshuffle_changes_order():
    """reshuffle() produces a (potentially) different order."""
    r = RNG(RNGInitParams(seed=1, pool=list(range(20))), logname="test_resh_ord")
    first_run = [r.draw() for _ in range(20)]
    r.reshuffle()
    second_run = [r.draw() for _ in range(20)]
    # Both contain the same items
    assert sorted(first_run) == sorted(second_run) == list(range(20))


def test_deterministic_with_seed():
    """Same seed produces same draw sequence."""
    params = RNGInitParams(seed=123, pool=list(range(10)))
    r1 = RNG(params, logname="test_det1")
    r2 = RNG(params, logname="test_det2")
    seq1 = [r1.draw() for _ in range(10)]
    seq2 = [r2.draw() for _ in range(10)]
    assert seq1 == seq2


# PLAIN RANDOM OPERATIONS #####################################################


def test_randint():
    """randint returns value in [a, b]."""
    r = RNG(RNGInitParams(seed=42), logname="test_randint")
    for _ in range(100):
        val = r.randint(1, 6)
        assert 1 <= val <= 6


def test_uniform():
    """uniform returns value in [a, b]."""
    r = RNG(RNGInitParams(seed=42), logname="test_uniform")
    for _ in range(100):
        val = r.uniform(0.0, 1.0)
        assert 0.0 <= val <= 1.0


def test_choice():
    """choice picks from a sequence."""
    r = RNG(RNGInitParams(seed=42), logname="test_choice")
    options = ["a", "b", "c"]
    result = r.choice(options)
    assert result in options


def test_choice_empty():
    """choice on empty sequence returns None."""
    r = RNG(RNGInitParams(seed=42), logname="test_choice_empty")
    result = r.choice([])
    assert result is None


def test_sample():
    """sample picks k unique elements."""
    r = RNG(RNGInitParams(seed=42), logname="test_sample")
    result = r.sample([1, 2, 3, 4, 5], 3)
    assert len(result) == 3
    assert len(set(result)) == 3  # all unique
    assert all(x in [1, 2, 3, 4, 5] for x in result)


def test_sample_too_many():
    """sample with k > len returns None."""
    r = RNG(RNGInitParams(seed=42), logname="test_sample_too_many")
    result = r.sample([1, 2], 5)
    assert result is None


def test_shuffle():
    """shuffle mutates the list in place."""
    r = RNG(RNGInitParams(seed=42), logname="test_shuffle")
    items = list(range(20))
    original = list(items)
    r.shuffle(items)
    assert sorted(items) == original  # same elements


def test_deterministic_randint():
    """Same seed produces same randint sequence."""
    r1 = RNG(RNGInitParams(seed=7), logname="test_det_ri1")
    r2 = RNG(RNGInitParams(seed=7), logname="test_det_ri2")
    seq1 = [r1.randint(0, 100) for _ in range(20)]
    seq2 = [r2.randint(0, 100) for _ in range(20)]
    assert seq1 == seq2


# SEED MANAGEMENT ##############################################################


def test_reseed():
    """reseed resets the PRNG to original seed."""
    r = RNG(RNGInitParams(seed=42), logname="test_reseed")
    first = [r.randint(0, 100) for _ in range(5)]
    r.reseed()
    second = [r.randint(0, 100) for _ in range(5)]
    assert first == second


def test_reseed_new_seed():
    """reseed with a new seed changes behavior."""
    r = RNG(RNGInitParams(seed=42), logname="test_reseed_new")
    first = [r.randint(0, 1000) for _ in range(10)]
    r.reseed(seed=99)
    second = [r.randint(0, 1000) for _ in range(10)]
    # Very unlikely to be the same with different seeds
    assert first != second


# DECK-LIKE SCENARIO ##########################################################


def test_deck_of_cards_scenario():
    """Simulate a simple card deck: load, draw, reshuffle, draw again."""
    suits = ["H", "D", "C", "S"]
    ranks = list(range(1, 14))
    deck = [f"{r}{s}" for s in suits for r in ranks]
    assert len(deck) == 52

    r = RNG(RNGInitParams(seed=1, pool=deck), logname="test_deck")
    assert r.pool_size == 52
    assert r.remaining == 52

    # Draw a hand of 5
    hand = r.draw(5)
    assert len(hand) == 5
    assert r.remaining == 47

    # All drawn cards are valid
    for card in hand:
        assert card in deck

    # Draw rest of the deck
    rest = r.draw(47)
    assert len(rest) == 47
    assert r.remaining == 0

    # All 52 cards were drawn exactly once
    all_drawn = hand + rest
    assert sorted(all_drawn) == sorted(deck)

    # Reshuffle and draw again
    r.reshuffle()
    assert r.remaining == 52
    new_hand = r.draw(5)
    assert len(new_hand) == 5
