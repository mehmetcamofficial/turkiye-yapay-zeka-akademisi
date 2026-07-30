#!/usr/bin/env python3
"""Validate the machine-readable metric history."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "metrics/history.json"
REQUIRED = {"date", "version", "phase", "task", "commit", "metric", "value", "denominator", "source", "confidence"}
CONFIDENCE = {"confirmed", "strong", "partial", "unknown"}


def load_history(path: Path = SOURCE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("History root must be an object")
    return data


def validate(data: dict, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    records = data.get("records")
    if not isinstance(records, list):
        return ["records must be a list"]
    seen: set[tuple[object, ...]] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} must be an object")
            continue
        missing = REQUIRED - record.keys()
        if missing:
            errors.append(f"record {index} missing {sorted(missing)}")
            continue
        try:
            date.fromisoformat(record["date"])
        except (TypeError, ValueError):
            errors.append(f"record {index} invalid date: {record['date']}")
        if record["confidence"] not in CONFIDENCE:
            errors.append(f"record {index} invalid confidence")
        if record["value"] is not None and not isinstance(record["value"], (int, float)):
            errors.append(f"record {index} value must be numeric or null")
        denominator = record["denominator"]
        if denominator is not None and (not isinstance(denominator, (int, float)) or denominator <= 0):
            errors.append(f"record {index} denominator must be positive or null")
        if not (root / record["source"]).exists():
            errors.append(f"record {index} missing source: {record['source']}")
        key = (record["date"], record["version"], record["phase"], record["task"], record["commit"], record["metric"])
        if key in seen:
            errors.append(f"duplicate record: {key}")
        seen.add(key)
    return errors


def main() -> int:
    errors = validate(load_history())
    if errors:
        print("Metrics validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Metrics history valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())

