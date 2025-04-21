import abc

from src.core.log import logger
from src.core.util.general import multiline


class LLMBase(abc.ABC):
    """Base class for model providers."""

    def __init__(self, model_name: str):
        logger.info(
            multiline(
                f"""
                Starting LLM init.
                Model name: {model_name}
                """,
                keep_newline=True,
            )
        )
        self._sub_init(model_name)
        self._model_name = model_name
        logger.success(
            multiline(
                f"""
                Finished LLM init.
                Model name: {model_name}
                """,
                keep_newline=True,
            )
        )

    @abc.abstractmethod
    def _sub_init(self, model_name: str):
        pass

    def generate(self, prompt: str) -> str:
        logger.info(
            multiline(
                f"""
                Starting LLM generate.
                Model name: {self._model_name}
                Prompt:
                {prompt}
                """,
                keep_newline=True,
            )
        )
        result = self._sub_generate(prompt)
        logger.success(
            multiline(
                f"""
                Finished LLM generate.
                Model name: {self._model_name}
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
