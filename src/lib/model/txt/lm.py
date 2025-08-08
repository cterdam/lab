from abc import abstractmethod

from src import env, log
from src.lib.model import Model
from src.lib.model.txt.lm_coke import LmCoke
from src.lib.model.txt.lm_gentxt_result import LmGentxtResult


class Lm(Model):
    """Base class for language models."""

    logspace_part = "txt"
    coke: LmCoke = LmCoke()

    def gentxt(self, *args, **kwargs) -> LmGentxtResult:

        result = self._do_gentxt(*args, **kwargs)

        with env.coup() as p:

            self.incr(Lm.coke.GENTXT_INVOC, p=p)
            self.incr(Lm.coke.INPUT_TOKEN, result.input_tokens, p=p)
            self.incr(Lm.coke.OUTPUT_TOKEN, result.output_tokens, p=p)

            log.incr(Lm.coke.GENTXT_INVOC, p=p)
            log.incr(Lm.coke.INPUT_TOKEN, result.input_tokens, p=p)
            log.incr(Lm.coke.OUTPUT_TOKEN, result.output_tokens, p=p)

        return result

    @abstractmethod
    def _do_gentxt(self, *args, **kwargs) -> LmGentxtResult: ...

    async def agentxt(self, *args, **kwargs) -> LmGentxtResult:

        result = await self._do_agentxt(*args, **kwargs)

        async with env.acoup() as p:

            await self.aincr(Lm.coke.AGENTXT_INVOC, p=p)
            await self.aincr(Lm.coke.INPUT_TOKEN, result.input_tokens, p=p)
            await self.aincr(Lm.coke.OUTPUT_TOKEN, result.output_tokens, p=p)

            await log.aincr(Lm.coke.AGENTXT_INVOC, p=p)
            await log.aincr(Lm.coke.INPUT_TOKEN, result.input_tokens, p=p)
            await log.aincr(Lm.coke.OUTPUT_TOKEN, result.output_tokens, p=p)

        return result

    @abstractmethod
    async def _do_agentxt(self, *args, **kwargs) -> LmGentxtResult: ...
