from openai import OpenAI

from src.lib.model.txt import GentxtParams, GentxtResult, LmBasis


class OpenaiLm(LmBasis):
    """OpenAI LM.

    Models: https://platform.openai.com/docs/models
    Pricing: https://platform.openai.com/docs/pricing
    """

    def _sub_init(self, model_name: str):
        self._client = OpenAI()
        self._openai_model_name = model_name.split("/")[1]

    def _sub_gentxt(self, params: GentxtParams) -> GentxtResult:
        response = self._client.responses.create(
            input=params.prompt,
            model=self._openai_model_name,
            instructions=params.system_prompt,
            max_output_tokens=params.max_new_tokens,
            temperature=params.temperature,
            top_p=params.top_p,
        )
        result = GentxtResult(
            output=response.output_text,
            input_tokens=response.usage.input_tokens,  # pyright:ignore
            output_tokens=response.usage.output_tokens,  # pyright:ignore
        )
        return result
