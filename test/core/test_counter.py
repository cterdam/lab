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
