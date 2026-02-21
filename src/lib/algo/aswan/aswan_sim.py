import math
import random

from pydantic import Field

from src import arg
from src.lib.algo.aswan.aswan import Aswan, AswanInput, AswanOutput


class AswanSimInput(AswanInput):
    """Input for the Aswan Monte Carlo simulation."""

    Ns: int = Field(
        default=arg.Ns,
        gt=0,
        description="Number of Monte Carlo simulations.",
    )


class AswanSim(Aswan):
    """Uses Monte Carlo simulation to determine required rounds."""

    input_type = AswanSimInput

    async def _run(self, inp: AswanSimInput) -> AswanOutput:  # type:ignore
        n = inp.N
        m = min(inp.M, n)
        target_tagged = int(math.ceil(inp.y * n))

        rounds = 1
        while True:
            successes = 0
            for _ in range(inp.Ns):
                if self._simulate(n, m, rounds) >= target_tagged:
                    successes += 1

            if successes / inp.Ns >= inp.p:
                return AswanOutput(x=rounds)

            rounds += 1
            if rounds > 1000:  # Safety break for simulation
                break

        return AswanOutput(x=rounds)

    def _simulate(self, n: int, m: int, rounds: int) -> int:
        """Simulate tagging process for given rounds."""
        tagged = set()
        population = list(range(n))
        for _ in range(rounds):
            samples = random.choices(population, k=m)
            tagged.update(samples)
        return len(tagged)
