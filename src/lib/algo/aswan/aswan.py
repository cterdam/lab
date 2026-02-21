from pydantic import Field

from src import arg
from src.lib.algo.algo import Algo, Input, Output


class AswanInput(Input):
    """Input for the Aswan sampling algorithm."""

    N: int = Field(
        default=arg.N,
        gt=0,
        description="Total population size.",
    )

    M: int = Field(
        default=arg.M,
        gt=0,
        description="Number of items sampled per round.",
    )

    p: float = Field(
        default=arg.p,
        gt=0,
        lt=1,
        description="Required confidence level.",
    )

    y: float = Field(
        default=arg.y,
        gt=0,
        lt=1,
        description="Target proportion of tagged population.",
    )


class AswanOutput(Output):
    """Output for the Aswan sampling algorithm."""

    x: int = Field(ge=0, description="Minimum number of rounds required.")


class Aswan(Algo[AswanInput, AswanOutput]):
    """Interface for Aswan sampling algorithms."""

    input_type = AswanInput
    logspace_part = "aswan"
