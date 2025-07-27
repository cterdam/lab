import asyncio
import os

import redis.asyncio as redis  # same package, async sub-module


async def realmain():
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

    await r.set("greeting", "hello")
    val = await r.get("greeting")
    print(val)

    await r.incr("visits")
    visits = await r.get("visits")
    print("visits =", visits)

    async with r.pipeline() as pipe:
        pipe.incr("visits")
        pipe.set("status", "ok")
        visits, _ = await pipe.execute()
    print("visits =", visits)


def main():
    asyncio.run(realmain())
