from openai import OpenAI

from src.lib.model.txt import LmBase


class OpenaiLm(LmBase):
    """OpenAI LM.


    Models: https://platform.openai.com/docs/models
    Pricing: https://platform.openai.com/docs/pricing
    """

    def _sub_init(self, model_name: str):
        self._client = OpenAI()
        self._openai_model_name = model_name.split("/")[1]

    def _sub_gen(self, prompt: str) -> str:
        response = self._client.responses.create(
            model=self._openai_model_name,
            input=prompt,
        )
        return response.output_text
