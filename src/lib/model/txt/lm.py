from abc import abstractmethod
from enum import StrEnum
from typing import final

from src import env, log
from src.core import Timed
from src.core.func_result import atimed, td2ms, timed
from src.lib.model import Model
from src.lib.model.txt.lm_gentxt_result import LMGentxtResult


class LM(Model):
    """Base class for language models."""

    logspace_part = "txt"

    class coke(StrEnum):
        GENTXT_INVOC = "gentxt_invoc"
        GENTXT_MICROS = "gentxt_micros"
        AGENTXT_INVOC = "agentxt_invoc"
        AGENTXT_MICROS = "agentxt_micros"
        INPUT_TOKEN = "input_tokens"
        OUTPUT_TOKEN = "output_tokens"

    @final
    @log.io()
    def gentxt(self, *args, **kwargs) -> Timed[LMGentxtResult]:
        """Public API for synchronous text generation."""
        res: Timed[LMGentxtResult] = timed(self._gentxt)(*args, **kwargs)
        with env.coup() as p:
            self.incr(LM.coke.GENTXT_INVOC, p=p)
            self.incr(LM.coke.GENTXT_MICROS, td2ms(res.time), p=p)
            self.incr(LM.coke.INPUT_TOKEN, res.data.n_input_tokens, p=p)
            self.incr(LM.coke.OUTPUT_TOKEN, res.data.n_output_tokens, p=p)
        return res

    @abstractmethod
    def _gentxt(self, *args, **kwargs) -> LMGentxtResult:
        """Core implementation for synchronous text generation."""
        pass

    @final
    @log.io()
    async def agentxt(self, *args, **kwargs) -> Timed[LMGentxtResult]:
        """Public API for asynchronous text generation."""
        res: Timed[LMGentxtResult] = await atimed(self._agentxt)(*args, **kwargs)
        async with env.acoup() as p:
            await self.aincr(LM.coke.AGENTXT_INVOC, p=p)
            await self.aincr(LM.coke.AGENTXT_MICROS, td2ms(res.time), p=p)
            await self.aincr(LM.coke.INPUT_TOKEN, res.data.n_input_tokens, p=p)
            await self.aincr(LM.coke.OUTPUT_TOKEN, res.data.n_output_tokens, p=p)
        return res

    @abstractmethod
    async def _agentxt(self, *args, **kwargs) -> LMGentxtResult:
        """Core implementation for asynchronous text generation."""
        pass
