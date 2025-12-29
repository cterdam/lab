import asyncio
from enum import StrEnum

from src import log
from src.lib.data import Data


class PriorityQueue(asyncio.PriorityQueue, Data):
    """Same as asyncio.PriorityQueue, but with logging."""

    logspace_part = "pq"

    class coke(StrEnum):
        PUT = "put"
        GET = "get"

    def __init__(self, maxsize: int = 0, *args, logname: str = "pq", **kwargs):
        asyncio.PriorityQueue.__init__(self, maxsize=maxsize)
        Data.__init__(self, *args, logname=logname, **kwargs)

    @log.input()
    async def put(self, item) -> None:
        await super().put(item)
        self.incr(PriorityQueue.coke.PUT)

    @log.output()
    async def get(self):
        item = await super().get()
        self.incr(PriorityQueue.coke.GET)
        return item
