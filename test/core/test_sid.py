from concurrent.futures import ThreadPoolExecutor

from src import env
from src.core.dataclass import Dataclass


def test_get_next_sid_monotonically_increasing():
    """Test that _get_next_sid returns monotonically increasing values."""
    num_sids = 100
    # Test through Dataclass instantiation
    sids = [Dataclass().sid for _ in range(num_sids)]

    # Check that all values are unique and increasing
    assert len(sids) == len(set(sids)), "All SIDs should be unique"
    assert sids == sorted(sids), "SIDs should be monotonically increasing"
    assert sids[0] < sids[-1], "First SID should be less than last SID"


def test_get_next_sid_uses_correct_counter_key():
    """Test that _get_next_sid uses the configured counter key."""
    # Reset the global SID counter
    env.r.set(env.SID_COUNTER_KEY, 0)

    # Get next SID through Dataclass instantiation
    d = Dataclass()
    current_sid = d.sid

    # Immediately check that the Redis counter matches the returned SID
    counter_value = int(env.r.get(env.SID_COUNTER_KEY))
    assert (
        counter_value == current_sid
    ), f"Counter should match returned SID: {counter_value} != {current_sid}"


def test_get_next_sid_concurrent():
    """Test that _get_next_sid is concurrency-safe."""
    num_threads = 50
    num_sids_per_thread = 20

    def get_sids():
        return [Dataclass().sid for _ in range(num_sids_per_thread)]

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(lambda _: get_sids(), range(num_threads)))

    # Flatten all SIDs
    all_sids = [sid for sids in results for sid in sids]

    # Check that all SIDs are unique
    assert len(all_sids) == len(set(all_sids)), "All concurrent SIDs should be unique"

    # Check that total count matches expected
    expected_total = num_threads * num_sids_per_thread
    assert len(all_sids) == expected_total, f"Should have {expected_total} SIDs"
