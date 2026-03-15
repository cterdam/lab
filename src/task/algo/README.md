# algo

Runs an algorithmic computation using the algo framework. The algo is specified
by its Python import path via the `algo` argument. At runtime, the class is
imported, its `input_type()` is constructed from `src.arg` fields
(`M`, `N`, `Ns`, `p`, `y`), and `algo.run(inp)` is awaited.

See `src/lib/algo/README.md` for how to add new algos.
