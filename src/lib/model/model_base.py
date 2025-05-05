import abc

from src import log
from src.core import Logger
from src.core.util import as_filename


class ModelBase(abc.ABC, Logger):
    """Base class for models."""

    namespace_part = "model"

    def __init__(
        self,
        model_name: str,
        log_name: str | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            log_name=log_name or as_filename(model_name),
            **kwargs,
        )
        log.info(f"Starting model init: {model_name}")
        self._sub_init(model_name)
        self._model_name = model_name
        log.success(f"Finished model init: {model_name}")

    @abc.abstractmethod
    def _sub_init(self, model_name: str):
        pass
