# Aswan Sampling Probability Algorithm

## Problem Description

We have a population of size **N**. In each round, we
sample **M** items (with replacement), tag them, and return them to the
population.

We want to find the minimum number of rounds **x** required such that we are at
least **p** (float between 0 and 1) certain that at least **y** (float between 0
and 1) proportion of the population has been tagged.

## Interface

- **Input (AswanInput)**:
  - `N`: Total population size.
  - `M`: Items sampled per round.
  - `p`: Required confidence level (float 0-1).
  - `y`: Target proportion of tagged population (float 0-1).

- **Output (AswanOutput)**:
  - `x`: The calculated minimum number of rounds.

## Implementations

- **AswanNormal**: Uses a normal approximation to the binomial distribution for
fast, analytical calculation.
- **AswanSim**: Runs Monte Carlo simulations to empirically determine the
required number of rounds.
