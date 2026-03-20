import gc
import weakref

from src.lib.rng.dice_rng import DiceRNG
from src.lib.rng.rng import RNG


# INIT & TYPE ###################################################################


def test_is_rng_subclass():
    """DiceRNG is a subclass of RNG."""
    assert issubclass(DiceRNG, RNG)


def test_instance_of_rng():
    """DiceRNG instance is also an RNG."""
    d = DiceRNG(seed=1, logname="test_isinstance")
    assert isinstance(d, RNG)


def test_logspace():
    """logspace includes both 'rng' and 'dice'."""
    d = DiceRNG(seed=1, logname="test_logspace")
    assert "rng" in d.logspace
    assert "dice" in d.logspace


def test_default_6_sides():
    """Default die has 6 faces."""
    d = DiceRNG(seed=1, logname="test_default")
    assert d.pool_size == 6
    assert d.remaining == 6
    assert d.n_sides == 6


def test_custom_sides():
    """Custom n_sides creates the right pool."""
    d = DiceRNG(20, seed=1, logname="test_d20")
    assert d.pool_size == 20
    assert d.remaining == 20
    assert d.n_sides == 20


def test_d4():
    """4-sided die."""
    d = DiceRNG(4, seed=1, logname="test_d4")
    assert d.pool_size == 4
    faces = d.draw(4)
    assert sorted(faces) == [1, 2, 3, 4]


def test_d12():
    """12-sided die."""
    d = DiceRNG(12, seed=1, logname="test_d12")
    assert d.pool_size == 12
    faces = d.draw(12)
    assert sorted(faces) == list(range(1, 13))


# ROLL METHOD ##################################################################


def test_roll_returns_int():
    """roll() returns an integer."""
    d = DiceRNG(seed=1, logname="test_roll")
    face = d.roll()
    assert isinstance(face, int)


def test_roll_in_range():
    """roll() returns value in [1, n_sides]."""
    d = DiceRNG(seed=1, logname="test_roll_range")
    face = d.roll()
    assert 1 <= face <= 6


def test_roll_decrements_remaining():
    """roll() reduces remaining by 1."""
    d = DiceRNG(seed=1, logname="test_roll_rem")
    d.roll()
    assert d.remaining == 5


def test_roll_all_faces():
    """Rolling all faces yields [1..n_sides]."""
    d = DiceRNG(seed=1, logname="test_roll_all")
    faces = [d.roll() for _ in range(6)]
    assert sorted(faces) == [1, 2, 3, 4, 5, 6]


def test_roll_exhausted():
    """roll() on exhausted die returns None."""
    d = DiceRNG(seed=1, logname="test_roll_empty")
    for _ in range(6):
        d.roll()
    assert d.roll() is None


def test_roll_after_reshuffle():
    """roll() works again after reshuffle."""
    d = DiceRNG(seed=1, logname="test_roll_resh")
    for _ in range(6):
        d.roll()
    d.reshuffle()
    assert d.remaining == 6
    face = d.roll()
    assert isinstance(face, int)


# DETERMINISM ##################################################################


def test_deterministic():
    """Same seed produces same roll sequence."""
    d1 = DiceRNG(seed=42, logname="test_det1")
    d2 = DiceRNG(seed=42, logname="test_det2")
    assert d1.roll() == d2.roll()
    assert [d1.roll() for _ in range(5)] == [d2.roll() for _ in range(5)]


def test_different_seeds_differ():
    """Different seeds produce different orders."""
    d1 = DiceRNG(20, seed=1, logname="test_diff1")
    d2 = DiceRNG(20, seed=999, logname="test_diff2")
    seq1 = [d1.roll() for _ in range(20)]
    seq2 = [d2.roll() for _ in range(20)]
    assert seq1 != seq2


# VALIDATION ###################################################################


def test_load_rejects_non_int():
    """load() rejects non-integer items."""
    d = DiceRNG(seed=1, logname="test_load_bad")
    d.load(["a", "b", "c"])
    # Pool should remain unchanged
    assert d.remaining == 6


def test_load_rejects_negative():
    """load() rejects negative integers."""
    d = DiceRNG(seed=1, logname="test_load_neg")
    d.load([-1, 0, 1])
    assert d.remaining == 6


def test_load_rejects_zero():
    """load() rejects zero."""
    d = DiceRNG(seed=1, logname="test_load_zero")
    d.load([0, 1, 2])
    assert d.remaining == 6


def test_load_rejects_float():
    """load() rejects floats."""
    d = DiceRNG(seed=1, logname="test_load_float")
    d.load([1.5, 2.5])
    assert d.remaining == 6


def test_load_accepts_valid():
    """load() accepts positive integers."""
    d = DiceRNG(seed=1, logname="test_load_good")
    d.load([1, 2, 3, 4, 5, 6, 7, 8])
    assert d.pool_size == 8


# DRAW STILL WORKS #############################################################


def test_draw_works():
    """draw() still works on DiceRNG."""
    d = DiceRNG(seed=1, logname="test_draw")
    face = d.draw()
    assert isinstance(face, int)
    assert 1 <= face <= 6


# RNG METHODS STILL WORK ######################################################


def test_randint_works():
    """Plain RNG methods still work on DiceRNG."""
    d = DiceRNG(seed=42, logname="test_randint")
    val = d.randint(1, 100)
    assert 1 <= val <= 100


# CLEANUP ######################################################################


def test_cleanup():
    """DiceRNG is garbage collected cleanly."""
    d = DiceRNG(seed=1, logname="test_gc")
    weak = weakref.ref(d)
    del d
    gc.collect()
    assert weak() is None


# GAME SCENARIO ################################################################


def test_yahtzee_scenario():
    """Simulate rolling 5 dice for Yahtzee."""
    dice = [DiceRNG(seed=i, logname=f"test_yah_{i}") for i in range(5)]
    rolls = [d.roll() for d in dice]
    assert len(rolls) == 5
    assert all(isinstance(r, int) for r in rolls)
    assert all(1 <= r <= 6 for r in rolls)
