from functools import cached_property

import openai

from src import env, log
from src.core.util import as_filename
from src.lib.model.txt import LmBasis
from src.lib.model.txt.api.openai.openai_lm_gentxt_params import OpenaiLmGentxtParams
from src.lib.model.txt.api.openai.openai_lm_gentxt_result import OpenaiLmGentxtResult
from src.lib.model.txt.api.openai.openai_lm_init_params import OpenaiLmInitParams


class OpenaiLm(LmBasis):
    """OpenAI LM.

    Models: https://platform.openai.com/docs/models
    Pricing: https://platform.openai.com/docs/pricing
    """

    @log.input()
    def __init__(
        self,
        params: OpenaiLmInitParams,
        logname: str | None = None,
    ):
        super().__init__(logname=logname or as_filename(f"openai/{params.model_name}"))
        self._model_name = params.model_name
        self._api_key = params.api_key

    @cached_property
    def _client(self) -> openai.OpenAI:
        return openai.OpenAI(api_key=self._api_key.get_secret_value())

    @cached_property
    def _aclient(self) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(api_key=self._api_key.get_secret_value())

    @log.io()
    def gentxt(self, params: OpenaiLmGentxtParams) -> OpenaiLmGentxtResult:

        response = self._client.responses.create(
            input=params.prompt,
            model=self._model_name,
            instructions=params.system_prompt,
            max_output_tokens=params.max_new_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
        )

        result = OpenaiLmGentxtResult(
            output=response.output_text,
            input_tokens=response.usage.input_tokens,  # pyright:ignore
            output_tokens=response.usage.output_tokens,  # pyright:ignore
        )

        self.incr(env.GENTXT_INVOC_CK)
        self.incr(env.INPUT_TOKEN_CK, result.input_tokens)
        self.incr(env.OUTPUT_TOKEN_CK, result.output_tokens)
        log.incr(env.GENTXT_INVOC_CK)
        log.incr(env.INPUT_TOKEN_CK, result.input_tokens)
        log.incr(env.OUTPUT_TOKEN_CK, result.output_tokens)

        return result

    @log.io()
    async def agentxt(self, params: OpenaiLmGentxtParams) -> OpenaiLmGentxtResult:

        response = await self._aclient.responses.create(
            input=params.prompt,
            model=self._model_name,
            instructions=params.system_prompt,
            max_output_tokens=params.max_new_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
        )

        result = OpenaiLmGentxtResult(
            output=response.output_text,
            input_tokens=response.usage.input_tokens,  # pyright:ignore
            output_tokens=response.usage.output_tokens,  # pyright:ignore
        )

        self.incr(env.AGENTXT_INVOC_CK)
        self.incr(env.INPUT_TOKEN_CK, result.input_tokens)
        self.incr(env.OUTPUT_TOKEN_CK, result.output_tokens)
        log.incr(env.AGENTXT_INVOC_CK)
        log.incr(env.INPUT_TOKEN_CK, result.input_tokens)
        log.incr(env.OUTPUT_TOKEN_CK, result.output_tokens)

        return result
