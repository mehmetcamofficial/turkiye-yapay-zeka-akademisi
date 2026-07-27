from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from evaluation.search.schema import GoldenQuery


def load_golden_queries(path: str | Path) -> list[GoldenQuery]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Golden queries file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    queries = []
    errors = []
    for item in data.get("queries", []):
        q = GoldenQuery(
            query=item.get("query", ""),
            expected_resource_ids=item.get("expected_resource_ids", []),
            relevance_grades=item.get("relevance_grades", {}),
            query_intent=item.get("query_intent", ""),
            evaluation_category=item.get("evaluation_category", ""),
            must_include=item.get("must_include", []),
            forbidden_resources=item.get("forbidden_resources", []),
            protected_targets=item.get("protected_targets", []),
            categories=item.get("categories", []),
            languages=item.get("languages", []),
            notes=item.get("notes", ""),
        )
        errs = q.validate()
        if errs:
            errors.append(f"query '{q.query[:40]}': {'; '.join(errs)}")
        else:
            queries.append(q)

    if errors:
        raise ValueError(f"Golden query validation errors:\n" + "\n".join(errors))

    return queries


def load_quality_gates(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"gates": [], "baseline_commit": "", "description": ""}

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_baseline(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_baseline(data: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
