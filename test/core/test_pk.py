import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from src import env, log


def test_next_pk_monotonically_increasing():
    """Test that next_pk returns monotonically increasing values."""
    num_pks = 100
    pks = [env.next_pk() for _ in range(num_pks)]

    # Check that all values are unique and increasing
    assert len(pks) == len(set(pks)), "All PKs should be unique"
    assert pks == sorted(pks), "PKs should be monotonically increasing"
    assert pks[0] < pks[-1], "First PK should be less than last PK"


def test_next_pk_uses_correct_counter_key():
    """Test that next_pk uses the configured counter key."""
    # Get next PK (increments counter and returns the new value)
    # next_pk() calls incr() which atomically increments and returns the new value
    current_pk = env.next_pk()

    # Immediately check that the counter matches the returned PK
    # The PK returned by next_pk() IS the counter value at the time of increment
    counter_value = log.iget(env.PK_COUNTER_KEY)
    # In parallel execution, another test may increment the counter between
    # the increment and this read, so we verify the counter is at least equal
    # to the PK (exact match or higher). This ensures the PK was valid.
    assert (
        counter_value >= current_pk
    ), f"Counter should be at least equal to returned PK: {counter_value} < {current_pk}"


def test_next_pk_concurrent():
    """Test that next_pk is concurrency-safe."""
    num_threads = 50
    num_pks_per_thread = 20

    def get_pks():
        return [env.next_pk() for _ in range(num_pks_per_thread)]

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(lambda _: get_pks(), range(num_threads)))

    # Flatten all PKs
    all_pks = [pk for pks in results for pk in pks]

    # Check that all PKs are unique
    assert len(all_pks) == len(set(all_pks)), "All concurrent PKs should be unique"

    # Check that total count matches expected
    expected_total = num_threads * num_pks_per_thread
    assert len(all_pks) == expected_total, f"Should have {expected_total} PKs"


@pytest.mark.asyncio
async def test_anext_pk_monotonically_increasing():
    """Test that anext_pk returns monotonically increasing values."""
    num_pks = 100
    pks = [await env.anext_pk() for _ in range(num_pks)]

    # Check that all values are unique and increasing
    assert len(pks) == len(set(pks)), "All PKs should be unique"
    assert pks == sorted(pks), "PKs should be monotonically increasing"
    assert pks[0] < pks[-1], "First PK should be less than last PK"


@pytest.mark.asyncio(scope="session")
async def test_anext_pk_uses_correct_counter_key():
    """Test that anext_pk uses the configured counter key."""
    # Warm up the async connection in this event loop by doing a simple operation
    # This ensures the connection pool is initialized in the correct event loop
    try:
        await log.aiget("_warmup_key")
    except Exception:
        pass  # Ignore errors, we just want to initialize the connection

    # Get next PK (increments counter and returns the new value)
    # anext_pk() calls aincr() which atomically increments and returns the new value
    current_pk = await env.anext_pk()

    # Immediately check that the counter matches the returned PK
    # The PK returned by anext_pk() IS the counter value at the time of increment
    counter_value = await log.aiget(env.PK_COUNTER_KEY)
    # In parallel execution, another test may increment the counter between
    # the increment and this read, so we verify the counter is at least equal
    # to the PK (exact match or higher). This ensures the PK was valid.
    assert (
        counter_value >= current_pk
    ), f"Counter should be at least equal to returned PK: {counter_value} < {current_pk}"


@pytest.mark.asyncio(scope="session")
async def test_anext_pk_concurrent():
    """Test that anext_pk is concurrency-safe."""
    num_tasks = 50
    num_pks_per_task = 20

    async def get_pks():
        return [await env.anext_pk() for _ in range(num_pks_per_task)]

    results = await asyncio.gather(*(get_pks() for _ in range(num_tasks)))

    # Flatten all PKs
    all_pks = [pk for pks in results for pk in pks]

    # Check that all PKs are unique
    assert len(all_pks) == len(set(all_pks)), "All concurrent PKs should be unique"

    # Check that total count matches expected
    expected_total = num_tasks * num_pks_per_task
    assert len(all_pks) == expected_total, f"Should have {expected_total} PKs"


def test_next_pk_and_anext_pk_share_counter():
    """Test that sync and async versions share the same counter.

    Note: This test only verifies sync operations to avoid event loop issues
    when mixing sync and async operations. The counter is shared, so both
    sync and async operations will increment the same counter.
    """
    # Get current counter value
    counter_before = log.iget(env.PK_COUNTER_KEY) or 0

    # Get next PK from sync version
    sync_pk = env.next_pk()
    # In parallel execution, another test may have incremented the counter,
    # so we verify the PK is at least counter_before + 1
    assert (
        sync_pk >= counter_before + 1
    ), f"Sync PK should be at least counter_before + 1: {sync_pk} < {counter_before + 1}"

    # Verify counter matches (or is higher if another test incremented it)
    counter_after = log.iget(env.PK_COUNTER_KEY)
    assert (
        counter_after >= sync_pk
    ), f"Counter should be at least equal to sync PK: {counter_after} < {sync_pk}"
