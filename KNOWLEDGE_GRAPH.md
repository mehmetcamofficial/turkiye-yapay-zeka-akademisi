# Repository Knowledge Graph

The canonical machine-readable graph is `docs/project/knowledge-graph.yaml`.
This view summarizes its principal evidence-backed paths.

Generated views: [summary](docs/architecture/diagrams/generated/knowledge-graph-summary.md),
[Mermaid](docs/architecture/diagrams/generated/knowledge-graph.mmd), and
[Graphviz DOT](docs/architecture/diagrams/generated/knowledge-graph.dot).

```text
repository
├── contains → machine-learning portfolio
│   ├── renders → churn, housing, sentiment, Trendyol, data-science pages
│   ├── contains → repository search
│   └── contains → AI Project Copilot
├── contains → Trendyol search relevance
│   ├── uses → TF-IDF / BM25 / multilingual E5 / Hybrid RRF
│   ├── evaluates → Recall@K / NDCG@10 / MRR
│   └── uses → cross-encoder reranker
├── contains → data-science coursework and profiling
└── documented_by → engineering knowledge system

TASK-0008 → introduced_by → Copilot V1
TASK-0010 → changed_by → exact filename-stem experiment
TASK-0011 → changed_by → phrase-alias experiment
TASK-0012 → addresses → file-location intent failure
TASK-0013 → changed_by → Engineering Knowledge System V1.1
metric snapshot → validates → Copilot current state
OPEN-GQ03/GQ11/GQ19/GQ25 → related_to → Copilot
```

Edges are not claims of causal rationale unless their confidence is `confirmed`.
Follow each node's `evidence` link before using it in code or publication.
