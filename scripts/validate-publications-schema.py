#!/usr/bin/env python3
"""Validate canonical publication data against its JSON Schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "publications.json"
SCHEMA_FILE = ROOT / "data" / "publications.schema.json"


def format_path(parts: object) -> str:
    values = list(parts)
    if not values:
        return "$"
    return "$" + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in values)


def main() -> int:
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.absolute_path))
    if errors:
        for error in errors:
            print(f"{format_path(error.absolute_path)}: {error.message}", file=sys.stderr)
        return 1
    print(f"JSON Schema validated {len(data.get('publications', []))} publication records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
