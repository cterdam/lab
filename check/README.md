# check

The check machinery, ported from `doc`: the `check()`/`rule()`/`fmt()` macros
(`def.bzl`), the aggregate per-file driver (`src/main.py`), and the formatting
rules (`src/rule/fmt_*.py` — black+isort, mdformat, canonical JSON, buildifier).
Rules are generic: a rule never assumes what a package's files mean — config
arrives as explicit parameters.

Every package calls `fmt()`; packages with their own invariants add `check()`
targets with package-specific rules in their `rule/` folder.
