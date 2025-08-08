from abc import ABC, abstractmethod

from src.lib.model import Model
from src.lib.model.txt.lm_gentxt_result import LmGentxtResult


class Lm(ABC, Model):
    """Base class for language models."""

    logspace_part = "txt"

    @abstractmethod
    def gentxt(self, *args, **kwargs) -> LmGentxtResult: ...

    @abstractmethod
    async def agentxt(self, *args, **kwargs) -> LmGentxtResult: ...
