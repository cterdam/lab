import asyncio
import time

from src import log
from src.lib.data.word_bank import WordBank
from src.lib.model.txt.api.openai import (
    OpenaiLm,
    OpenaiLmGentxtParams,
    OpenaiLmInitParams,
)


async def main():

    wb = WordBank()
    model = OpenaiLm(params=OpenaiLmInitParams(model_name="gpt-4.1"))

    start = time.time()
    for i in range(10):
        prompt = f"In 10 words, what is {wb.pick_word()}"
        result = model.gentxt(OpenaiLmGentxtParams(prompt=prompt))
        log.info(f"Sync [{i+1}/10] {result.output!r}")
    duration = time.time() - start

    log.success(f"Sync run took {duration:.2f}s")

    tasks = []
    for i in range(10):
        prompt = f"In 10 words, what is {wb.pick_word()}"
        tasks.append(model.agentxt(OpenaiLmGentxtParams(prompt=prompt)))
    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    for i, res in enumerate(results, 1):
        log.info(f"Async [{i}/10] {res.output!r}")

    log.success(f"Async run took {duration:.2f}s")
