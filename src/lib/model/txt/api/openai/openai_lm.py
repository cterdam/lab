import functools

import openai

from src import log
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
        log_name: str | None = None,
    ):
        super().__init__(
            log_name=log_name or as_filename(f"openai/{params.model_name}")
        )
        self._model_name = params.model_name

    @functools.cached_property
    def _client(self) -> openai.OpenAI:
        return openai.OpenAI()

    @functools.cached_property
    def _aclient(self) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI()

    @log.io()
    def gentxt(self, params: OpenaiLmGentxtParams) -> OpenaiLmGentxtResult:
        messages = []
        if params.system_prompt:
            messages.append({"role": "system", "content": params.system_prompt})
        messages.append({"role": "user", "content": params.prompt})

        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            max_tokens=params.max_new_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
        )
        result = OpenaiLmGentxtResult(
            output=response.choices[0].message.content or "",
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )
        return result

    @log.io()
    async def agentxt(self, params: OpenaiLmGentxtParams) -> OpenaiLmGentxtResult:
        messages = []
        if params.system_prompt:
            messages.append({"role": "system", "content": params.system_prompt})
        messages.append({"role": "user", "content": params.prompt})

        response = await self._aclient.chat.completions.create(
            model=self._model_name,
            messages=messages,
            max_tokens=params.max_new_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
        )
        result = OpenaiLmGentxtResult(
            output=response.choices[0].message.content or "",
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )
        return result
