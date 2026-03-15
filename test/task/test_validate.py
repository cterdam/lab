import json

import yaml

from src.task.validate_all_yaml.main import build_registry, find_pairs, validate_pair


def test_valid_data_passes(tmp_path):
    d = tmp_path / "item"
    d.mkdir()
    (d / "schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
            }
        )
    )
    (d / "head.yaml").write_text(yaml.dump({"name": "Alice"}))

    registry = build_registry(tmp_path)
    errors = validate_pair(d, registry)
    assert errors == []


def test_invalid_data_fails(tmp_path):
    d = tmp_path / "item"
    d.mkdir()
    (d / "schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"type": "string"}},
            }
        )
    )
    (d / "head.yaml").write_text(yaml.dump({"age": 30}))

    registry = build_registry(tmp_path)
    errors = validate_pair(d, registry)
    assert len(errors) == 1
    assert "name" in errors[0].message


def test_ref_resolution(tmp_path):
    # Shared schema with $id
    shared = tmp_path / "shared"
    shared.mkdir()
    (shared / "schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "shared",
                "$defs": {"name": {"type": "string", "minLength": 1}},
            }
        )
    )

    # Schema that references shared
    d = tmp_path / "item"
    d.mkdir()
    (d / "schema.json").write_text(
        json.dumps(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "required": ["name"],
                "properties": {"name": {"$ref": "shared#/$defs/name"}},
            }
        )
    )
    (d / "head.yaml").write_text(yaml.dump({"name": "Alice"}))

    registry = build_registry(tmp_path)
    errors = validate_pair(d, registry)
    assert errors == []

    # Empty name should fail due to minLength
    (d / "head.yaml").write_text(yaml.dump({"name": ""}))
    errors = validate_pair(d, registry)
    assert len(errors) == 1


def test_dirs_without_pairs_skipped(tmp_path):
    # Only head.yaml, no schema.json
    d1 = tmp_path / "a"
    d1.mkdir()
    (d1 / "head.yaml").write_text(yaml.dump({"name": "Alice"}))

    # Only schema.json, no head.yaml
    d2 = tmp_path / "b"
    d2.mkdir()
    (d2 / "schema.json").write_text(json.dumps({"type": "object"}))

    pairs = find_pairs(tmp_path)
    assert pairs == []
