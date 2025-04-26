import abc

from src.core import log
from src.core.util import multiline


class LLMBase(abc.ABC):
    """Base class for model providers."""

    def __init__(self, model_name: str):
        log.info(f"Starting LLM init: {model_name}")
        self._sub_init(model_name)
        self._model_name = model_name
        log.success(f"Finished LLM init: {model_name}")

    @abc.abstractmethod
    def _sub_init(self, model_name: str):
        pass

    def generate(self, prompt: str) -> str:
        log.info(
            multiline(
                f"""
                Starting LLM generate: {self._model_name}
                Prompt:
                {prompt}
                """,
                keep_newline=True,
            )
        )
        result = self._sub_generate(prompt)
        log.success(
            multiline(
                f"""
                Finished LLM generate: {self._model_name}
                Prompt:
                {prompt}
                Result:
                {result}
                """,
                keep_newline=True,
            )
        )
        return result

    @abc.abstractmethod
    def _sub_generate(self, prompt: str) -> str:
        pass
