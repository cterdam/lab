import asyncio
import time

from src import log
from src.lib.data.word_bank import WordBank
from src.lib.game.game import Game
from src.lib.model.txt.api.openai import (
    OpenAILM,
    OpenAILMGentxtParams,
    OpenAILMInitParams,
)


def run_sync(n_tasks: int, wb: WordBank, model: OpenAILM):

    start = time.time()
    for i in range(n_tasks):
        prompt = f"In 10 words, what is {wb.pick_word()}"
        result = model.gentxt(OpenAILMGentxtParams(prompt=prompt))
        log.info(f"Sync [{i+1}/{n_tasks}] {result.output!r}")
        log.incr("sync_success")
    duration = time.time() - start

    log.success(f"Sync run took {duration:.2f}s")


async def run_async(n_tasks: int, wb: WordBank, model: OpenAILM):
    tasks = []
    for i in range(n_tasks):
        prompt = f"In 10 words, what is {wb.pick_word()}"
        tasks.append(model.agentxt(OpenAILMGentxtParams(prompt=prompt)))
    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start

    for i, res in enumerate(results, 1):
        log.info(f"Async [{i}/{n_tasks}] {res.output!r}")
        log.incr("async_success")

    log.success(f"Async run took {duration:.2f}s")


def main():

    g = Game(logname="sample_game")
    g.info("Hi!")
    g.trig("normal")
    g.info("Hi again!")
    g.trig("again")
    g.success("Back!")

    n_tasks = 3
    wb = WordBank()
    model = OpenAILM(params=OpenAILMInitParams(model_name="gpt-4.1"))

    run_sync(n_tasks, wb, model)
    asyncio.run(run_async(n_tasks, wb, model))

    log.biset({"abc": 1, "def": 2, "ghi": 30})
    log.incr("abc")
