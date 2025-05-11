import abc

from src.lib.model import ModelBasis
from src.lib.model.txt.lm_gentxt_result import LmGentxtResult


class LmBasis(abc.ABC, ModelBasis):
    """Base class for language models."""

    namespace_part = "txt"

    @abc.abstractmethod
    def gentxt(self, *args, **kwargs) -> LmGentxtResult: ...

    @abc.abstractmethod
    async def agentxt(self, *args, **kwargs) -> LmGentxtResult: ...
