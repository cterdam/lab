import pytest

from src import env, log


@pytest.mark.asyncio
async def test_async_counter_no_concurrency():
    key = "test_async_counter_no_concurrency"
    num_incrs = 100
    val_per_incr = 2
    for _ in range(num_incrs):
        await log.aincr(key, val_per_incr)
    assert await log.aiget(key) == num_incrs * val_per_incr


@pytest.mark.asyncio
async def test_async_counter_negative():
    key = "test_async_counter_negative"
    init_val = 0
    num_incrs = 100
    val_per_incr = -1

    assert val_per_incr < 0

    await log.aiset(key, init_val)
    for _ in range(num_incrs):
        await log.aincr(key, val_per_incr)

    assert await log.aiget(key) == num_incrs * val_per_incr


@pytest.mark.asyncio
async def test_async_counter_absent_set():
    key = "test_async_counter_absent_set"
    set_val = 10
    assert await log.aiget(key) is None

    await log.aiset(key, set_val)
    assert await log.aiget(key) == set_val


@pytest.mark.asyncio
async def test_async_counter_absent_incr():
    key = "test_async_counter_absent_get"
    incr_val = 10
    assert await log.aiget(key) is None

    await log.aincr(key, incr_val)
    assert await log.aiget(key) == incr_val


@pytest.mark.asyncio
async def test_async_iset_return_new_vs_overwrite():
    key = "test_async_iset_return_new_vs_overwrite"

    # Brand-new hash field → Redis HSET returns 1
    assert await log.aiset(key, 111) == 1
    assert await log.aiget(key) == 111

    # Overwrite existing field → returns 0
    assert await log.aiset(key, 222) == 0
    assert await log.aiget(key) == 222


@pytest.mark.asyncio
async def test_async_biset_all_new_and_biget_fetch():
    mapping = {
        "test_async_biset_many_key_0": 0,
        "test_async_biset_many_key_1": 1,
        "test_async_biset_many_key_2": 2,
    }

    added = await log.abiset(mapping)
    assert added == len(mapping)

    assert await log.abiget(list(mapping)) == list(mapping.values())


@pytest.mark.asyncio
async def test_async_biget_mixed_present_and_absent():
    k1, k2, k3 = (
        "test_async_biget_mix_present",
        "test_async_biget_mix_absent",
        "test_async_biget_mix_present2",
    )
    await log.aiset(k1, 11)
    await log.aiset(k3, 33)

    res: list[int | None] = await log.abiget([k1, k2, k3])
    assert res == [11, None, 33]


@pytest.mark.asyncio
async def test_async_pipeline_is_flushed_at_exit():
    k, v = "test_async_pipeline_is_flushed_at_exit", 999
    async with env.acoup() as p:
        await log.aiset(k, v, p=p)
        # No explicit p.execute()
    assert await log.aiget(k) == v


@pytest.mark.asyncio
async def test_async_pipeline_multiple_commands():
    k1, k2, k3 = "async_multi_1", "async_multi_2", "async_multi_3"
    v1, v2 = 10, 20
    await log.aiset(k1, v1)

    async with env.acoup() as p:
        await log.aincr(k1, p=p)
        await log.aiset(k2, v2, p=p)
        await log.aiget(k1, p=p)
        await log.abiget([k1, k2, k3], p=p)
        results = await p.execute()

    assert results == [v1 + 1, 1, v1 + 1, [v1 + 1, v2, None]]
    assert await log.aiget(k1) == v1 + 1
    assert await log.aiget(k2) == v2
    assert await log.aiget(k3) is None
