# tools

Workspace-level tooling (generic code, so it lives in lab; the scratch workspace
launches it as a bazel target — no symlinks).

- `ws` — the ~/llz workspace harness: `ws test` runs every member's full suite
  in place (the green-workspace gate); `ws status` shows each member's VCS state
  where it has one. The member list is declared at the top of the script.
  Path-relative and VCS-agnostic.
