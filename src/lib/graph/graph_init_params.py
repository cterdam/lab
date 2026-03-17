from pydantic import Field

from src.core import Dataclass
from src.core.util import multiline


class GraphInitParams(Dataclass):
    """Initialization params for a graph."""

    default_edge_cost: float = Field(
        default=1.0,
        ge=0.0,
        description="Default cost for edges when not explicitly specified.",
    )

    directed: bool = Field(
        default=False,
        description=multiline(
            """
            Whether edges are directed by default. If False, connect(a, b) also
            creates the reverse edge b -> a with the same cost.
            """
        ),
    )
