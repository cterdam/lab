import math
import random

from pydantic import Field

from src.lib.algo.aswan.aswan import Aswan, AswanInput, AswanOutput


class AswanSimInput(AswanInput):
    """Extended input for simulation."""

    num_simulations: int = Field(
        default=1000, gt=0, description="Number of Monte Carlo simulations to run."
    )


class AswanSim(Aswan):
    """Uses Monte Carlo simulation to determine required rounds."""

    async def _run(self, inp: AswanSimInput) -> AswanOutput:  # type: ignore
        n = inp.N
        m = min(inp.M, n)
        target_tagged = int(math.ceil(inp.y * n))

        # We start with the minimal possible rounds
        rounds = 1
        while True:
            successes = 0
            for _ in range(inp.num_simulations):
                if self._simulate(n, m, rounds) >= target_tagged:
                    successes += 1

            if successes / inp.num_simulations >= inp.p:
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
            # Sample M items with replacement
            samples = random.choices(population, k=m)
            tagged.update(samples)
        return len(tagged)
