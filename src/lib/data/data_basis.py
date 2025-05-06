import abc

from src import env
from src.core import DataCore, Logger
from src.core.util import multiline


class DataBasis(abc.ABC, Logger):
    """Base class for data services."""

    namespace_part = "data"

    def __init__(
        self,
        log_name: str,
        init_params: DataCore = DataCore(),
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            log_name=log_name,
            **kwargs,
        )
        self.log.debug(
            multiline(
                """
                Starting data service init with params:
                {init_params}
                """,
                oneline=False,
            ),
            init_params=init_params.format_str(indent=env.indent),
        )
