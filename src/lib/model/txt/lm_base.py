import abc

from src import log
from src.core.util import multiline
from src.lib.model import ModelBase


class LmBase(ModelBase):
    """Base class for language models."""

    namespace_part = "txt"

    def gen(self, prompt: str) -> str:
        log.info(
            multiline(
                f"""
                Starting LM generate: {self._model_name}
                Prompt:
                {prompt}
                """,
                keep_newline=True,
            )
        )
        result = self._sub_gen(prompt)
        log.success(
            multiline(
                f"""
                Finished LM generate: {self._model_name}
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
    def _sub_gen(self, prompt: str) -> str:
        pass
