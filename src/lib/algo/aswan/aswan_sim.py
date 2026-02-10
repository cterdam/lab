import math
import random

from src.lib.algo.aswan.aswan import Aswan, AswanInput, AswanOutput


class AswanSim(Aswan):
    """Uses Monte Carlo simulation to determine required rounds."""

    n_sims: int = 1000

    def __init__(self, *args, n_sims: int = 1000, **kwargs):
        super().__init__(*args, **kwargs)
        self.n_sims = n_sims

    async def _run(self, inp: AswanInput) -> AswanOutput:
        n = inp.N
        m = min(inp.M, n)
        target_tagged = int(math.ceil(inp.y * n))

        # We start with the minimal possible rounds
        rounds = 1
        while True:
            successes = 0
            for _ in range(self.n_sims):
                if self._simulate(n, m, rounds) >= target_tagged:
                    successes += 1

            if successes / self.n_sims >= inp.p:
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
