import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from src import arg, log


def build_registry(root: Path) -> Registry:
    """Walk root for all JSON files with a $id; register them for $ref resolution."""
    resources: list[tuple[str, Resource]] = []
    for json_path in root.rglob("*.json"):
        with open(json_path) as f:
            try:
                schema = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
        if not isinstance(schema, dict):
            continue
        schema_id = schema.get("$id")
        if schema_id:
            resource = Resource.from_contents(schema, default_specification=DRAFT202012)
            resources.append((schema_id, resource))
    return Registry().with_resources(resources)


def find_pairs(root: Path) -> list[Path]:
    """Find directories containing both head.yaml and schema.json."""
    pairs = []
    for head in root.rglob("head.yaml"):
        if (head.parent / "schema.json").exists():
            pairs.append(head.parent)
    return sorted(pairs)


def validate_pair(dir_path: Path, registry: Registry) -> list[ValidationError]:
    """Validate head.yaml against schema.json in dir_path."""
    with open(dir_path / "head.yaml") as f:
        data = yaml.safe_load(f)
    with open(dir_path / "schema.json") as f:
        schema = json.load(f)
    validator = Draft202012Validator(schema, registry=registry)
    return list(validator.iter_errors(data))


def main():

    root = arg.input_dir
    log.info(f"Validating head.yaml files under {root}")

    registry = build_registry(root)
    pairs = find_pairs(root)

    log.incr("schemas_registered", len(registry))
    log.incr("pairs_found", len(pairs))

    if not pairs:
        log.warning("No head.yaml + schema.json pairs found")
        return

    for dir_path in pairs:
        errors = validate_pair(dir_path, registry)
        if errors:
            log.incr("pairs_failed")
            log.incr("errors", len(errors))
            detail = "\n".join(f"  {err.message}" for err in errors)
            log.error(f"FAIL {dir_path}\n{detail}")
        else:
            log.incr("pairs_passed")
            log.success(f"PASS {dir_path}")
