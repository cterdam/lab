# validate_all_yaml

Validates `head.yaml` data files against `schema.json` schemas (JSON Schema
draft 2020-12) within a directory tree.

## How it works

1. **Build a `$ref` registry** — walks `input_dir` for all `schema.json`
   files. Any schema with a top-level `$id` is registered so that `$ref`
   references (e.g. `"schema#/$defs/name"`) resolve across files.
2. **Find validation pairs** — finds directories containing both `head.yaml`
   and `schema.json`.
3. **Validate each pair** — loads the YAML data and JSON schema, creates a
   `Draft202012Validator` with the registry, and collects all validation errors.
4. **Report** — logs each pair as PASS or FAIL. Exits non-zero if any fail.

## Counters

`schemas_registered`, `pairs_found`, `pairs_passed`, `pairs_failed`, `errors`.

## Volume mount

Because the task runs inside Docker but validates files on the host,
`input_dir` is bind-mounted read-only into the container at the same path.
This is handled automatically by the `Makefile` and `compose.yml`. Set
`input_dir` to the absolute host path (e.g.
`input_dir=/Users/joshlee/cterdam/doc`).
