from src.lib.rng.rng_init_params import RNGInitParams


def test_default_params():
    """Default params have no seed and no pool."""
    p = RNGInitParams()
    assert p.seed is None
    assert p.pool is None


def test_seed_param():
    """Seed can be set."""
    p = RNGInitParams(seed=42)
    assert p.seed == 42


def test_pool_param():
    """Pool can be set."""
    p = RNGInitParams(pool=[1, 2, 3])
    assert p.pool == [1, 2, 3]


def test_seed_and_pool():
    """Both seed and pool can be set together."""
    p = RNGInitParams(seed=99, pool=["a", "b"])
    assert p.seed == 99
    assert p.pool == ["a", "b"]
