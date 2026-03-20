# RNG

A seeded random number generator with draw-without-replacement. Wraps Python's
`random.Random` with logging, counters, and a built-in item pool.

## Pool

The pool is the central primitive — a shuffled collection of items that are
drawn one at a time without replacement. This models any "draw from a bag"
mechanic: cards from a deck, tiles from a bag, etc.

- `load(items)` replaces the pool and shuffles it.
- `draw(n)` pops items from the pool. Returns a single item when `n=1`, a list
  when `n>1`, or `None` when the pool is exhausted or not loaded.
- `reshuffle()` restores the original pool contents and reshuffles.

Drawing from an empty or unloaded pool is a no-op — it logs a warning and bumps
an error counter rather than raising. This matches the Graph convention of
graceful degradation.

## Reproducibility

When `seed` is set, all operations (pool shuffles, randint, choice, etc.) are
deterministic. Two `RNG` instances with the same seed and same sequence of
calls will produce identical results. `reseed()` resets the PRNG state.

## Subclasses

`Deck`, `Coin`, and `Dice` extend `RNG` with domain-specific semantics:

- **Deck** — Pre-loaded with 52 standard playing cards (optionally +jokers).
  `deal(n)` is a semantic alias for `draw(n)`. Cards are `Card` dataclasses
  with `Rank` and `Suit` enums. `load()` validates that all items are `Card`
  instances.
- **Coin** — Pre-loaded with `[HEADS, TAILS]`. `flip()` draws one side.
  `load()` enforces exactly 2 `CoinSide` items.
- **Dice** — Pre-loaded with `[1..n_sides]` (default 6). `roll()` draws one
  face. `load()` enforces positive integers.

Each subclass validates its `load()` input and rejects invalid items with a
warning — the existing pool remains unchanged on rejection.

## Extend

To add a new RNG variant (e.g. a spinner, a bingo cage):

1. Subclass `RNG`.
2. Set `logspace_part` to a unique string.
3. Pre-load the pool in `__init__` via `RNGInitParams(pool=...)`.
4. Add a domain method (like `spin()` or `call()`) that wraps `draw()`.
5. Override `load()` with validation if the pool contents are constrained.
