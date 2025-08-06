import asyncio
import random
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool

import pytest

from src import log


def test_counter_no_concurrency():
    key = "test_counter_no_concurrency"
    num_incrs = 100
    val_per_incr = 2
    for _ in range(num_incrs):
        log.incr(key, val_per_incr)
    assert log.iget(key) == num_incrs * val_per_incr


@pytest.mark.asyncio
async def test_counter_async():
    num_attempts = 100
    num_incrs_per_attempt = 100
    val_per_incr = 2
    key = "test_counter_async"

    async def incr_count(num_incrs: int, val_per_incr: int):
        for _ in range(num_incrs):
            log.incr(key, val_per_incr)
            await asyncio.sleep(random.uniform(0, 0.001))

    _ = await asyncio.gather(
        *(incr_count(num_incrs_per_attempt, val_per_incr) for _ in range(num_attempts))
    )

    assert log.iget(key) == num_attempts * num_incrs_per_attempt * val_per_incr


def test_counter_thread():
    num_attempts = 100
    num_incrs_per_attempt = 100
    val_per_incr = 2
    key = "test_counter_thread"

    def incr_count(num_incrs: int, val_per_incr: int):
        for _ in range(num_incrs):
            log.incr(key, val_per_incr)
            time.sleep(random.uniform(0, 0.001))

    with ThreadPoolExecutor(max_workers=num_attempts) as executor:
        _ = list(
            executor.map(
                lambda _: incr_count(num_incrs_per_attempt, val_per_incr),
                range(num_attempts),
            )
        )

    assert log.iget(key) == num_attempts * num_incrs_per_attempt * val_per_incr


def process_incr_count(key: str, num_incrs_per_attempt: int, val_per_incr: int):
    for _ in range(num_incrs_per_attempt):
        log.incr(key, val_per_incr)
        time.sleep(random.uniform(0, 0.001))


def test_counter_process():
    num_attempts = 30
    num_incrs_per_attempt = 100
    val_per_incr = 2
    key = "test_counter_process"

    with Pool(processes=num_attempts) as pool:
        _ = pool.starmap(
            process_incr_count,
            [(key, num_incrs_per_attempt, val_per_incr)] * num_attempts,
        )

    assert log.iget(key) == num_attempts * num_incrs_per_attempt * val_per_incr


def test_counter_negative():
    key = "test_counter_negative"
    init_val = 0
    num_incrs = 100
    val_per_incr = -1

    assert val_per_incr < 0

    log.iset(key, init_val)
    for _ in range(num_incrs):
        log.incr(key, val_per_incr)

    assert log.iget(key) == num_incrs * val_per_incr


def test_counter_absent_set():
    key = "test_counter_absent_set"
    set_val = 10
    assert log.iget(key) is None

    log.iset(key, set_val)
    assert log.iget(key) == set_val


def test_counter_absent_incr():
    key = "test_counter_absent_get"
    incr_val = 10
    assert log.iget(key) is None

    log.incr(key, incr_val)
    assert log.iget(key) == incr_val


def test_counter_set_val():
    key = "test_counter_set_val"
    init_val = 10
    set_val_1 = 20
    set_val_2 = 30

    log.iset(key, init_val)
    assert log.iget(key) == init_val

    log.iset(key, set_val_1)
    assert log.iget(key) == set_val_1

    log.iset(key, set_val_2)
    assert log.iget(key) == set_val_2


def test_iset_return_new_vs_overwrite():
    key = "test_iset_return_new_vs_overwrite"

    # Brand-new hash field → Redis HSET returns 1
    assert log.iset(key, 111) == 1
    assert log.iget(key) == 111

    # Overwrite existing field → returns 0
    assert log.iset(key, 222) == 0
    assert log.iget(key) == 222


def test_biset_all_new_and_biget_fetch():
    mapping = {
        "test_biset_many_key_0": 0,
        "test_biset_many_key_1": 1,
        "test_biset_many_key_2": 2,
        "test_biset_many_key_3": 3,
        "test_biset_many_key_4": 4,
    }

    added = log.biset(mapping)
    assert added == len(mapping)  # every key was new

    assert log.biget(list(mapping)) == list(mapping.values())


def test_biset_mixed_and_biget_preserves_order():
    k_existing = "test_biset_mixed_existing"
    k_new = "test_biset_mixed_new"

    log.iset(k_existing, 7)  # pre-populate existing field

    added = log.biset({k_existing: 70, k_new: 80})
    assert added == 1  # only k_new added

    # Query in reverse order; output order must match input order
    assert log.biget([k_new, k_existing]) == [80, 70]


def test_biset_all_existing_returns_zero():
    k1, k2 = "test_biset_exist_1", "test_biset_exist_2"
    log.biset({k1: 1, k2: 2})  # first insert → adds 2 fields

    added = log.biset({k1: 10, k2: 20})  # overwrite both
    assert added == 0  # no new fields added
    assert log.biget([k1, k2]) == [10, 20]


def test_biget_mixed_present_and_absent():
    k1, k2, k3 = (
        "test_biget_mix_present",
        "test_biget_mix_absent",
        "test_biget_mix_present2",
    )
    log.iset(k1, 11)
    log.iset(k3, 33)

    res: list[int | None] = log.biget([k1, k2, k3])
    assert res == [11, None, 33]


def test_biget_all_absent_returns_none_list():
    k1, k2 = "test_biget_all_absent_1", "test_biget_all_absent_2"
    assert log.biget([k1, k2]) == [None, None]
