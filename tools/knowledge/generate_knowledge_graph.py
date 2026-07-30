#!/usr/bin/env python3
"""Generate deterministic documentation views from the canonical graph."""

from __future__ import annotations

from pathlib import Path
import re

from validate_knowledge_graph import ROOT, SOURCE, load_graph, validate

OUTPUT = ROOT / "docs/architecture/diagrams/generated"
HEADER = "Generated from docs/project/knowledge-graph.yaml; do not edit directly."


def mermaid_id(value: str) -> str:
    return "N_" + re.sub(r"[^A-Za-z0-9_]", "_", value)


def quote(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def main() -> int:
    graph = load_graph()
    errors = validate(graph)
    if errors:
        raise SystemExit("\n".join(errors))
    nodes = sorted(graph["nodes"], key=lambda item: item["id"])
    edges = sorted(graph["relationships"], key=lambda item: (item["from"], item["to"], item["type"]))
    OUTPUT.mkdir(parents=True, exist_ok=True)

    mmd = [f"%% {HEADER}", "flowchart LR"]
    for node in nodes:
        mmd.append(f'  {mermaid_id(node["id"])}["{quote(node["label"])}"]')
    for edge in edges:
        label = f'{edge["type"]} ({edge["confidence"]})'
        mmd.append(f'  {mermaid_id(edge["from"])} -->|"{quote(label)}"| {mermaid_id(edge["to"])}')
    (OUTPUT / "knowledge-graph.mmd").write_text("\n".join(mmd) + "\n", encoding="utf-8")

    dot = [f"// {HEADER}", "digraph repository_knowledge {", "  rankdir=LR;"]
    for node in nodes:
        dot.append(f'  "{quote(node["id"])}" [label="{quote(node["label"])}\\n({quote(node["type"])})"];')
    for edge in edges:
        dot.append(f'  "{quote(edge["from"])}" -> "{quote(edge["to"])}" [label="{quote(edge["type"])} / {quote(edge["confidence"])}"];')
    dot.append("}")
    (OUTPUT / "knowledge-graph.dot").write_text("\n".join(dot) + "\n", encoding="utf-8")

    counts: dict[str, int] = {}
    for node in nodes:
        counts[node["type"]] = counts.get(node["type"], 0) + 1
    summary = [f"<!-- {HEADER} -->", "# Knowledge Graph Summary", "", f"- Nodes: {len(nodes)}", f"- Relationships: {len(edges)}", "", "## Node types", ""]
    summary.extend(f"- `{kind}`: {count}" for kind, count in sorted(counts.items()))
    summary.extend(["", "## Canonical source", "", "`docs/project/knowledge-graph.yaml`", ""])
    (OUTPUT / "knowledge-graph-summary.md").write_text("\n".join(summary), encoding="utf-8")
    print(f"Generated {len(nodes)} nodes and {len(edges)} relationships")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

