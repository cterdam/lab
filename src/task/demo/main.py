import asyncio
import time

from src import log
from src.lib.data.word_bank import WordBank
from src.lib.model.txt.api.openai import (
    OpenaiLm,
    OpenaiLmGentxtParams,
    OpenaiLmInitParams,
)


def run_sync(n_tasks: int, wb: WordBank, model: OpenaiLm):

    start = time.time()
    for i in range(n_tasks):
        prompt = f"In 10 words, what is {wb.pick_word()}"
        result = model.gentxt(OpenaiLmGentxtParams(prompt=prompt))
        log.info(f"Sync [{i+1}/{n_tasks}] {result.output!r}")
    duration = time.time() - start

    log.success(f"Sync run took {duration:.2f}s")


async def run_async(n_tasks: int, wb: WordBank, model: OpenaiLm):
    tasks = []
    for i in range(n_tasks):
        prompt = f"In 10 words, what is {wb.pick_word()}"
        tasks.append(model.agentxt(OpenaiLmGentxtParams(prompt=prompt)))
    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    for i, res in enumerate(results, 1):
        log.info(f"Async [{i}/{n_tasks}] {res.output!r}")

    log.success(f"Async run took {duration:.2f}s")


def main():

    n_tasks = 10
    wb = WordBank()
    model = OpenaiLm(params=OpenaiLmInitParams(model_name="gpt-4.1"))

    run_sync(n_tasks, wb, model)
    asyncio.run(run_async(n_tasks, wb, model))
