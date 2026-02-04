from abc import ABC

from pydantic import Field

from src.lib.algo.algo import Algo, Input, Output


class AswanInput(Input):
    """Input for the Aswan sampling algorithm."""

    N: int = Field(gt=0, description="Total population size.")
    M: int = Field(gt=0, description="Number of items sampled per round.")
    p: float = Field(gt=0, lt=1, description="Required confidence level.")
    y: float = Field(gt=0, lt=1, description="Target proportion of tagged population.")


class AswanOutput(Output):
    """Output for the Aswan sampling algorithm."""

    x: int = Field(ge=0, description="Minimum number of rounds required.")


class Aswan(Algo[AswanInput, AswanOutput], ABC):
    """Interface for Aswan sampling algorithms."""

    logspace_part = "aswan"
