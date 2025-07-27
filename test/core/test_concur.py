import asyncio
import random
import threading
import time
from multiprocessing import Process, Value

import pytest


@pytest.mark.asyncio
async def test_race_async():
    num_incrs = 100
    global counter
    counter = 0

    async def incr():
        global counter
        await asyncio.sleep(random.uniform(0, 0.001))
        temp = counter
        await asyncio.sleep(0)
        counter = temp + 1

    await asyncio.gather(*(incr() for _ in range(num_incrs)))
    assert counter < num_incrs, f"Race condition NOT observed"


def test_race_thread():
    num_incrs = 100
    global counter
    counter = 0

    def incr():
        global counter
        temp = counter
        time.sleep(random.uniform(0, 0.001))
        counter = temp + 1

    threads = [threading.Thread(target=incr) for _ in range(num_incrs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert counter < num_incrs, f"Race condition NOT observed"


def process_incr(counter):
    temp = counter.value
    time.sleep(random.uniform(0, 0.001))
    counter.value = temp + 1


def test_race_process():
    num_incrs = 20
    counter = Value("i", 0, lock=False)

    processes = [
        Process(target=process_incr, args=(counter,)) for _ in range(num_incrs)
    ]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    assert counter.value < num_incrs, f"Race condition NOT observed"
