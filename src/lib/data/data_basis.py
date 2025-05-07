from src import env
from src.core import DataCore, Logger
from src.core.util import multiline


class DataBasis(Logger):
    """Base class for data services."""

    namespace_part = "data"

    def __init__(
        self,
        params: DataCore,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.log.debug(
            multiline(
                """
                Starting {class_name} init with params:
                {params}
                """,
                oneline=False,
            ),
            class_name=self.__class__.__name__,
            params=params.format_str(indent=env.indent),
        )
