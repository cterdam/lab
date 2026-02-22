import math
from statistics import NormalDist

from src.lib.algo.aswan.aswan import Aswan, AswanInput, AswanOutput


class AswanNormal(Aswan):
    """Uses Normal Approximation to estimate required rounds."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._norm = NormalDist()

    async def _run(self, inp: AswanInput) -> AswanOutput:
        n, m, p, y = inp.N, inp.M, inp.p, inp.y

        if m >= n:
            return AswanOutput(x=1)

        z_p = self._norm.inv_cdf(p)
        k = n * (1 - y)
        q_per_round = 1 - (m / n)

        # Initial guess
        x = max(1, math.ceil(math.log(1 - y) / math.log(q_per_round)))

        while True:
            q = math.pow(q_per_round, x)
            mu = n * q
            sigma = math.sqrt(n * q * (1 - q))

            if mu + z_p * sigma <= k:
                return AswanOutput(x=x)

            x += 1
            if x > 1000000:  # Safety break
                break

        return AswanOutput(x=x)
