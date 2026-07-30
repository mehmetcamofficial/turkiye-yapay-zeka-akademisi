#!/usr/bin/env python3
"""Validate the canonical repository knowledge graph."""

from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/project/knowledge-graph.yaml"
NODE_TYPES = {
    "repository", "project", "subsystem", "model", "dataset", "interface",
    "task", "hypothesis", "experiment", "failure", "ADR", "metric_snapshot",
    "release", "commit", "prompt", "lesson", "open_question", "timeline",
    "architecture_stage", "open_problem", "documentation_system",
}
RELATIONS = {
    "contains", "depends_on", "uses", "trains", "evaluates", "renders",
    "introduced_by", "changed_by", "tests", "validates", "addresses",
    "caused_by", "resolves", "rejected_by", "documented_by", "released_as",
    "improves", "regresses", "supersedes", "related_to",
}
CONFIDENCE = {"confirmed", "strong", "partial", "unknown"}


def load_graph(path: Path = SOURCE) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Graph root must be a mapping")
    return data


def validate(data: dict, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    nodes = data.get("nodes")
    edges = data.get("relationships")
    if not isinstance(nodes, list):
        return ["nodes must be a list"]
    if not isinstance(edges, list):
        return ["relationships must be a list"]
    ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"node {index} must be a mapping")
            continue
        missing = {"id", "type", "label", "evidence"} - node.keys()
        if missing:
            errors.append(f"node {index} missing {sorted(missing)}")
            continue
        node_id = str(node["id"])
        if node_id in ids:
            errors.append(f"duplicate node id: {node_id}")
        ids.add(node_id)
        if node["type"] not in NODE_TYPES:
            errors.append(f"invalid node type {node['type']} for {node_id}")
        evidence = root / str(node["evidence"])
        if not evidence.exists():
            errors.append(f"missing evidence for {node_id}: {node['evidence']}")
    edge_keys: set[tuple[str, str, str]] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edge {index} must be a mapping")
            continue
        missing = {"from", "to", "type", "confidence"} - edge.keys()
        if missing:
            errors.append(f"edge {index} missing {sorted(missing)}")
            continue
        source, target, relation = str(edge["from"]), str(edge["to"]), str(edge["type"])
        if source not in ids:
            errors.append(f"edge {index} unknown source: {source}")
        if target not in ids:
            errors.append(f"edge {index} unknown target: {target}")
        if relation not in RELATIONS:
            errors.append(f"edge {index} invalid relation: {relation}")
        if edge["confidence"] not in CONFIDENCE:
            errors.append(f"edge {index} invalid confidence: {edge['confidence']}")
        key = (source, target, relation)
        if key in edge_keys:
            errors.append(f"duplicate edge: {key}")
        edge_keys.add(key)
    return errors


def main() -> int:
    errors = validate(load_graph())
    if errors:
        print("Knowledge graph validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Knowledge graph valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())

