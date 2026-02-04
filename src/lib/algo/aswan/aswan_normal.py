import math

from src.lib.algo.aswan.aswan import Aswan, AswanInput, AswanOutput


class AswanNormal(Aswan):
    """Uses Normal Approximation to estimate required rounds."""

    async def _run(self, inp: AswanInput) -> AswanOutput:
        n, m, p, y = inp.N, inp.M, inp.p, inp.y

        if m >= n:
            return AswanOutput(x=1)

        z_p = self._get_z_score(p)
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

    def _get_z_score(self, p: float) -> float:
        """Approximate inverse CDF of standard normal."""
        if p < 0.5:
            return -self._get_z_score(1 - p)
        t = math.sqrt(-2.0 * math.log(1.0 - p))
        z = t - (
            (2.515517 + 0.802853 * t + 0.010328 * t * t)
            / (1.0 + 1.432788 * t + 0.189269 * t * t + 0.001308 * t * t * t)
        )
        return z
