from functools import cached_property

import openai

from src import log
from src.core.util import as_filename
from src.lib.model.txt import LM
from src.lib.model.txt.api.openai.openai_lm_gentxt_params import OpenAILMGentxtParams
from src.lib.model.txt.api.openai.openai_lm_gentxt_result import OpenAILMGentxtResult
from src.lib.model.txt.api.openai.openai_lm_init_params import OpenAILMInitParams


class OpenAILM(LM):
    """OpenAI LM.

    Models: https://platform.openai.com/docs/models
    Pricing: https://platform.openai.com/docs/pricing
    """

    def __init__(
        self,
        params: OpenAILMInitParams,
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
    def _do_gentxt(self, params: OpenAILMGentxtParams) -> OpenAILMGentxtResult:

        response = self._client.responses.create(
            input=params.prompt,
            model=self._model_name,
            instructions=params.system_prompt,
            max_output_tokens=params.max_new_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
        )

        result = OpenAILMGentxtResult(
            output=response.output_text,
            input_tokens=response.usage.input_tokens,  # pyright:ignore
            output_tokens=response.usage.output_tokens,  # pyright:ignore
        )

        return result

    @log.io()
    async def _do_agentxt(self, params: OpenAILMGentxtParams) -> OpenAILMGentxtResult:

        response = await self._aclient.responses.create(
            input=params.prompt,
            model=self._model_name,
            instructions=params.system_prompt,
            max_output_tokens=params.max_new_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
        )

        result = OpenAILMGentxtResult(
            output=response.output_text,
            input_tokens=response.usage.input_tokens,  # pyright:ignore
            output_tokens=response.usage.output_tokens,  # pyright:ignore
        )

        return result
