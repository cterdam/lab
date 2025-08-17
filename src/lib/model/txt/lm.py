from abc import abstractmethod
from enum import StrEnum

from src import env, log
from src.lib.model import Model
from src.lib.model.txt.lm_gentxt_result import LMGentxtResult


class LM(Model):
    """Base class for language models."""

    logspace_part = "txt"

    class coke(StrEnum):
        GENTXT_INVOC = "gentxt_invoc"
        AGENTXT_INVOC = "agentxt_invoc"
        INPUT_TOKEN = "input_tokens"
        OUTPUT_TOKEN = "output_tokens"

    @log.io()
    def gentxt(self, *args, **kwargs) -> LMGentxtResult:

        result = self._do_gentxt(*args, **kwargs)

        with env.coup() as p:

            self.incr(LM.coke.GENTXT_INVOC, p=p)
            self.incr(LM.coke.INPUT_TOKEN, result.input_tokens, p=p)
            self.incr(LM.coke.OUTPUT_TOKEN, result.output_tokens, p=p)

            log.incr(LM.coke.GENTXT_INVOC, p=p)
            log.incr(LM.coke.INPUT_TOKEN, result.input_tokens, p=p)
            log.incr(LM.coke.OUTPUT_TOKEN, result.output_tokens, p=p)

        return result

    @abstractmethod
    def _do_gentxt(self, *args, **kwargs) -> LMGentxtResult: ...

    @log.io()
    async def agentxt(self, *args, **kwargs) -> LMGentxtResult:

        result = await self._do_agentxt(*args, **kwargs)

        async with env.acoup() as p:

            await self.aincr(LM.coke.AGENTXT_INVOC, p=p)
            await self.aincr(LM.coke.INPUT_TOKEN, result.input_tokens, p=p)
            await self.aincr(LM.coke.OUTPUT_TOKEN, result.output_tokens, p=p)

            await log.aincr(LM.coke.AGENTXT_INVOC, p=p)
            await log.aincr(LM.coke.INPUT_TOKEN, result.input_tokens, p=p)
            await log.aincr(LM.coke.OUTPUT_TOKEN, result.output_tokens, p=p)

        return result

    @abstractmethod
    async def _do_agentxt(self, *args, **kwargs) -> LMGentxtResult: ...
