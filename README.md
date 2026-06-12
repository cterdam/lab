# lab

Functional code (the sibling of `doc`, which holds docs/data). Same
infrastructure: Bazel with bzlmod, pinned Python 3.12, pip deps via `REQ.txt` (+
fully-pinned `REQ.txt.lock`), buildifier, and the shared check machinery.

## Layout

- `core/` — the packages; each is `core/<pkg>/` with `src/` (libraries) and
  `test/` (unit tests). See `core/README.md`.
- `check/` — the `check()`/`rule()`/`fmt()` macros, the aggregate driver, and
  the formatting rules (black + isort, mdformat, canonical JSON, buildifier).
- `REQ.txt` — top-level pip deps; regenerate the lock with
  `bazel run //:req.update` (sync is itself tested by `//:req_test`).

## Commands

- `bazel test //...` — everything: unit tests plus the per-language formatting
  suites every package emits via `fmt()`.
- `bazel run //:req.update` — refresh `REQ.txt.lock` after editing `REQ.txt`.

## Conventions

- Every package calls `fmt()`; code is black/isort-formatted, BUILD files
  buildifier-formatted, markdown mdformat-formatted (wrap 80).
- Tests live next to what they test (`core/<pkg>/test/test_<module>.py`) and
  import first-party code by tree path (`from core.<pkg>.src import ...`).
- Visibility is public by default (`REPO.bazel`) — this is one repo's internal
  tooling, not an API surface.

## Workspace

This repo is a member of the `~/llz` workspace, beside `doc` (all docs, plus
only doc-specific util code) and `scratch` (launchpad + scratchpad, nothing
concrete). doc consumes lab by local path; there is no version pinning between
members — the workspace lives at head, and correctness is defined at workspace
level. After changing any member, run `~/llz/scratch/ws test` and keep it green.
