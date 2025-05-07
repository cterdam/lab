from openai import OpenAI

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

    def __init__(
        self,
        params: OpenaiLmInitParams,
        *args,
        **kwargs,
    ):
        super().__init__(
            log_name=kwargs.pop("log_name", None)
            or as_filename(f"openai/{params.model_name}"),
            params=params,
            *args,
            **kwargs,
        )
        self._client = OpenAI()
        self._model_name = params.model_name
        self.log.debug("Finished init")

    def _sub_gentxt(self, params: OpenaiLmGentxtParams) -> OpenaiLmGentxtResult:
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
        return result
