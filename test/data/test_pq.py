import asyncio

import pytest

from src.lib.data.pq import PriorityQueue


@pytest.mark.asyncio
async def test_pq_basic_put_get():
    """Test basic put and get operations."""
    pq = PriorityQueue(logname="test_basic")
    await pq.put(1)
    await pq.put(2)
    await pq.put(3)

    assert await pq.get() == 1
    assert await pq.get() == 2
    assert await pq.get() == 3


@pytest.mark.asyncio
async def test_pq_priority_ordering():
    """Test that priority queue maintains correct ordering."""
    pq = PriorityQueue(logname="test_priority")
    # Put items with different priorities (lower number = higher priority)
    await pq.put((2, "second"))
    await pq.put((1, "first"))
    await pq.put((3, "third"))

    assert await pq.get() == (1, "first")
    assert await pq.get() == (2, "second")
    assert await pq.get() == (3, "third")


@pytest.mark.asyncio
async def test_pq_counters():
    """Test that counters are incremented correctly."""
    pq = PriorityQueue(logname="test_counters")

    assert pq.iget(PriorityQueue.coke.PUT) is None
    assert pq.iget(PriorityQueue.coke.GET) is None

    await pq.put(1)
    assert pq.iget(PriorityQueue.coke.PUT) == 1
    assert pq.iget(PriorityQueue.coke.GET) is None

    await pq.put(2)
    assert pq.iget(PriorityQueue.coke.PUT) == 2

    await pq.get()
    assert pq.iget(PriorityQueue.coke.GET) == 1

    await pq.get()
    assert pq.iget(PriorityQueue.coke.GET) == 2


@pytest.mark.asyncio
async def test_pq_maxsize():
    """Test that maxsize limit works correctly."""
    pq = PriorityQueue(maxsize=2, logname="test_maxsize")

    await pq.put(1)
    await pq.put(2)

    # Queue should be full now
    assert pq.full() is True

    # This should block until space is available
    async def delayed_get():
        await asyncio.sleep(0.1)
        await pq.get()

    # Start get task before putting third item
    get_task = asyncio.create_task(delayed_get())
    await asyncio.sleep(0.05)  # Give get task time to start waiting

    # Now put should succeed after get frees space
    put_task = asyncio.create_task(pq.put(3))
    await asyncio.gather(get_task, put_task)

    assert await pq.get() == 2
    assert await pq.get() == 3


@pytest.mark.asyncio
async def test_pq_empty():
    """Test empty queue behavior."""
    pq = PriorityQueue(logname="test_empty")

    assert pq.empty() is True
    assert pq.qsize() == 0

    await pq.put(1)
    assert pq.empty() is False
    assert pq.qsize() == 1

    await pq.get()
    assert pq.empty() is True
    assert pq.qsize() == 0


@pytest.mark.asyncio
async def test_pq_multiple_items_same_priority():
    """Test that items with same priority maintain insertion order."""
    pq = PriorityQueue(logname="test_same_priority")

    # All items have same priority (0)
    await pq.put((0, "a"))
    await pq.put((0, "b"))
    await pq.put((0, "c"))

    # Should maintain insertion order for same priority
    assert await pq.get() == (0, "a")
    assert await pq.get() == (0, "b")
    assert await pq.get() == (0, "c")


@pytest.mark.asyncio
async def test_pq_custom_logname():
    """Test that custom logname is respected."""
    custom_name = "custom_pq_test"
    pq = PriorityQueue(logname=custom_name)

    assert pq.logname == custom_name
    assert custom_name in pq.logid


@pytest.mark.asyncio
async def test_pq_concurrent_operations():
    """Test concurrent put/get operations."""
    pq = PriorityQueue(logname="test_concurrent")

    async def put_items():
        for i in range(10):
            await pq.put(i)

    async def get_items(results):
        for _ in range(10):
            item = await pq.get()
            results.append(item)

    results = []
    await asyncio.gather(put_items(), get_items(results))

    # Should get all items, possibly in different order due to concurrency
    assert len(results) == 10
    assert set(results) == set(range(10))
