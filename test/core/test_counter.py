import asyncio
import random
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool

import pytest

from src.core import Logger


def test_counter_no_concurrency():
    logger_name = "test_counter_noconcur"
    logger = Logger(logname=logger_name)
    key = "count"
    num_incrs = 100
    val_per_incr = 2
    for _ in range(num_incrs):
        logger.incr(key, val_per_incr)
    assert logger.get(key) == num_incrs * val_per_incr


@pytest.mark.asyncio
async def test_counter_async():
    logger_name = "test_counter_async"
    num_attempts = 100
    num_incrs_per_attempt = 100
    val_per_incr = 2
    key = "count"

    async def incr_count(logger: Logger):
        for _ in range(num_incrs_per_attempt):
            logger.incr(key, val_per_incr)
            await asyncio.sleep(random.uniform(0, 0.001))

    logger = Logger(logname=logger_name)
    _ = await asyncio.gather(*(incr_count(logger) for _ in range(num_attempts)))

    assert logger.get(key) == num_attempts * num_incrs_per_attempt * val_per_incr


def test_counter_thread():
    logger_name = "test_counter_thread"
    num_attempts = 100
    num_incrs_per_attempt = 100
    val_per_incr = 2
    key = "count"

    def incr_count(logger: Logger):
        for _ in range(num_incrs_per_attempt):
            logger.incr(key, val_per_incr)
            time.sleep(random.uniform(0, 0.001))

    logger = Logger(logname=logger_name)
    with ThreadPoolExecutor(max_workers=num_attempts) as executor:
        _ = list(executor.map(lambda _: incr_count(logger), range(num_attempts)))

    assert logger.get(key) == num_attempts * num_incrs_per_attempt * val_per_incr


def process_incr_count(key: str, num_incrs_per_attempt: int, val_per_incr: int):
    from src import log

    for _ in range(num_incrs_per_attempt):
        log.incr(key, val_per_incr)
        time.sleep(random.uniform(0, 0.001))


def test_counter_process():
    num_attempts = 30
    num_incrs_per_attempt = 100
    val_per_incr = 2
    key = "count"

    with Pool(processes=num_attempts) as pool:
        _ = pool.starmap(
            process_incr_count,
            [(key, num_incrs_per_attempt, val_per_incr)] * num_attempts,
        )

    from src import log

    assert log.get(key) == num_attempts * num_incrs_per_attempt * val_per_incr
