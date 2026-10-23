"""JSON Schema validation against the files in contracts/schemas (the single source of truth)."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ENVELOPE = {"$ref": "https://fox3.local/schemas/common.json#/$defs/envelope"}


class Validators:
    def __init__(self, schemas_dir: Path):
        self._schemas: dict[str, dict] = {}
        resources = []
        for f in sorted(schemas_dir.glob("*.json")):
            schema = json.loads(f.read_text("utf-8"))
            self._schemas[f.stem] = schema
            resources.append((schema["$id"], Resource.from_contents(schema, DRAFT202012)))
        self._registry = Registry().with_resources(resources)

    def errors(self, schema: dict | str, instance: object, limit: int = 5) -> list[str]:
        sch = self._schemas[schema] if isinstance(schema, str) else schema
        validator = Draft202012Validator(sch, registry=self._registry)
        out = []
        for e in validator.iter_errors(instance):
            out.append(f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}")
            if len(out) >= limit:
                break
        return out
