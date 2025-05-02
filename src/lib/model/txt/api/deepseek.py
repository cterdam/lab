import os

from openai import OpenAI

from src.lib.model.txt import LmBase


class DeepseekLm(LmBase):
    """DeepSeek LM.

    Models & Pricing: https://api-docs.deepseek.com/quick_start/pricing
    """

    def _sub_init(self, model_name: str):
        self._client = OpenAI(
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com",
        )
        self._deepseek_model_name = model_name.split("/")[1]

    def _sub_generate(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._deepseek_model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        return response.choices[0].message.content  # pyright: ignore
