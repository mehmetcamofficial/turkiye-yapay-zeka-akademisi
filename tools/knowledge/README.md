# Knowledge Graph Tooling

Run from the repository root:

```bash
python tools/knowledge/validate_knowledge_graph.py
python tools/knowledge/generate_knowledge_graph.py
```

The tools read `docs/project/knowledge-graph.yaml`, use local PyYAML, require no
network or graph database, and write deterministic Mermaid, DOT, and Markdown
under `docs/architecture/diagrams/generated/`. If Graphviz is installed, DOT
may later be rendered manually; rendering is not required.

