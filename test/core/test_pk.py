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
    # Get current counter value
    current_pk = env.next_pk()

    # Check that the counter key exists and has the expected value
    counter_value = log.iget(env.PK_COUNTER_KEY)
    assert counter_value == current_pk, "Counter should match last PK"


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


@pytest.mark.asyncio
async def test_anext_pk_uses_correct_counter_key():
    """Test that anext_pk uses the configured counter key."""
    # Get current counter value
    current_pk = await env.anext_pk()

    # Check that the counter key exists and has the expected value
    counter_value = await log.aiget(env.PK_COUNTER_KEY)
    assert counter_value == current_pk, "Counter should match last PK"


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_next_pk_and_anext_pk_share_counter():
    """Test that sync and async versions share the same counter."""
    # Get some PKs from sync version
    sync_pks = [env.next_pk() for _ in range(10)]
    last_sync_pk = sync_pks[-1]

    # Get next PK from async version - should continue from sync
    async_pk = await env.anext_pk()
    assert async_pk > last_sync_pk, "Async PK should continue from sync PK"

    # Get more from sync - should continue from async
    sync_pk_after_async = env.next_pk()
    assert sync_pk_after_async > async_pk, "Sync PK should continue from async PK"
