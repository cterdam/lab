from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Generic, TypeVar, final

from src import env, log
from src.core import Dataclass, Logger
from src.core.func_result import Timed, atimed, td2ms


class Input(Dataclass):
    """Base class for algorithm inputs."""

    pass


class Output(Dataclass):
    """Base class for algorithm outputs."""

    pass


InputT = TypeVar("InputT", bound=Input)
OutputT = TypeVar("OutputT", bound=Output)


class Algo(Logger, ABC, Generic[InputT, OutputT]):
    """Base class for all algorithms with built-in orchestration."""

    logspace_part = "algo"

    input_type: type[InputT]

    class coke(StrEnum):
        INVOC = "invoc"
        MICROS = "micros"

    @final
    @log.io()
    async def run(self, inp: InputT) -> Timed[OutputT]:
        """Public API for algo run."""
        res: Timed[OutputT] = await atimed(self._run)(inp)
        async with env.acoup() as p:
            await self.aincr(Algo.coke.INVOC, p=p)
            await self.aincr(Algo.coke.MICROS, td2ms(res.time), p=p)
        return res

    @abstractmethod
    async def _run(self, inp: InputT) -> OutputT:
        """Core algo run logic to be implemented by child classes."""
        pass
