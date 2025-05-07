import abc

from src import env
from src.core.util import multiline
from src.lib.model import ModelBasis
from src.lib.model.txt.lm_gentxt_params import LmGentxtParams
from src.lib.model.txt.lm_gentxt_result import LmGentxtResult


class LmBasis(abc.ABC, ModelBasis):
    """Base class for language models."""

    namespace_part = "txt"

    def gentxt(self, params: LmGentxtParams) -> LmGentxtResult:
        self.log.info(
            multiline(
                """
                Starting LM generate with params:
                {params}
                """,
                oneline=False,
            ),
            params=params.format_str(indent=env.indent),
        )
        result = self._sub_gentxt(params)
        self.log.info(
            multiline(
                """
                Finished LM generate with result:
                {result}
                """,
                oneline=False,
            ),
            result=result.format_str(indent=env.indent),
        )
        return result

    @abc.abstractmethod
    def _sub_gentxt(self, params: LmGentxtParams) -> LmGentxtResult:
        pass
