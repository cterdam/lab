# core

The packages. Each package is a folder here with:

- `src/` — the implementation (`py_library` targets).
- `test/` — its unit tests (`py_test` targets), mirroring `src/` modules as
  `test_<module>.py`.
- `BUILD.bazel` — calls `fmt()` and wires the library + tests.
- `README.md` — what the package is for.

Import paths follow the tree: `from core.<pkg>.src import <module>`.
