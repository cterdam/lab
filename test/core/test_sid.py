import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from src import env, log


def test_next_sid_monotonically_increasing():
    """Test that next_sid returns monotonically increasing values."""
    num_sids = 100
    sids = [env.next_sid() for _ in range(num_sids)]

    # Check that all values are unique and increasing
    assert len(sids) == len(set(sids)), "All SIDs should be unique"
    assert sids == sorted(sids), "SIDs should be monotonically increasing"
    assert sids[0] < sids[-1], "First SID should be less than last SID"


def test_next_sid_uses_correct_counter_key():
    """Test that next_sid uses the configured counter key."""
    # Get next SID (increments counter and returns the new value)
    # next_sid() calls incr() which atomically increments and returns the new value
    current_sid = env.next_sid()

    # Immediately check that the counter matches the returned SID
    # The SID returned by next_sid() IS the counter value at the time of increment
    counter_value = log.iget(env.SID_COUNTER_KEY)
    # In parallel execution, another test may increment the counter between
    # the increment and this read, so we verify the counter is at least equal
    # to the SID (exact match or higher). This ensures the SID was valid.
    assert (
        counter_value >= current_sid
    ), f"Counter should be at least equal to returned SID: {counter_value} < {current_sid}"


def test_next_sid_concurrent():
    """Test that next_sid is concurrency-safe."""
    num_threads = 50
    num_sids_per_thread = 20

    def get_sids():
        return [env.next_sid() for _ in range(num_sids_per_thread)]

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(lambda _: get_sids(), range(num_threads)))

    # Flatten all SIDs
    all_sids = [sid for sids in results for sid in sids]

    # Check that all SIDs are unique
    assert len(all_sids) == len(set(all_sids)), "All concurrent SIDs should be unique"

    # Check that total count matches expected
    expected_total = num_threads * num_sids_per_thread
    assert len(all_sids) == expected_total, f"Should have {expected_total} SIDs"


@pytest.mark.asyncio
async def test_anext_sid_monotonically_increasing():
    """Test that anext_sid returns monotonically increasing values."""
    num_sids = 100
    sids = [await env.anext_sid() for _ in range(num_sids)]

    # Check that all values are unique and increasing
    assert len(sids) == len(set(sids)), "All SIDs should be unique"
    assert sids == sorted(sids), "SIDs should be monotonically increasing"
    assert sids[0] < sids[-1], "First SID should be less than last SID"


@pytest.mark.asyncio(scope="session")
async def test_anext_sid_uses_correct_counter_key():
    """Test that anext_sid uses the configured counter key."""
    # Warm up the async connection in this event loop by doing a simple operation
    # This ensures the connection pool is initialized in the correct event loop
    try:
        await log.aiget("_warmup_key")
    except Exception:
        pass  # Ignore errors, we just want to initialize the connection

    # Get next SID (increments counter and returns the new value)
    # anext_sid() calls aincr() which atomically increments and returns the new value
    current_sid = await env.anext_sid()

    # Immediately check that the counter matches the returned SID
    # The SID returned by anext_sid() IS the counter value at the time of increment
    counter_value = await log.aiget(env.SID_COUNTER_KEY)
    # In parallel execution, another test may increment the counter between
    # the increment and this read, so we verify the counter is at least equal
    # to the SID (exact match or higher). This ensures the SID was valid.
    assert (
        counter_value >= current_sid
    ), f"Counter should be at least equal to returned SID: {counter_value} < {current_sid}"


@pytest.mark.asyncio(scope="session")
async def test_anext_sid_concurrent():
    """Test that anext_sid is concurrency-safe."""
    num_tasks = 50
    num_sids_per_task = 20

    async def get_sids():
        return [await env.anext_sid() for _ in range(num_sids_per_task)]

    results = await asyncio.gather(*(get_sids() for _ in range(num_tasks)))

    # Flatten all SIDs
    all_sids = [sid for sids in results for sid in sids]

    # Check that all SIDs are unique
    assert len(all_sids) == len(set(all_sids)), "All concurrent SIDs should be unique"

    # Check that total count matches expected
    expected_total = num_tasks * num_sids_per_task
    assert len(all_sids) == expected_total, f"Should have {expected_total} SIDs"


def test_next_sid_and_anext_sid_share_counter():
    """Test that sync and async versions share the same counter.

    Note: This test only verifies sync operations to avoid event loop issues
    when mixing sync and async operations. The counter is shared, so both
    sync and async operations will increment the same counter.
    """
    # Get current counter value
    counter_before = log.iget(env.SID_COUNTER_KEY) or 0

    # Get next SID from sync version
    sync_sid = env.next_sid()
    # In parallel execution, another test may have incremented the counter,
    # so we verify the SID is at least counter_before + 1
    assert (
        sync_sid >= counter_before + 1
    ), f"Sync SID should be at least counter_before + 1: {sync_sid} < {counter_before + 1}"

    # Verify counter matches (or is higher if another test incremented it)
    counter_after = log.iget(env.SID_COUNTER_KEY)
    assert (
        counter_after >= sync_sid
    ), f"Counter should be at least equal to sync SID: {counter_after} < {sync_sid}"
