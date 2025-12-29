import asyncio
import time

from src import log
from src.lib.data.word_bank import WordBank
from src.lib.game.event.misc import GameEnd
from src.lib.game.game import Game
from src.lib.game.game_init_params import GameInitParams
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
        log.info(f"Sync [{i+1}/{n_tasks}] {result.output_str}")
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
        log.info(f"Async [{i}/{n_tasks}] {res.output_str}")
        log.incr("async_success")

    log.success(f"Async run took {duration:.2f}s")


async def demo_game():
    """Run a simple game demo."""
    log.info("Starting game demo")

    # Create game
    game = Game(
        params=GameInitParams(
            max_react_per_event=-1,  # Unlimited reactions
            max_interrupt_per_speech=-1,  # Unlimited interruptions
        ),
    )

    # Start game in background (this will emit GameStart and process it)
    game_task = asyncio.create_task(game.start())

    # Wait a bit, then end the game
    await asyncio.sleep(0.1)
    game_end = GameEnd(src=game.logid)
    await game._eq.put(
        (
            game.prio.NORMAL,
            game_end.event_id,
            game_end,
        )
    )

    # Wait for game to finish
    await game_task

    log.success("Game demo finished")


def main():

    n_tasks = 1
    wb = WordBank()
    model = OpenAILM(params=OpenAILMInitParams(model_name="gpt-4.1"))

    run_sync(n_tasks, wb, model)
    asyncio.run(run_async(n_tasks, wb, model))

    log.biset({"abc": 1, "def": 2, "ghi": 30})
    log.incr("abc")

    # Run game demo
    asyncio.run(demo_game())
