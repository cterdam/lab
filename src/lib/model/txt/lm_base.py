import abc

from src.core.constants import INDENT
from src.core.util import multiline
from src.lib.model import ModelBase
from src.lib.model.txt.lm_gen_params import LmGenParams
from src.lib.model.txt.lm_gen_result import LmGenResult


class LmBase(ModelBase):
    """Base class for language models."""

    namespace_part = "txt"

    def gentxt(self, params: LmGenParams) -> LmGenResult:
        self.log.info(
            multiline(
                """
                Starting LM generate: {model_name}
                - Params:
                {params}
                """,
                oneline=False,
            ),
            model_name=self._model_name,
            params=params.format_str(indent=INDENT),
        )
        result = self._sub_gentxt(params)
        self.log.info(
            multiline(
                """
                Finished LM generate: {model_name}
                - Params:
                {params}
                - Result:
                {result}
                """,
                oneline=False,
            ),
            model_name=self._model_name,
            params=params.format_str(indent=INDENT),
            result=result.format_str(indent=INDENT),
        )
        return result

    @abc.abstractmethod
    def _sub_gentxt(self, params: LmGenParams) -> LmGenResult:
        pass
