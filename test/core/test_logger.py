import asyncio
import random
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool

import pytest

from src import env
from src.core import Logger


@pytest.fixture(autouse=True)
def reset_logger_state(tmp_path, monkeypatch):
    """Before each test, set the global registry env.out_dir."""
    monkeypatch.setattr(env, "loggers", dict())
    monkeypatch.setattr(env, "out_dir", tmp_path)
    monkeypatch.setattr(env, "repo_root", tmp_path)


def test_duplicate_logger_no_concurrency():
    dup_name = "dup_noconcur"
    assert dup_name != env.ROOT_LOGID
    _ = Logger(logname=dup_name)
    with pytest.raises(ValueError):
        Logger(logname=dup_name)


@pytest.mark.asyncio
async def test_duplicate_logger_async():
    dup_name = "dup_async"
    assert dup_name != env.ROOT_LOGID
    num_attempts = 100

    async def create_logger():
        try:
            await asyncio.sleep(random.uniform(0, 0.001))
            _ = Logger(logname=dup_name)
            return True
        except:
            return False

    results = await asyncio.gather(*(create_logger() for _ in range(num_attempts)))

    assert sum(results) == 1


def test_duplicate_logger_thread():
    dup_name = "dup_thread"
    assert dup_name != env.ROOT_LOGID
    num_attempts = 100

    def create_logger():
        time.sleep(random.uniform(0, 0.001))
        try:
            _ = Logger(logname=dup_name)
            return True
        except:
            return False

    with ThreadPoolExecutor(max_workers=num_attempts) as executor:
        results = list(executor.map(lambda _: create_logger(), range(num_attempts)))

    assert sum(results) == 1


def process_create_logger(logname: str):
    time.sleep(random.uniform(0, 0.001))
    try:
        _ = Logger(logname=logname)
        return True
    except:
        return False


def test_race_process():
    dup_name = "dup_process"
    assert dup_name != env.ROOT_LOGID
    num_attempts = 20

    with Pool(processes=num_attempts) as pool:
        results = pool.map(process_create_logger, [dup_name] * num_attempts)

    assert sum(results) == 1
