from abc import ABC, abstractmethod

from src.lib.model import ModelBasis
from src.lib.model.txt.lm_gentxt_result import LmGentxtResult


class LmBasis(ABC, ModelBasis):
    """Base class for language models."""

    logspace_part = "txt"

    @abstractmethod
    def gentxt(self, *args, **kwargs) -> LmGentxtResult: ...

    @abstractmethod
    async def agentxt(self, *args, **kwargs) -> LmGentxtResult: ...
