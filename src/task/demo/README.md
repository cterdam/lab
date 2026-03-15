# demo

End-to-end demonstration of the project's capabilities. Exercises multiple
subsystems in a single run:

1. **Sync LLM calls** — sends prompts to OpenAI sequentially, timing the batch.
2. **Async LLM calls** — sends the same prompts concurrently with
   `asyncio.gather`, comparing wall-clock time against the sync run.
3. **Game demo** — creates and starts a `Game` instance with unlimited reactions
   and interruptions, exercising the event-driven game engine.
4. **Group and counter demo** — creates groups, logs membership, and exercises
   the counter and biset logging facilities.

Requires `OPENAI_API_KEY`.
